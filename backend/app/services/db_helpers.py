"""
Database helper functions for creating and querying cases, evidence, and classifications.
Bridges the classifier output (Pydantic ClassificationResult) with the DB models.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.database import (
    Case as DBCase,
    EvidenceItem as DBEvidence,
    Classification as DBClassification,
    Category as DBCategory,
    Law as DBLaw,
    gen_uuid,
)
from app.models.evidence import ClassificationResult, Category, GermanLaw
from app.services.evidence import hash_content, capture_timestamp


# ── Category/Law name → DB ID mapping ──

# Maps classifier Category enum values to DB category IDs
_CATEGORY_MAP = {
    "harassment": "harassment",
    "threat": "threat",
    "death_threat": "threat",  # maps to threat category in DB
    "defamation": "defamation",
    "misogyny": "misogyny",
    "body_shaming": "body_shaming",
    "coordinated_attack": "harassment",
    "false_facts": "defamation",
    "sexual_harassment": "sexual_harassment",
    "scam": "scam",
    "phishing": "phishing",
    "investment_fraud": "scam",
    "romance_scam": "scam",
    "impersonation": "identity_theft",
    "volksverhetzung": "volksverhetzung",
    "verleumdung": "slander",
    "stalking": "cyberstalking",
    "intimate_images": "intimate_images",
}

# Maps classifier GermanLaw paragraph to DB law IDs
_LAW_MAP = {
    "§ 130 StGB": "stgb-130",
    "§ 185 StGB": "stgb-185",
    "§ 186 StGB": "stgb-186",
    "§ 187 StGB": "stgb-187",
    "§ 201a StGB": "stgb-201a",
    "§ 238 StGB": "stgb-238",
    "§ 241 StGB": "stgb-241",
    "§ 126a StGB": "stgb-126a",
    "§ 263 StGB": "stgb-263",
    "§ 263a StGB": "stgb-263",  # maps to same fraud entry
    "§ 269 StGB": "stgb-269",
    "NetzDG § 3": "netzdg-3",
}


def create_case(db: Session, title: str | None = None, user_id: str | None = None) -> DBCase:
    """Create a new case in the database."""
    case = DBCase(
        id=gen_uuid(),
        user_id=user_id,
        title=title or "New Case",
        status="open",
        overall_severity="none",
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def add_evidence_with_classification(
    db: Session,
    case_id: str,
    text: str,
    classification_result: ClassificationResult,
    content_type: str = "text",
    source_url: str | None = None,
    author_username: str = "unknown",
    platform: str | None = None,
    archived_url: str | None = None,
    extracted_text: str | None = None,
    previous_hash: str | None = None,
    classifier_tier: int = 3,
    screenshot_base64: str | None = None,
) -> DBEvidence:
    """
    Create an EvidenceItem + linked Classification in the database.
    Maps classifier output categories/laws to DB reference data.

    If screenshot_base64 is provided, it's stored in metadata_json and will
    be embedded in legal PDFs.
    """
    import json as _json

    content_hash = hash_content(text)
    now = capture_timestamp()

    # Build metadata blob. Screenshots live here (not a dedicated column) to
    # avoid a DB migration for the MVP. Future: move to object storage.
    metadata: dict = {"author_username": author_username}
    if screenshot_base64:
        metadata["screenshot_base64"] = screenshot_base64
        metadata["screenshot_size_bytes"] = len(screenshot_base64) * 3 // 4
    metadata_json = _json.dumps(metadata)

    # Create evidence item
    evidence = DBEvidence(
        id=gen_uuid(),
        case_id=case_id,
        content_type=content_type,
        raw_content=text,
        extracted_text=extracted_text,
        content_hash=content_hash,
        hash_chain_previous=previous_hash,
        platform=platform,
        source_url=source_url,
        archived_url=archived_url,
        timestamp_utc=now,
        metadata_json=metadata_json,
    )
    db.add(evidence)
    db.flush()  # get evidence.id before creating classification

    # Create classification
    classification = DBClassification(
        id=gen_uuid(),
        evidence_item_id=evidence.id,
        severity=classification_result.severity.value,
        confidence=classification_result.confidence,
        classifier_tier=classifier_tier,
        summary=classification_result.summary,
        summary_de=classification_result.summary_de,
        potential_consequences=classification_result.potential_consequences,
        potential_consequences_de=classification_result.potential_consequences_de,
        recommended_actions=_build_recommended_actions(classification_result, "en"),
        recommended_actions_de=_build_recommended_actions(classification_result, "de"),
    )
    db.add(classification)
    db.flush()

    # Link categories (many-to-many)
    seen_cat_ids = set()
    for cat in classification_result.categories:
        cat_id = _CATEGORY_MAP.get(cat.value)
        if cat_id and cat_id not in seen_cat_ids:
            db_cat = db.query(DBCategory).filter_by(id=cat_id).first()
            if db_cat:
                classification.categories.append(db_cat)
                seen_cat_ids.add(cat_id)

    # Link laws (many-to-many)
    seen_law_ids = set()
    for law in classification_result.applicable_laws:
        law_id = _LAW_MAP.get(law.paragraph)
        if law_id and law_id not in seen_law_ids:
            db_law = db.query(DBLaw).filter_by(id=law_id).first()
            if db_law:
                classification.laws.append(db_law)
                seen_law_ids.add(law_id)

    db.commit()
    db.refresh(evidence)

    # Update case overall severity
    _update_case_severity(db, case_id)

    return evidence


def _update_case_severity(db: Session, case_id: str):
    """Recompute case overall_severity from its evidence classifications."""
    case = db.query(DBCase).filter_by(id=case_id).first()
    if not case:
        return

    severity_order = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    max_severity = "none"

    for ev in case.evidence_items:
        if ev.classification and ev.classification.severity:
            sev = ev.classification.severity
            if severity_order.get(sev, 0) > severity_order.get(max_severity, 0):
                max_severity = sev

    case.overall_severity = max_severity
    case.updated_at = datetime.now(timezone.utc)
    db.commit()


def _build_recommended_actions(result: ClassificationResult, lang: str) -> str:
    """Build recommended actions based on classification result."""
    actions = []
    is_critical = result.severity.value == "critical"
    is_high = result.severity.value == "high"

    if lang == "de":
        if is_critical:
            actions.append("Sofort Strafanzeige erstatten (online: www.onlinewache.polizei.de)")
            actions.append("NetzDG-Beschwerde bei der Plattform einreichen (24h Frist)")
            actions.append("Beweise sichern (Screenshots, Hash-Prüfung)")
        elif is_high:
            actions.append("Strafanzeige erwägen")
            actions.append("NetzDG-Beschwerde einreichen (7 Tage Frist)")
            actions.append("Alle Beweise dokumentieren")
        else:
            actions.append("Inhalt bei der Plattform melden")
            actions.append("Beweise sichern für mögliche spätere Anzeige")

        if any(c.value in ("scam", "investment_fraud", "phishing") for c in result.categories):
            actions.append("BaFin informieren (Bundesanstalt für Finanzdienstleistungsaufsicht)")
            actions.append("Bank kontaktieren falls Geld überwiesen wurde")

        actions.append("Beratung bei HateAid e.V.: https://hateaid.org")
    else:
        if is_critical:
            actions.append("File a police report immediately (Strafanzeige)")
            actions.append("Submit NetzDG complaint to the platform (24h deadline)")
            actions.append("Preserve all evidence (screenshots, hash verification)")
        elif is_high:
            actions.append("Consider filing a police report")
            actions.append("Submit NetzDG complaint (7-day deadline)")
            actions.append("Document all evidence")
        else:
            actions.append("Report the content to the platform")
            actions.append("Preserve evidence for potential future report")

        if any(c.value in ("scam", "investment_fraud", "phishing") for c in result.categories):
            actions.append("Report to BaFin (Federal Financial Supervisory Authority)")
            actions.append("Contact your bank if money was transferred")

        actions.append("Get support from HateAid e.V.: https://hateaid.org")

    return "\n".join(f"- {a}" for a in actions)


def get_last_hash(db: Session, case_id: str) -> str | None:
    """Get the content_hash of the last evidence item in a case (for hash chain)."""
    last = (
        db.query(DBEvidence)
        .filter_by(case_id=case_id)
        .order_by(DBEvidence.timestamp_utc.desc())
        .first()
    )
    return last.content_hash if last else None


def case_to_pydantic(db_case: DBCase):
    """Convert a DB Case with relationships to the legacy Pydantic Case model.
    Used by report generators that expect the old model format.
    """
    from app.models.evidence import (
        Case, EvidenceItem, ClassificationResult, PatternFlag,
        Severity, Category as PydanticCategory, GermanLaw,
    )

    evidence_items = []
    for ev in db_case.evidence_items:
        classification = None
        if ev.classification:
            cl = ev.classification
            # Map DB categories back to Pydantic Category enum
            categories = []
            for cat in cl.categories:
                # Try to find matching enum value
                for pc in PydanticCategory:
                    if pc.value == cat.id or pc.value == cat.name.lower().replace(" ", "_"):
                        categories.append(pc)
                        break

            # Map DB laws to GermanLaw Pydantic models
            laws = []
            for law in cl.laws:
                laws.append(GermanLaw(
                    paragraph=f"§ {law.section} {law.code.upper()}" if law.code != "netzdg" else f"NetzDG § {law.section}",
                    title=law.name or "",
                    title_de=law.name_de or "",
                    description="",
                    description_de="",
                    max_penalty=law.max_penalty or "",
                    applies_because="",
                    applies_because_de="",
                ))

            classification = ClassificationResult(
                severity=Severity(cl.severity) if cl.severity else Severity.LOW,
                categories=categories or [PydanticCategory.HARASSMENT],
                confidence=cl.confidence or 0.0,
                requires_immediate_action=cl.severity in ("critical", "high"),
                summary=cl.summary or "",
                summary_de=cl.summary_de or "",
                applicable_laws=laws,
                potential_consequences=cl.potential_consequences or "",
                potential_consequences_de=cl.potential_consequences_de or "",
            )

        evidence_items.append(EvidenceItem(
            id=ev.id,
            url=ev.source_url or "",
            platform=ev.platform or "unknown",
            captured_at=ev.timestamp_utc or datetime.now(timezone.utc),
            author_username="unknown",
            content_text=ev.raw_content,
            content_hash=ev.content_hash or "",
            archived_url=ev.archived_url,
            classification=classification,
        ))

    return Case(
        id=db_case.id,
        created_at=db_case.created_at or datetime.now(timezone.utc),
        updated_at=db_case.updated_at or datetime.now(timezone.utc),
        title=db_case.title or "Untitled Case",
        status=db_case.status or "open",
        overall_severity=Severity(db_case.overall_severity) if db_case.overall_severity and db_case.overall_severity != "none" else Severity.LOW,
        evidence_items=evidence_items,
    )
