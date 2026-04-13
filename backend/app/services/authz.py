"""
Authorization service — centralized access control for cases and orgs.

Design principle: *authorization is not duplicated across routers*. Every
endpoint that touches a case or org calls the helpers here. Future RLS
migration (Supabase) can replace these helpers with DB-level policies
without changing endpoint code.

Roles (strongest → weakest):
  owner > admin > caseworker > viewer

Actions and required roles:
  read       → viewer+
  write      → caseworker+ (and assignee for case writes)
  delete     → admin+
  manage_org → admin+
  transfer   → owner
"""

from __future__ import annotations

from typing import Literal
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database import Case, Org, OrgMember, User


Action = Literal["read", "write", "delete", "export", "manage_org", "transfer"]
Role = Literal["owner", "admin", "caseworker", "viewer"]

# Ordered from strongest to weakest
_ROLE_ORDER: list[Role] = ["owner", "admin", "caseworker", "viewer"]
_ROLE_RANK = {r: i for i, r in enumerate(_ROLE_ORDER)}

# Minimum role required per action
_MIN_ROLE_FOR_ACTION: dict[Action, Role] = {
    "read": "viewer",
    "export": "viewer",
    "write": "caseworker",
    "delete": "admin",
    "manage_org": "admin",
    "transfer": "owner",
}


def role_meets(actual: str, required: Role) -> bool:
    """True iff `actual` is at least as strong as `required`. Unknown role → False."""
    if actual not in _ROLE_RANK:
        return False
    return _ROLE_RANK[actual] <= _ROLE_RANK[required]


def get_membership(db: Session, user_id: str, org_id: str) -> OrgMember | None:
    return (
        db.query(OrgMember)
        .filter(OrgMember.user_id == user_id, OrgMember.org_id == org_id)
        .first()
    )


def require_case_access(
    case_id: str,
    db: Session,
    user: User,
    *,
    action: Action = "read",
) -> Case:
    """
    Load a case and verify `user` has permission for `action`.

    Access rules (first match wins):
      1. Case creator (case.user_id == user.id) → always allowed for any action they own
      2. Org member with sufficient role → allowed per _MIN_ROLE_FOR_ACTION
      3. Assigned caseworker → can 'read' and 'write'

    Raises 404 if case doesn't exist, 403 if access denied.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # 1. Case creator has full access
    if case.user_id and case.user_id == user.id:
        return case

    # 2. Assignee can read + write but not delete
    if case.assigned_to == user.id and action in ("read", "write", "export"):
        return case

    # 3. Org membership
    if case.org_id:
        # Visibility must permit it — 'private' cases are creator-only
        if case.visibility == "private" and case.user_id and case.user_id != user.id:
            # Private case: only creator (rule 1 above) + assignee (rule 2 above)
            raise HTTPException(status_code=403, detail="Private case — only the creator has access")

        membership = get_membership(db, user.id, case.org_id)
        if not membership:
            raise HTTPException(status_code=403, detail="Not a member of this case's organization")

        required_role = _MIN_ROLE_FOR_ACTION[action]
        if not role_meets(membership.role, required_role):
            raise HTTPException(
                status_code=403,
                detail=f"Role '{membership.role}' cannot {action} (requires {required_role}+)",
            )

        return case

    # 4. Orphan cases (no user_id, no org_id) — should not happen post-migration
    raise HTTPException(status_code=403, detail="Case has no owner; access denied")


def require_org_access(
    org_id: str,
    db: Session,
    user: User,
    *,
    action: Action = "read",
) -> tuple[Org, OrgMember]:
    """
    Load an org and verify user is a member with sufficient role.
    Returns (org, membership) if OK.
    """
    org = db.query(Org).filter(Org.id == org_id).first()
    if not org:
        # Allow lookup by slug as a convenience
        org = db.query(Org).filter(Org.slug == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    membership = get_membership(db, user.id, org.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    required_role = _MIN_ROLE_FOR_ACTION[action]
    if not role_meets(membership.role, required_role):
        raise HTTPException(
            status_code=403,
            detail=f"Role '{membership.role}' cannot {action} (requires {required_role}+)",
        )

    return org, membership


def list_accessible_cases(db: Session, user: User) -> list[Case]:
    """
    Return all cases this user can read.

    Includes:
      - Cases they created (case.user_id == user.id)
      - Cases assigned to them (case.assigned_to == user.id)
      - Cases in orgs they're a member of (unless visibility='private' by someone else)
    """
    # Own cases
    own = db.query(Case).filter(Case.user_id == user.id).all()
    # Assigned cases
    assigned = db.query(Case).filter(Case.assigned_to == user.id).all()
    # Org cases (non-private)
    org_ids = [m.org_id for m in user.org_memberships]
    org_cases = []
    if org_ids:
        org_cases = (
            db.query(Case)
            .filter(Case.org_id.in_(org_ids))
            .filter(Case.visibility != "private")
            .all()
        )

    # Deduplicate
    seen = set()
    result = []
    for case in own + assigned + org_cases:
        if case.id not in seen:
            seen.add(case.id)
            result.append(case)
    return result
