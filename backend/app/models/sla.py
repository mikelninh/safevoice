from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class SLAStatus(str, Enum):
    PENDING = "pending"          # Report not yet filed
    REPORTED = "reported"        # Filed with platform
    ACKNOWLEDGED = "acknowledged" # Platform acknowledged receipt
    REMOVED = "removed"          # Content removed
    EXPIRED = "expired"          # Deadline passed without action
    APPEALED = "appealed"        # Platform rejected, appeal filed


class SLARecord(BaseModel):
    id: str
    case_id: str
    evidence_id: str
    platform: str
    reported_at: datetime | None = None
    deadline_24h: datetime | None = None  # For clearly illegal (critical severity)
    deadline_7d: datetime | None = None   # For other illegal content
    status: SLAStatus = SLAStatus.PENDING
    platform_response: str | None = None
    removed_at: datetime | None = None


class SLADashboard(BaseModel):
    total_reports: int
    pending: int
    within_deadline: int
    expired: int
    removed: int
    removal_rate: float
    avg_removal_hours: float | None
