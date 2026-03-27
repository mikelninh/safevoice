from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from app.data.mock_data import get_case_by_id
from app.services.report_generator import generate_report
from app.services.pdf_generator import generate_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{case_id}")
def get_report(
    case_id: str,
    report_type: str = Query(default="general", description="general | netzdg | police"),
    lang: str = Query(default="de", description="de | en")
):
    case = get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return generate_report(case, report_type=report_type, lang=lang)


@router.get("/{case_id}/pdf")
def get_report_pdf(
    case_id: str,
    report_type: str = Query(default="general", description="general | netzdg | police"),
    lang: str = Query(default="de", description="de | en")
):
    case = get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    pdf_bytes = generate_pdf(case, report_type=report_type, lang=lang)
    filename = f"safevoice_{case_id}_{report_type}_{lang}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
