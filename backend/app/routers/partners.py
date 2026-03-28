"""
Partner API — RESTful endpoints for institutional partners.
Authentication via API key in X-API-Key header.
"""

from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel
from app.models.partner import CaseSubmission, OrgType, OrgRole
from app.services.partner_store import (
    get_org_by_api_key, create_organization, list_organizations,
    add_member, get_org_members, assign_case, get_org_assignments,
    update_assignment_status, get_case_assignments,
)
from app.services.classifier import classify
from app.services.evidence import hash_content, capture_timestamp
from app.models.evidence import EvidenceItem
from app.data.mock_data import get_case_by_id, get_all_cases
import uuid

router = APIRouter(prefix="/partners", tags=["partners"])


def _require_api_key(x_api_key: str | None):
    """Validate API key and return the organization."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    org = get_org_by_api_key(x_api_key)
    if not org:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return org


# === Organization management ===

class CreateOrgRequest(BaseModel):
    name: str
    org_type: OrgType
    contact_email: str
    bundesland: str | None = None
    description: str | None = None


@router.post("/organizations")
def create_org(req: CreateOrgRequest):
    """Create a new organization. Returns the org with its API key."""
    org = create_organization(
        name=req.name,
        org_type=req.org_type,
        contact_email=req.contact_email,
        bundesland=req.bundesland,
        description=req.description,
    )
    return {
        "organization": org,
        "api_key": org.api_key,
        "message": "Store this API key securely. It cannot be retrieved again.",
    }


@router.get("/organizations")
def list_orgs():
    """List all registered organizations (admin endpoint)."""
    orgs = list_organizations()
    # Strip API keys from listing
    return [
        {
            "id": o.id,
            "name": o.name,
            "org_type": o.org_type,
            "contact_email": o.contact_email,
            "bundesland": o.bundesland,
            "active": o.active,
        }
        for o in orgs
    ]


# === Member management ===

class AddMemberRequest(BaseModel):
    email: str
    display_name: str
    role: OrgRole = OrgRole.ANALYST


@router.post("/members")
def add_org_member(
    req: AddMemberRequest,
    x_api_key: str | None = Header(default=None),
):
    """Add a member to the authenticated organization."""
    org = _require_api_key(x_api_key)
    member = add_member(org.id, req.email, req.display_name, req.role)
    if not member:
        raise HTTPException(status_code=404, detail="Organization not found")
    return member


@router.get("/members")
def list_members(x_api_key: str | None = Header(default=None)):
    """List members of the authenticated organization."""
    org = _require_api_key(x_api_key)
    return get_org_members(org.id)


# === Case submission ===

@router.post("/cases/submit")
def submit_case(
    req: CaseSubmission,
    x_api_key: str | None = Header(default=None),
):
    """Submit a case via the partner API. Classifies content and creates evidence."""
    org = _require_api_key(x_api_key)

    classification = classify(req.text)
    content_hash = hash_content(req.text)
    captured_at = capture_timestamp()

    evidence = EvidenceItem(
        id=str(uuid.uuid4()),
        url=req.url or "",
        platform=req.platform,
        captured_at=captured_at,
        author_username=req.author_username,
        content_text=req.text,
        content_hash=content_hash,
        classification=classification,
    )

    return {
        "evidence": evidence,
        "classification": classification,
        "submitted_by": org.name,
        "priority": req.priority,
        "message": "Case submitted and classified.",
    }


# === Case retrieval ===

@router.get("/cases")
def list_partner_cases(
    x_api_key: str | None = Header(default=None),
):
    """List cases assigned to the authenticated organization."""
    org = _require_api_key(x_api_key)
    assignments = get_org_assignments(org.id)

    result = []
    for a in assignments:
        case = get_case_by_id(a.case_id)
        result.append({
            "assignment": a,
            "case": case,
        })
    return result


@router.get("/cases/{case_id}")
def get_partner_case(
    case_id: str,
    x_api_key: str | None = Header(default=None),
):
    """Get a specific case (if assigned to this organization)."""
    org = _require_api_key(x_api_key)
    assignments = get_org_assignments(org.id)

    if not any(a.case_id == case_id for a in assignments):
        raise HTTPException(status_code=403, detail="Case not assigned to your organization")

    case = get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


# === Case assignment ===

class AssignCaseRequest(BaseModel):
    case_id: str
    jurisdiction: str | None = None
    unit_type: str | None = None
    assigned_to: str | None = None


@router.post("/cases/assign")
def assign_case_endpoint(
    req: AssignCaseRequest,
    x_api_key: str | None = Header(default=None),
):
    """Assign a case to this organization."""
    org = _require_api_key(x_api_key)
    assignment = assign_case(
        case_id=req.case_id,
        org_id=org.id,
        jurisdiction=req.jurisdiction,
        unit_type=req.unit_type,
        assigned_to=req.assigned_to,
    )
    return assignment


class UpdateAssignmentRequest(BaseModel):
    status: str  # assigned, in_review, resolved, declined
    notes: str | None = None


@router.put("/assignments/{assignment_id}")
def update_assignment(
    assignment_id: str,
    req: UpdateAssignmentRequest,
    x_api_key: str | None = Header(default=None),
):
    """Update the status of a case assignment."""
    _require_api_key(x_api_key)
    assignment = update_assignment_status(assignment_id, req.status, req.notes)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment
