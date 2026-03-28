"""
Legal AI analysis + serial offender endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.data.mock_data import get_case_by_id
from app.services.legal_ai import analyze_case_legally, is_available as ai_available
from app.services.offender_db import (
    check_offender, get_serial_offenders, get_offender_stats, index_case,
)
from app.services.platform_submit import generate_platform_submission

router = APIRouter(tags=["legal"])


# === AI Legal Analysis (4.5) ===

@router.get("/legal/{case_id}")
def get_legal_analysis(case_id: str):
    """Get AI-powered legal analysis for a case."""
    case = get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    analysis = analyze_case_legally(case)
    return {
        "case_id": case_id,
        "ai_available": ai_available(),
        "analysis": analysis,
    }


# === Serial Offender Database (4.6) ===

@router.get("/offenders/check/{username}")
def check_offender_endpoint(username: str):
    """Check if a username is a known repeat offender."""
    result = check_offender(username)
    return {
        "username": username,
        "match": {
            "is_known": result.is_known,
            "is_serial": result.is_serial,
            "prior_cases": result.prior_cases,
            "prior_evidence": result.prior_evidence,
            "top_categories": result.top_categories,
            "max_severity": result.max_severity,
            "risk_level": result.risk_level,
        },
    }


@router.get("/offenders/serial")
def list_serial_offenders():
    """List all serial offenders (3+ cases). Anonymized."""
    return {
        "serial_offenders": get_serial_offenders(),
        "stats": get_offender_stats(),
    }


@router.get("/offenders/stats")
def offender_stats():
    """Aggregate offender database statistics."""
    return get_offender_stats()


# === Platform NetzDG Submission (4.7) ===

@router.get("/submit/{case_id}/{platform}")
def get_platform_submission(
    case_id: str,
    platform: str,
    lang: str = Query(default="de"),
):
    """Generate pre-filled NetzDG submission for a specific platform."""
    case = get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    submission = generate_platform_submission(case, platform, lang)
    return submission
