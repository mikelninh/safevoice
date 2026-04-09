"""
Shared test fixtures — seeds the database with mock cases for all tests.
"""

import pytest
from app.database import SessionLocal, init_db, seed_categories_and_laws, Base, engine
from app.database import Case as DBCase, EvidenceItem as DBEvidence, Classification as DBClassification, Category as DBCategory, Law as DBLaw
from app.data.mock_data import MOCK_CASES
from app.services.evidence import hash_content
from datetime import datetime, timezone


def _seed_mock_cases_to_db():
    """Convert the in-memory MOCK_CASES to DB records so existing tests pass."""
    db = SessionLocal()

    # Category/law mapping (classifier Category enum → DB category id)
    cat_map = {
        "harassment": "harassment",
        "threat": "threat",
        "death_threat": "threat",
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

    law_map = {
        "§ 185 StGB": "stgb-185",
        "§ 186 StGB": "stgb-186",
        "§ 187 StGB": "stgb-187",
        "§ 241 StGB": "stgb-241",
        "§ 126a StGB": "stgb-126a",
        "§ 263 StGB": "stgb-263",
        "§ 263a StGB": "stgb-263",
        "§ 269 StGB": "stgb-269",
        "NetzDG § 3": "netzdg-3",
        "§ 130 StGB": "stgb-130",
        "§ 201a StGB": "stgb-201a",
        "§ 238 StGB": "stgb-238",
    }

    for mock_case in MOCK_CASES:
        # Skip if already exists
        if db.query(DBCase).filter_by(id=mock_case.id).first():
            continue

        db_case = DBCase(
            id=mock_case.id,
            title=mock_case.title,
            status=mock_case.status,
            overall_severity=mock_case.overall_severity.value,
            created_at=mock_case.created_at,
            updated_at=mock_case.updated_at,
        )
        db.add(db_case)
        db.flush()

        for ev in mock_case.evidence_items:
            db_ev = DBEvidence(
                id=ev.id,
                case_id=mock_case.id,
                content_type=ev.content_type,
                raw_content=ev.content_text,
                content_hash=ev.content_hash,
                platform=ev.platform,
                source_url=ev.url,
                archived_url=ev.archived_url,
                timestamp_utc=ev.captured_at,
            )
            db.add(db_ev)
            db.flush()

            if ev.classification:
                cl = ev.classification
                db_cl = DBClassification(
                    id=f"cl-{ev.id}",
                    evidence_item_id=ev.id,
                    severity=cl.severity.value,
                    confidence=cl.confidence,
                    classifier_tier=3,
                    summary=cl.summary,
                    summary_de=cl.summary_de,
                    potential_consequences=cl.potential_consequences,
                    potential_consequences_de=cl.potential_consequences_de,
                )
                db.add(db_cl)
                db.flush()

                # Link categories
                seen_cats = set()
                for cat in cl.categories:
                    cat_id = cat_map.get(cat.value)
                    if cat_id and cat_id not in seen_cats:
                        db_cat = db.query(DBCategory).filter_by(id=cat_id).first()
                        if db_cat:
                            db_cl.categories.append(db_cat)
                            seen_cats.add(cat_id)

                # Link laws
                seen_laws = set()
                for law in cl.applicable_laws:
                    law_id = law_map.get(law.paragraph)
                    if law_id and law_id not in seen_laws:
                        db_law = db.query(DBLaw).filter_by(id=law_id).first()
                        if db_law:
                            db_cl.laws.append(db_law)
                            seen_laws.add(law_id)

    db.commit()
    db.close()


# Auto-seed on import (runs once per test session)
# Ensure tables exist first
init_db()
seed_categories_and_laws()
_seed_mock_cases_to_db()
