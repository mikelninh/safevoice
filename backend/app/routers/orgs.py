"""
Organization router — multi-tenant NGO accounts.

Endpoints:
  POST   /orgs                              Create org (current user becomes owner)
  GET    /orgs                              List orgs the current user is a member of
  GET    /orgs/{slug_or_id}                 Org detail
  PUT    /orgs/{slug_or_id}                 Update org metadata / settings
  DELETE /orgs/{slug_or_id}                 Delete org (owner only)

  GET    /orgs/{slug_or_id}/members         List members
  POST   /orgs/{slug_or_id}/members         Invite user by email (creates user if needed)
  PUT    /orgs/{slug_or_id}/members/{uid}   Change role
  DELETE /orgs/{slug_or_id}/members/{uid}   Remove member
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.database import get_db, Org, OrgMember, User
from app.schemas import (
    OrgCreate, OrgUpdate, OrgOut,
    MemberInvite, MemberRoleUpdate, MemberOut,
)
from app.services.authz import require_org_access, get_membership
from app.services import org_service
from app.services.auth import get_user_by_session
from app.services.auth import get_user  # uses in-memory user registry for legacy flows


router = APIRouter(prefix="/orgs", tags=["orgs"])


# ── Auth dependency (reused from auth router pattern) ──

def _current_user(db: Session, authorization: str | None) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    token = authorization.replace("Bearer ", "").strip()
    pydantic_user = get_user_by_session(token)
    if not pydantic_user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    # Upsert the in-memory user into the DB so FK constraints work for org membership.
    # (Legacy auth uses Pydantic models; new multi-tenant flows use the SQLAlchemy User.)
    db_user = db.query(User).filter(User.id == pydantic_user.id).first()
    if not db_user:
        db_user = User(
            id=pydantic_user.id,
            email=pydantic_user.email,
            display_name=pydantic_user.display_name,
            language=pydantic_user.lang,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    return db_user


def current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    return _current_user(db, authorization)


# ── Helpers ──

def _org_out(org: Org, membership: OrgMember | None = None) -> OrgOut:
    return OrgOut(
        id=org.id,
        slug=org.slug,
        display_name=org.display_name,
        contact_email=org.contact_email,
        status=org.status or "active",
        created_at=org.created_at,
        settings=org_service.get_org_settings(org),
        member_count=len(org.members) if org.members else 0,
        my_role=membership.role if membership else None,
    )


def _member_out(member: OrgMember, db: Session) -> MemberOut:
    user = db.query(User).filter(User.id == member.user_id).first()
    return MemberOut(
        user_id=member.user_id,
        org_id=member.org_id,
        role=member.role,
        joined_at=member.joined_at,
        email=user.email if user else None,
        display_name=user.display_name if user else None,
    )


# ── Org CRUD ──

@router.post("", response_model=OrgOut)
def create_org_endpoint(
    req: OrgCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Create a new org. The authenticated user becomes its first owner."""
    org = org_service.create_org(
        db,
        slug=req.slug,
        display_name=req.display_name,
        contact_email=req.contact_email,
        owner=user,
    )
    # fetch the owner membership for the response
    membership = get_membership(db, user.id, org.id)
    return _org_out(org, membership)


@router.get("", response_model=list[OrgOut])
def list_orgs_endpoint(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """List orgs the current user belongs to."""
    orgs = org_service.list_orgs_for_user(db, user)
    result = []
    for org in orgs:
        membership = get_membership(db, user.id, org.id)
        result.append(_org_out(org, membership))
    return result


@router.get("/{slug_or_id}", response_model=OrgOut)
def get_org_endpoint(
    slug_or_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    org, membership = require_org_access(slug_or_id, db, user, action="read")
    return _org_out(org, membership)


@router.put("/{slug_or_id}", response_model=OrgOut)
def update_org_endpoint(
    slug_or_id: str,
    req: OrgUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Update org metadata. Requires admin+ role."""
    org, membership = require_org_access(slug_or_id, db, user, action="manage_org")

    if req.display_name is not None:
        org.display_name = req.display_name
    if req.contact_email is not None:
        org.contact_email = req.contact_email
    if req.settings is not None:
        org_service.update_org_settings(db, org=org, updates=req.settings)

    db.commit()
    db.refresh(org)
    return _org_out(org, membership)


@router.delete("/{slug_or_id}")
def delete_org_endpoint(
    slug_or_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Delete org. Requires owner role. Cases in the org are NOT deleted; they become orphans."""
    org, _ = require_org_access(slug_or_id, db, user, action="transfer")  # owner-only
    db.delete(org)
    db.commit()
    return {"message": f"Org {org.slug} deleted"}


# ── Member management ──

@router.get("/{slug_or_id}/members", response_model=list[MemberOut])
def list_members(
    slug_or_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    org, _ = require_org_access(slug_or_id, db, user, action="read")
    return [_member_out(m, db) for m in org.members]


@router.post("/{slug_or_id}/members", response_model=MemberOut)
def invite_member(
    slug_or_id: str,
    req: MemberInvite,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """
    Invite a user by email. Creates user record if they don't exist yet
    (they'll receive a magic-link email on first /auth/login).
    """
    org, _ = require_org_access(slug_or_id, db, user, action="manage_org")

    # Find or create user by email
    target = db.query(User).filter(User.email == req.email.lower()).first()
    if not target:
        target = User(
            email=req.email.lower(),
            display_name=None,
            language="de",
        )
        db.add(target)
        db.commit()
        db.refresh(target)

    if req.role not in ("owner", "admin", "caseworker", "viewer"):
        raise HTTPException(status_code=400, detail="Invalid role")

    # Only owners can invite owners
    current_membership = get_membership(db, user.id, org.id)
    if req.role == "owner" and (not current_membership or current_membership.role != "owner"):
        raise HTTPException(status_code=403, detail="Only owners can invite other owners")

    member = org_service.add_member(db, org=org, user=target, role=req.role, invited_by=user)
    return _member_out(member, db)


@router.put("/{slug_or_id}/members/{user_id}", response_model=MemberOut)
def update_member_role(
    slug_or_id: str,
    user_id: str,
    req: MemberRoleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    org, _ = require_org_access(slug_or_id, db, user, action="manage_org")
    if req.role not in ("owner", "admin", "caseworker", "viewer"):
        raise HTTPException(status_code=400, detail="Invalid role")

    member = org_service.change_member_role(
        db, org=org, user_id=user_id, new_role=req.role, changed_by=user,
    )
    return _member_out(member, db)


@router.delete("/{slug_or_id}/members/{user_id}")
def remove_member_endpoint(
    slug_or_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    org, _ = require_org_access(slug_or_id, db, user, action="manage_org")
    org_service.remove_member(db, org=org, user_id=user_id)
    return {"message": "Member removed"}
