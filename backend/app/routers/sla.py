from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.sla import SLARecord, SLAStatus, SLADashboard
from app.services.sla_tracker import (
    create_sla_record,
    get_records_by_case,
    get_record_by_id,
    get_all_records,
    update_sla_status,
    check_deadlines,
    get_dashboard,
)

router = APIRouter(prefix="/sla", tags=["sla"])


class CreateSLARequest(BaseModel):
    case_id: str
    evidence_id: str
    platform: str
    severity: str  # "critical", "high", "medium", "low"


class UpdateStatusRequest(BaseModel):
    status: SLAStatus
    platform_response: str | None = None


@router.post("/report", response_model=SLARecord)
def file_sla_report(req: CreateSLARequest):
    """Create an SLA record when filing a NetzDG report."""
    record = create_sla_record(
        case_id=req.case_id,
        evidence_id=req.evidence_id,
        platform=req.platform,
        severity=req.severity,
    )
    return record


@router.get("/dashboard", response_model=SLADashboard)
def sla_dashboard():
    """Get aggregate SLA dashboard stats across all records."""
    records = check_deadlines(get_all_records())
    return get_dashboard(records)


@router.get("/{case_id}", response_model=list[SLARecord])
def get_case_sla_records(case_id: str):
    """Get all SLA records for a case, with deadline status refreshed."""
    records = get_records_by_case(case_id)
    if not records:
        raise HTTPException(status_code=404, detail="No SLA records found for this case")
    return check_deadlines(records)


@router.put("/{record_id}/status", response_model=SLARecord)
def update_record_status(record_id: str, req: UpdateStatusRequest):
    """Update the status of an SLA record (reported, acknowledged, removed, etc.)."""
    record = get_record_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="SLA record not found")

    updated = update_sla_status(
        record_id=record_id,
        new_status=req.status,
        response=req.platform_response,
    )
    return updated
