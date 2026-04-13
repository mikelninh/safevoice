"""
Report generation — reads case data from DB, generates text/PDF/ZIP reports.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload

from app.database import get_db, Case as DBCase, EvidenceItem as DBEvidence, Org
from app.services.db_helpers import case_to_pydantic
from app.services.report_generator import generate_report
from app.services.pdf_generator import generate_pdf
from app.services.bafin_report import generate_bafin_report
from app.services.court_export import generate_court_package
from app.services.legal_pdf import generate_legal_pdf
from app.services.eml_builder import build_eml
from app.schemas import EmlBuildRequest
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{case_id}/legal-pdf")
def get_legal_pdf(
    case_id: str,
    db: Session = Depends(get_db),
):
    """
    NGO-grade legal PDF with org letterhead, chain-of-custody appendix, and
    disclosure block. Suitable for Strafanzeige filing.

    Uses the case's org (if any) for branding. Anonymous cases get default SafeVoice branding.
    """
    db_case = (
        db.query(DBCase)
        .options(
            joinedload(DBCase.evidence_items)
            .joinedload(DBEvidence.classification),
        )
        .filter(DBCase.id == case_id)
        .first()
    )
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")

    org = db.query(Org).filter(Org.id == db_case.org_id).first() if db_case.org_id else None

    pdf_bytes = generate_legal_pdf(db_case, org=org)
    filename = f"safevoice-legal-{case_id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{case_id}/eml")
def build_eml_endpoint(
    case_id: str,
    req: EmlBuildRequest,
    db: Session = Depends(get_db),
):
    """
    Build a downloadable .eml file for this case.

    Unlike mailto: (URL-length-limited, no attachments), an .eml file
    contains the full pre-filled email including:
      - From: the victim (so there's no spoofing)
      - To: the authority (ZAC / Polizei / HateAid / etc.)
      - Subject + body: personalized with victim data
      - Legal PDF attached (with embedded screenshots)
      - Hash-chain CSV attached (for independent verification)

    User downloads the .eml → double-click opens Apple Mail / Outlook /
    Thunderbird with everything ready, they just hit Send.
    """
    db_case = (
        db.query(DBCase)
        .options(
            joinedload(DBCase.evidence_items)
            .joinedload(DBEvidence.classification),
        )
        .filter(DBCase.id == case_id)
        .first()
    )
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")

    org = db.query(Org).filter(Org.id == db_case.org_id).first() if db_case.org_id else None

    # Use the requested report type (default 'police'). Recipient-template
    # mismatches (e.g. NetzDG body sent to police) are now caller-controlled.
    report_type = (req.report_type or "police").lower()
    if report_type not in {"general", "netzdg", "police"}:
        report_type = "police"
    pydantic_case = case_to_pydantic(db_case)
    report = generate_report(pydantic_case, report_type=report_type, lang="de")

    # Personalize body if victim data provided
    default_body = report.get("body", "")
    if req.victim_name:
        sender_block = req.victim_name
        if req.victim_address:
            sender_block += f"\n{req.victim_address}"
        if req.victim_phone:
            sender_block += f"\nTel: {req.victim_phone}"
        if req.victim_email:
            sender_block += f"\nE-Mail: {req.victim_email}"
        default_body = default_body.replace("[NAME DES OPFERS]", sender_block)
        default_body = default_body.replace("[UNTERSCHRIFT]", req.victim_name)

    body = req.body or default_body
    subject = req.subject or report.get("subject", f"Strafanzeige — Fall {case_id[:8]}")

    pdf_bytes = generate_legal_pdf(db_case, org=org)

    eml_bytes = build_eml(
        case=db_case,
        org=org,
        recipient_email=req.recipient_email,
        subject=subject,
        body=body,
        victim_email=req.victim_email,
        victim_name=req.victim_name,
        pdf_bytes=pdf_bytes,
        pdf_filename=f"safevoice-bericht-{case_id[:8]}.pdf",
    )

    filename = f"safevoice-strafanzeige-{case_id[:8]}.eml"
    return Response(
        content=eml_bytes,
        media_type="message/rfc822",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
