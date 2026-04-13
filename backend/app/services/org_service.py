"""
Org service — business logic for organization + membership management.

Kept separate from the router so routing layer stays thin and testable.
"""

from __future__ import annotations

import re
import json
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database import Org, OrgMember, User, gen_uuid
from app.services.authz import Role, role_meets


def _slugify(text: str) -> str:
    """Produce URL-safe slug. Lowercase, hyphens, alphanumeric only."""
    s = re.sub(r"[^\w\s-]", "", text.lower())
    s = re.sub(r"[-\s]+", "-", s).strip("-")
    return s or "org"


def create_org(
    db: Session,
    *,
    slug: str,
    display_name: str,
    contact_email: Optional[str],
    owner: User,
) -> Org:
    """Create a new org and make `owner` its first member with role='owner'."""
    slug = _slugify(slug)

    existing = db.query(Org).filter(Org.slug == slug).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Org with slug '{slug}' already exists")

    org = Org(
        id=gen_uuid(),
        slug=slug,
        display_name=display_name,
        contact_email=contact_email,
        settings_json="{}",
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(org)
    db.flush()  # get org.id without full commit

    membership = OrgMember(
        user_id=owner.id,
        org_id=org.id,
        role="owner",
        joined_at=datetime.utcnow(),
    )
    db.add(membership)
    db.commit()
    db.refresh(org)
    return org


def add_member(
    db: Session,
    *,
    org: Org,
    user: User,
    role: Role,
    invited_by: Optional[User] = None,
) -> OrgMember:
    """Add a user to an org. Idempotent: if already a member, updates role."""
    existing = (
        db.query(OrgMember)
        .filter(OrgMember.user_id == user.id, OrgMember.org_id == org.id)
        .first()
    )
    if existing:
        existing.role = role
        db.commit()
        return existing

    membership = OrgMember(
        user_id=user.id,
        org_id=org.id,
        role=role,
        joined_at=datetime.utcnow(),
        invited_by=invited_by.id if invited_by else None,
    )
    db.add(membership)
    db.commit()
    return membership


def remove_member(db: Session, *, org: Org, user_id: str) -> None:
    """Remove a user from an org. Enforces: can't remove the last owner."""
    membership = (
        db.query(OrgMember)
        .filter(OrgMember.user_id == user_id, OrgMember.org_id == org.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=404, detail="Member not found in this org")

    if membership.role == "owner":
        owner_count = (
            db.query(OrgMember)
            .filter(OrgMember.org_id == org.id, OrgMember.role == "owner")
            .count()
        )
        if owner_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove the last owner. Transfer ownership first.",
            )

    db.delete(membership)
    db.commit()


def change_member_role(
    db: Session,
    *,
    org: Org,
    user_id: str,
    new_role: Role,
    changed_by: User,
) -> OrgMember:
    """Change a member's role. Only owners can create other owners."""
    changer = (
        db.query(OrgMember)
        .filter(OrgMember.user_id == changed_by.id, OrgMember.org_id == org.id)
        .first()
    )
    if not changer:
        raise HTTPException(status_code=403, detail="You're not a member of this org")

    # Promoting to owner requires being an owner yourself
    if new_role == "owner" and changer.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can appoint other owners")

    membership = (
        db.query(OrgMember)
        .filter(OrgMember.user_id == user_id, OrgMember.org_id == org.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=404, detail="Member not found")

    # Demoting the last owner is blocked
    if membership.role == "owner" and new_role != "owner":
        owner_count = (
            db.query(OrgMember)
            .filter(OrgMember.org_id == org.id, OrgMember.role == "owner")
            .count()
        )
        if owner_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot demote the last owner. Appoint another owner first.",
            )

    membership.role = new_role
    db.commit()
    return membership


def list_orgs_for_user(db: Session, user: User) -> list[Org]:
    """All orgs the user is a member of, newest first."""
    return (
        db.query(Org)
        .join(OrgMember, OrgMember.org_id == Org.id)
        .filter(OrgMember.user_id == user.id)
        .order_by(Org.created_at.desc())
        .all()
    )


def get_org_settings(org: Org) -> dict:
    """Parse settings_json safely; returns {} on malformed data."""
    try:
        return json.loads(org.settings_json or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}


def update_org_settings(db: Session, *, org: Org, updates: dict) -> Org:
    """Merge-update org settings. Validates keys against allowed list."""
    allowed_keys = {
        "letterhead_url",
        "letterhead_text",
        "primary_color",
        "default_language",
        "default_visibility",
        "signature_url",
    }
    invalid = set(updates) - allowed_keys
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unknown settings keys: {sorted(invalid)}")

    current = get_org_settings(org)
    current.update(updates)
    org.settings_json = json.dumps(current)
    db.commit()
    db.refresh(org)
    return org
