"""
Phase 5: Policy Impact API endpoints.

Provides structured data exports for regulatory bodies, researchers,
and law-enforcement agencies.
"""

from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from app.database import get_db, Case as DBCase
from app.services.db_helpers import case_to_pydantic
from app.services.policy_export import (
    generate_evidence_standard,
    generate_dsa_report,
    generate_research_dataset,
    generate_dgeg_submission,
    generate_europol_siena,
    _build_data_dictionary,
)

router = APIRouter(prefix="/policy", tags=["policy"])


def _get_all_pydantic_cases(db: Session):
    db_cases = db.query(DBCase).all()
    return [case_to_pydantic(c) for c in db_cases]


@router.get("/evidence-standard")
def evidence_standard():
    """5.1 — SafeVoice evidence format specification (Bundestag proposal)."""
    return generate_evidence_standard()


@router.get("/dsa-report")
def dsa_report(lang: str = Query(default="de", description="de | en"), db: Session = Depends(get_db)):
    """5.2 — EU Digital Services Act Art. 15/24 transparency report."""
    cases = _get_all_pydantic_cases(db)
    return generate_dsa_report(cases, lang=lang)


@router.get("/research-dataset")
def research_dataset(db: Session = Depends(get_db)):
    """5.3 — Fully anonymized dataset for academic researchers."""
    cases = _get_all_pydantic_cases(db)
    return generate_research_dataset(cases)


@router.get("/research-dictionary")
def research_dictionary():
    """5.3 — Data dictionary describing the anonymized research dataset."""
    return {"data_dictionary": _build_data_dictionary()}


@router.get("/dgeg-submission")
def dgeg_submission(lang: str = Query(default="de", description="de | en"), db: Session = Depends(get_db)):
    """5.4 — Digitale-Gewalt-Gesetz parliament consultation data."""
    cases = _get_all_pydantic_cases(db)
    return generate_dgeg_submission(cases, lang=lang)


@router.get("/europol-siena")
def europol_siena(db: Session = Depends(get_db)):
    """5.5 — Europol SIENA cross-border flagging package."""
    cases = _get_all_pydantic_cases(db)
    return generate_europol_siena(cases)
