"""
Report generation — reads case data from DB, generates text/PDF/ZIP reports.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload

from app.database import get_db, Case as DBCase, EvidenceItem as DBEvidence
from app.services.db_helpers import case_to_pydantic
from app.services.report_generator import generate_report
from app.services.pdf_generator import generate_pdf
from app.services.bafin_report import generate_bafin_report
from app.services.court_export import generate_court_package

router = APIRouter(prefix="/reports", tags=["reports"])


def _get_case_as_pydantic(case_id: str, db: Session):
    """Load case from DB and convert to Pydantic model for report services."""
    db_case = (
        db.query(DBCase)
        .options(
            joinedload(DBCase.evidence_items)
            .joinedload(DBEvidence.classification)
        )
        .filter(DBCase.id == case_id)
        .first()
    )
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case_to_pydantic(db_case)


@router.get("/{case_id}")
def get_report(
    case_id: str,
    report_type: str = Query(default="general", description="general | netzdg | police"),
    lang: str = Query(default="de", description="de | en"),
    db: Session = Depends(get_db),
):
    case = _get_case_as_pydantic(case_id, db)
    return generate_report(case, report_type=report_type, lang=lang)


@router.get("/{case_id}/pdf")
def get_report_pdf(
    case_id: str,
    report_type: str = Query(default="general", description="general | netzdg | police"),
    lang: str = Query(default="de", description="de | en"),
    db: Session = Depends(get_db),
):
    case = _get_case_as_pydantic(case_id, db)
    pdf_bytes = generate_pdf(case, report_type=report_type, lang=lang)
    filename = f"safevoice_{case_id}_{report_type}_{lang}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{case_id}/bafin")
def get_bafin_report(
    case_id: str,
    lang: str = Query(default="de", description="de | en"),
    db: Session = Depends(get_db),
):
    case = _get_case_as_pydantic(case_id, db)
    report = generate_bafin_report(case, lang=lang)
    if not report:
        raise HTTPException(
            status_code=422,
            detail="This case does not contain scam/fraud evidence for a BaFin report.",
        )
    return report


@router.get("/{case_id}/court-package")
def get_court_package(
    case_id: str,
    lang: str = Query(default="de", description="de | en"),
    db: Session = Depends(get_db),
):
    """Download a complete court-ready evidence package (ZIP)."""
    case = _get_case_as_pydantic(case_id, db)
    zip_bytes = generate_court_package(case, lang=lang)
    filename = f"safevoice_{case_id}_court_package_{lang}.zip"
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
