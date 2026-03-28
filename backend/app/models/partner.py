"""
Partner and institutional account models.
Covers API keys, organizations, roles, and case assignment.
"""

from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class OrgType(str, Enum):
    POLICE = "police"
    NGO = "ngo"
    LAW_FIRM = "law_firm"
    UNIVERSITY = "university"
    EMPLOYER = "employer"
    GOVERNMENT = "government"
    OTHER = "other"


class OrgRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class Organization(BaseModel):
    id: str
    name: str
    org_type: OrgType
    contact_email: str
    api_key: str
    created_at: datetime
    active: bool = True
    bundesland: str | None = None
    description: str | None = None


class OrgMember(BaseModel):
    id: str
    org_id: str
    email: str
    display_name: str
    role: OrgRole
    created_at: datetime
    active: bool = True


class CaseAssignment(BaseModel):
    id: str
    case_id: str
    org_id: str
    assigned_to: str | None = None  # OrgMember ID
    assigned_at: datetime
    status: str = "assigned"  # assigned, in_review, resolved, declined
    jurisdiction: str | None = None  # Bundesland
    unit_type: str | None = None  # cybercrime, general, fraud
    notes: str | None = None


class CaseSubmission(BaseModel):
    """Inbound case submission from a partner via API."""
    text: str
    url: str = ""
    platform: str = "unknown"
    author_username: str = "unknown"
    victim_context: str = ""
    priority: str = "normal"  # normal, high, urgent
