"""
NetzDG SLA deadline tracking service.

Under Germany's NetzDG (Network Enforcement Act):
- Clearly illegal content (critical severity) must be removed within 24 hours
- Other illegal content must be removed within 7 days

This service tracks SLA deadlines, detects expiry, and computes dashboard stats.
"""

import uuid
from datetime import datetime, timedelta, timezone

from app.models.sla import SLADashboard, SLARecord, SLAStatus

# In-memory storage for MVP
_sla_records: list[SLARecord] = []


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def get_all_records() -> list[SLARecord]:
    """Return all SLA records."""
    return list(_sla_records)


def get_records_by_case(case_id: str) -> list[SLARecord]:
    """Return all SLA records for a given case."""
    return [r for r in _sla_records if r.case_id == case_id]


def get_record_by_id(record_id: str) -> SLARecord | None:
    """Return a single SLA record by ID."""
    for r in _sla_records:
        if r.id == record_id:
            return r
    return None


def create_sla_record(
    case_id: str,
    evidence_id: str,
    platform: str,
    severity: str,
) -> SLARecord:
    """
    Create a new SLA record with correct deadlines based on severity.

    CRITICAL severity -> 24-hour deadline (clearly illegal content under NetzDG)
    All other severities -> 7-day deadline (other illegal content under NetzDG)
    """
    now = _now_utc()
    record_id = f"sla-{uuid.uuid4().hex[:12]}"

    if severity.lower() == "critical":
        deadline_24h = now + timedelta(hours=24)
        deadline_7d = None
    else:
        deadline_24h = None
        deadline_7d = now + timedelta(days=7)

    record = SLARecord(
        id=record_id,
        case_id=case_id,
        evidence_id=evidence_id,
        platform=platform,
        reported_at=now,
        deadline_24h=deadline_24h,
        deadline_7d=deadline_7d,
        status=SLAStatus.REPORTED,
    )

    _sla_records.append(record)
    return record


def update_sla_status(
    record_id: str,
    new_status: SLAStatus,
    response: str | None = None,
) -> SLARecord | None:
    """
    Update the status of an SLA record.

    If the new status is REMOVED, the removed_at timestamp is set automatically.
    """
    for i, r in enumerate(_sla_records):
        if r.id == record_id:
            update_data: dict = {"status": new_status}
            if response is not None:
                update_data["platform_response"] = response
            if new_status == SLAStatus.REMOVED:
                update_data["removed_at"] = _now_utc()

            updated = r.model_copy(update=update_data)
            _sla_records[i] = updated
            return updated
    return None


def check_deadlines(records: list[SLARecord]) -> list[SLARecord]:
    """
    Check all records and mark expired ones.

    A record is expired if:
    - It has a 24h deadline that has passed and status is not REMOVED
    - It has a 7d deadline that has passed and status is not REMOVED
    Only records in active states (REPORTED, ACKNOWLEDGED) can expire.
    """
    now = _now_utc()
    active_statuses = {SLAStatus.REPORTED, SLAStatus.ACKNOWLEDGED}
    updated: list[SLARecord] = []

    for record in records:
        if record.status not in active_statuses:
            updated.append(record)
            continue

        expired = False
        if record.deadline_24h and now > record.deadline_24h:
            expired = True
        if record.deadline_7d and now > record.deadline_7d:
            expired = True

        if expired:
            marked = record.model_copy(update={"status": SLAStatus.EXPIRED})
            updated.append(marked)
            # Also update in-memory storage
            for i, stored in enumerate(_sla_records):
                if stored.id == record.id:
                    _sla_records[i] = marked
                    break
        else:
            updated.append(record)

    return updated


def get_dashboard(records: list[SLARecord]) -> SLADashboard:
    """
    Compute aggregate SLA dashboard statistics from a list of records.
    """
    total = len(records)
    if total == 0:
        return SLADashboard(
            total_reports=0,
            pending=0,
            within_deadline=0,
            expired=0,
            removed=0,
            removal_rate=0.0,
            avg_removal_hours=None,
        )

    now = _now_utc()
    pending = sum(1 for r in records if r.status == SLAStatus.PENDING)
    expired = sum(1 for r in records if r.status == SLAStatus.EXPIRED)
    removed = sum(1 for r in records if r.status == SLAStatus.REMOVED)

    # Within deadline: active records (REPORTED/ACKNOWLEDGED) whose deadline hasn't passed
    within_deadline = 0
    for r in records:
        if r.status in (SLAStatus.REPORTED, SLAStatus.ACKNOWLEDGED):
            deadline = r.deadline_24h or r.deadline_7d
            if deadline and now <= deadline:
                within_deadline += 1

    removal_rate = (removed / total) * 100 if total > 0 else 0.0

    # Average removal time in hours
    removal_hours: list[float] = []
    for r in records:
        if r.status == SLAStatus.REMOVED and r.removed_at and r.reported_at:
            delta = (r.removed_at - r.reported_at).total_seconds() / 3600
            removal_hours.append(delta)

    avg_removal_hours = (
        sum(removal_hours) / len(removal_hours) if removal_hours else None
    )

    return SLADashboard(
        total_reports=total,
        pending=pending,
        within_deadline=within_deadline,
        expired=expired,
        removed=removed,
        removal_rate=round(removal_rate, 1),
        avg_removal_hours=round(avg_removal_hours, 1) if avg_removal_hours is not None else None,
    )


def clear_records() -> None:
    """Clear all SLA records. Used for testing."""
    _sla_records.clear()
