"""
In-memory partner/organization store.
MVP: stores in memory. Production: replace with PostgreSQL.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from app.models.partner import (
    Organization, OrgType, OrgMember, OrgRole,
    CaseAssignment
)

# In-memory stores
_orgs: dict[str, Organization] = {}
_members: dict[str, OrgMember] = {}
_assignments: dict[str, CaseAssignment] = {}
_api_keys: dict[str, str] = {}  # api_key -> org_id


def generate_api_key() -> str:
    """Generate a secure API key."""
    return "sv_" + secrets.token_urlsafe(32)


def create_organization(
    name: str,
    org_type: OrgType,
    contact_email: str,
    bundesland: str | None = None,
    description: str | None = None,
) -> Organization:
    """Create a new organization and return it with its API key."""
    org_id = str(uuid.uuid4())
    api_key = generate_api_key()

    org = Organization(
        id=org_id,
        name=name,
        org_type=org_type,
        contact_email=contact_email,
        api_key=api_key,
        created_at=datetime.now(timezone.utc),
        bundesland=bundesland,
        description=description,
    )
    _orgs[org_id] = org
    _api_keys[api_key] = org_id
    return org


def get_org_by_api_key(api_key: str) -> Organization | None:
    """Look up organization by API key."""
    org_id = _api_keys.get(api_key)
    if org_id:
        return _orgs.get(org_id)
    return None


def get_org(org_id: str) -> Organization | None:
    return _orgs.get(org_id)


def list_organizations() -> list[Organization]:
    return list(_orgs.values())


def add_member(
    org_id: str,
    email: str,
    display_name: str,
    role: OrgRole = OrgRole.ANALYST,
) -> OrgMember | None:
    if org_id not in _orgs:
        return None
    member = OrgMember(
        id=str(uuid.uuid4()),
        org_id=org_id,
        email=email,
        display_name=display_name,
        role=role,
        created_at=datetime.now(timezone.utc),
    )
    _members[member.id] = member
    return member


def get_org_members(org_id: str) -> list[OrgMember]:
    return [m for m in _members.values() if m.org_id == org_id and m.active]


def assign_case(
    case_id: str,
    org_id: str,
    jurisdiction: str | None = None,
    unit_type: str | None = None,
    assigned_to: str | None = None,
) -> CaseAssignment:
    assignment = CaseAssignment(
        id=str(uuid.uuid4()),
        case_id=case_id,
        org_id=org_id,
        assigned_to=assigned_to,
        assigned_at=datetime.now(timezone.utc),
        jurisdiction=jurisdiction,
        unit_type=unit_type,
    )
    _assignments[assignment.id] = assignment
    return assignment


def get_case_assignments(case_id: str) -> list[CaseAssignment]:
    return [a for a in _assignments.values() if a.case_id == case_id]


def get_org_assignments(org_id: str) -> list[CaseAssignment]:
    return [a for a in _assignments.values() if a.org_id == org_id]


def update_assignment_status(
    assignment_id: str, status: str, notes: str | None = None
) -> CaseAssignment | None:
    a = _assignments.get(assignment_id)
    if not a:
        return None
    a.status = status
    if notes:
        a.notes = notes
    return a


# Seed demo org for testing
def seed_demo_org():
    """Create a demo police organization for testing."""
    if any(o.name == "LKA Berlin - Cybercrime" for o in _orgs.values()):
        return

    org = create_organization(
        name="LKA Berlin - Cybercrime",
        org_type=OrgType.POLICE,
        contact_email="cybercrime@polizei.berlin.de",
        bundesland="Berlin",
        description="Landeskriminalamt Berlin, Abteilung Cybercrime",
    )
    add_member(org.id, "k.mueller@polizei.berlin.de", "K. Müller", OrgRole.ADMIN)
    add_member(org.id, "s.schmidt@polizei.berlin.de", "S. Schmidt", OrgRole.ANALYST)

    # Also create HateAid demo
    ngo = create_organization(
        name="HateAid",
        org_type=OrgType.NGO,
        contact_email="intake@hateaid.org",
        description="Beratungsstelle für Betroffene digitaler Gewalt",
    )
    add_member(ngo.id, "beratung@hateaid.org", "Beratungsteam", OrgRole.ANALYST)


seed_demo_org()
