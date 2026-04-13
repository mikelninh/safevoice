"""
Case management — full CRUD backed by SQLAlchemy database.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db, Case as DBCase, EvidenceItem as DBEvidence
from app.schemas import (
    CaseOut, CaseListOut, CaseCreate, CaseUpdate,
    EvidenceCreate, EvidenceOut, ClassificationOut,
)
from app.services.db_helpers import (
    create_case, add_evidence_with_classification, get_last_hash,
)
from app.services.classifier import classify, ClassifierUnavailableError
from app.services.evidence import archive_url_sync
from app.services.scraper import scrape_url_sync, detect_platform

router = APIRouter(prefix="/cases", tags=["cases"])


def _load_case(db: Session, case_id: str) -> DBCase:
    """Load case with all relationships eagerly."""
    case = (
        db.query(DBCase)
        .options(
            joinedload(DBCase.evidence_items)
            .joinedload(DBEvidence.classification)
        )
        .filter(DBCase.id == case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


def _case_to_response(case: DBCase) -> CaseOut:
    """Convert DB case to API response."""
    evidence_items = []
    for ev in case.evidence_items:
        cl_out = None
        if ev.classification:
            cl = ev.classification
            cl_out = ClassificationOut(
                id=cl.id,
                severity=cl.severity or "none",
                confidence=cl.confidence or 0.0,
                classifier_tier=cl.classifier_tier,
                summary=cl.summary,
                summary_de=cl.summary_de,
                potential_consequences=cl.potential_consequences,
                potential_consequences_de=cl.potential_consequences_de,
                recommended_actions=cl.recommended_actions,
                recommended_actions_de=cl.recommended_actions_de,
                categories=[{"id": c.id, "name": c.name, "name_de": c.name_de} for c in cl.categories],
                laws=[{"id": l.id, "code": l.code, "section": l.section, "name": l.name, "name_de": l.name_de, "max_penalty": l.max_penalty} for l in cl.laws],
                classified_at=cl.classified_at,
            )
        evidence_items.append(EvidenceOut(
            id=ev.id,
            content_type=ev.content_type or "text",
            raw_content=ev.raw_content,
            extracted_text=ev.extracted_text,
            content_hash=ev.content_hash,
            hash_chain_previous=ev.hash_chain_previous,
            platform=ev.platform,
            source_url=ev.source_url,
            archived_url=ev.archived_url,
            timestamp_utc=ev.timestamp_utc,
            classification=cl_out,
        ))

    return CaseOut(
        id=case.id,
        title=case.title,
        summary=case.summary,
        summary_de=case.summary_de,
        status=case.status or "open",
        overall_severity=case.overall_severity or "none",
        created_at=case.created_at,
        updated_at=case.updated_at,
        evidence_count=len(evidence_items),
        evidence_items=evidence_items,
    )


@router.get("/", response_model=list[CaseListOut])
def list_cases(db: Session = Depends(get_db)):
    """List all cases (without nested evidence for performance)."""
    cases = db.query(DBCase).order_by(DBCase.updated_at.desc()).all()
    return [
        CaseListOut(
            id=c.id,
            title=c.title,
            status=c.status or "open",
            overall_severity=c.overall_severity or "none",
            created_at=c.created_at,
            updated_at=c.updated_at,
            evidence_count=len(c.evidence_items),
        )
        for c in cases
    ]


@router.get("/{case_id}", response_model=CaseOut)
def get_case(case_id: str, db: Session = Depends(get_db)):
    """Get case detail with all evidence and classifications."""
    case = _load_case(db, case_id)
    return _case_to_response(case)


@router.post("/", response_model=CaseOut)
def create_new_case(req: CaseCreate, db: Session = Depends(get_db)):
    """Create a new empty case."""
    case = create_case(db, title=req.title)
    return _case_to_response(case)


@router.put("/{case_id}", response_model=CaseOut)
def update_case(case_id: str, req: CaseUpdate, db: Session = Depends(get_db)):
    """Update case metadata."""
    case = _load_case(db, case_id)
    if req.title is not None:
        case.title = req.title
    if req.status is not None:
        case.status = req.status
    db.commit()
    db.refresh(case)
    return _case_to_response(case)


@router.delete("/{case_id}")
def delete_case(case_id: str, db: Session = Depends(get_db)):
    """Delete a case and all its evidence."""
    case = db.query(DBCase).filter_by(id=case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    db.delete(case)
    db.commit()
    return {"message": f"Case {case_id} deleted"}


@router.post("/{case_id}/evidence", response_model=EvidenceOut)
def add_evidence(case_id: str, req: EvidenceCreate, db: Session = Depends(get_db)):
    """Add evidence to a case — classify, hash, and persist."""
    # Verify case exists
    case = db.query(DBCase).filter_by(id=case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Single-tier LLM classifier
    tier = 1

    # Classify the text
    try:
        classification_result = classify(req.text)
    except ClassifierUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Get previous hash for chain
    previous_hash = get_last_hash(db, case_id)

    # Archive URL if provided
    archived_url = archive_url_sync(req.source_url) if req.source_url else None

    # Create evidence + classification in DB
    evidence = add_evidence_with_classification(
        db=db,
        case_id=case_id,
        text=req.text,
        classification_result=classification_result,
        content_type=req.content_type,
        source_url=req.source_url,
        author_username=req.author_username,
        platform=req.platform or detect_platform(req.source_url) if req.source_url else None,
        archived_url=archived_url,
        previous_hash=previous_hash,
        classifier_tier=tier,
        screenshot_base64=req.screenshot_base64,
    )

    # Build response
    cl = evidence.classification
    cl_out = None
    if cl:
        cl_out = ClassificationOut(
            id=cl.id,
            severity=cl.severity or "none",
            confidence=cl.confidence or 0.0,
            classifier_tier=cl.classifier_tier,
            summary=cl.summary,
            summary_de=cl.summary_de,
            potential_consequences=cl.potential_consequences,
            potential_consequences_de=cl.potential_consequences_de,
            recommended_actions=cl.recommended_actions,
            recommended_actions_de=cl.recommended_actions_de,
            categories=[{"id": c.id, "name": c.name, "name_de": c.name_de} for c in cl.categories],
            laws=[{"id": l.id, "code": l.code, "section": l.section, "name": l.name, "name_de": l.name_de, "max_penalty": l.max_penalty} for l in cl.laws],
            classified_at=cl.classified_at,
        )

    return EvidenceOut(
        id=evidence.id,
        content_type=evidence.content_type,
        raw_content=evidence.raw_content,
        extracted_text=evidence.extracted_text,
        content_hash=evidence.content_hash,
        hash_chain_previous=evidence.hash_chain_previous,
        platform=evidence.platform,
        source_url=evidence.source_url,
        archived_url=evidence.archived_url,
        timestamp_utc=evidence.timestamp_utc,
        classification=cl_out,
    )
