from fastapi import APIRouter, HTTPException, Query
from app.data.mock_data import get_case_by_id
from app.services.report_generator import generate_report

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
