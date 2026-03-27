from fastapi import APIRouter, HTTPException
from app.data.mock_data import get_all_cases, get_case_by_id
from app.models.evidence import Case

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("/", response_model=list[Case])
def list_cases():
    return get_all_cases()


@router.get("/{case_id}", response_model=Case)
def get_case(case_id: str):
    case = get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case
