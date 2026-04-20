"""
Authentication router — magic link login.
No passwords. Email-only.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.database import (
    get_db,
    Case as DBCase,
    EvidenceItem as DBEvidence,
    Org as DBOrg,
    OrgMember as DBOrgMember,
)
from app.schemas import (
    UserExport, ExportUser, ExportCase, ExportEvidence,
    ExportClassification, ExportOrgMembership,
)
from app.services.auth import (
    request_magic_link, verify_magic_link, get_user_by_session,
    logout, soft_delete_user, emergency_delete_user, get_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _require_user(authorization: str | None):
    """Extract and validate session token from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    token = authorization.replace("Bearer ", "").strip()
    user = get_user_by_session(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return user, token


# === Login flow ===

class LoginRequest(BaseModel):
    email: str


class LoginResponse(BaseModel):
    message: str
    magic_link_token: str | None = None  # MVP: returned directly. Production: sent via email


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    """
    Request a magic link login.
    MVP: returns the token directly (production: sends email).
    """
    email = req.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email required")

    link = request_magic_link(email)

    # MVP: return token directly (production: send via email, return only message)
    return LoginResponse(
        message=f"Magic link sent to {email}. Check your inbox.",
        magic_link_token=link.token,  # Remove in production
    )


class VerifyRequest(BaseModel):
    token: str


@router.post("/verify")
def verify(req: VerifyRequest):
    """Verify a magic link token and create a session."""
    session = verify_magic_link(req.token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid, expired, or already used magic link")

    user = get_user(session.user_id)

    return {
        "session_token": session.token,
        "expires_at": session.expires_at.isoformat(),
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "lang": user.lang,
        },
    }


# === Authenticated endpoints ===

@router.get("/me")
def get_me(authorization: str | None = Header(default=None)):
    """Get the currently authenticated user."""
    user, _ = _require_user(authorization)
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "lang": user.lang,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


class UpdateProfileRequest(BaseModel):
    display_name: str | None = None
    lang: str | None = None


@router.put("/me")
def update_me(
    req: UpdateProfileRequest,
    authorization: str | None = Header(default=None),
):
    """Update user profile."""
    user, _ = _require_user(authorization)
    if req.display_name is not None:
        user.display_name = req.display_name
    if req.lang is not None and req.lang in ("de", "en"):
        user.lang = req.lang
    return {"message": "Profile updated", "user": {"display_name": user.display_name, "lang": user.lang}}


@router.post("/logout")
def logout_endpoint(authorization: str | None = Header(default=None)):
    """Invalidate the current session."""
    _, token = _require_user(authorization)
    logout(token)
    return {"message": "Logged out"}


# === Deletion ===

@router.delete("/me")
def delete_account(authorization: str | None = Header(default=None)):
    """
    Soft-delete account. Data hidden immediately, hard-deleted after 7 days.
    User can still log in during the 7-day window to recover.
    """
    user, _ = _require_user(authorization)
    soft_delete_user(user.id)
    return {
        "message": "Account scheduled for deletion. Data will be permanently removed in 7 days.",
        "hard_delete_after": "7 days",
    }


@router.delete("/me/emergency")
def emergency_delete(authorization: str | None = Header(default=None)):
    """
    EMERGENCY: Immediately and permanently delete ALL data.
    No recovery. For victims in danger.
    """
    user, _ = _require_user(authorization)
    emergency_delete_user(user.id)
    return {
        "message": "All data permanently deleted. This cannot be undone.",
        "recovered": False,
    }


# === GDPR Art. 20 — Right to data portability ===

def _iso(dt) -> str | None:
    """Normalize any datetime to ISO-8601 UTC (Z-suffixed when naive)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _law_str(law) -> str:
    if law.code == "netzdg":
        return f"NetzDG § {law.section}"
    return f"§ {law.section} {law.code.upper()}"


@router.get("/me/export", response_model=UserExport)
def export_my_data(
    include_deleted: bool = False,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """GDPR Art. 20 — Right to data portability.

    Returns a complete JSON export of the authenticated user's profile,
    cases, evidence, classifications, and org memberships. Excludes
    sessions, magic-link tokens, other users' data. Reference data
    (categories/laws) is included by name/paragraph only.
    """
    user, _ = _require_user(authorization)

    cases = (
        db.query(DBCase)
        .options(joinedload(DBCase.evidence_items).joinedload(DBEvidence.classification))
        .filter(DBCase.user_id == user.id)
        .order_by(DBCase.created_at.asc())
        .all()
    )

    export_cases: list[ExportCase] = []
    for c in cases:
        evidence_out: list[ExportEvidence] = []
        for ev in c.evidence_items:
            cl = ev.classification
            cl_out = ExportClassification(
                severity=cl.severity or "none",
                confidence=cl.confidence or 0.0,
                summary=cl.summary,
                summary_de=cl.summary_de,
                potential_consequences=cl.potential_consequences,
                potential_consequences_de=cl.potential_consequences_de,
                categories=[cat.name for cat in cl.categories],
                laws=[_law_str(law) for law in cl.laws],
                classified_at=_iso(cl.classified_at),
            ) if cl else None
            evidence_out.append(ExportEvidence(
                id=ev.id,
                content_type=ev.content_type or "text",
                raw_content=ev.raw_content,
                content_hash=ev.content_hash,
                hash_chain_previous=ev.hash_chain_previous,
                platform=ev.platform,
                source_url=ev.source_url,
                archived_url=ev.archived_url,
                timestamp_utc=_iso(ev.timestamp_utc),
                classification=cl_out,
            ))
        export_cases.append(ExportCase(
            id=c.id, title=c.title,
            status=c.status or "open",
            overall_severity=c.overall_severity or "none",
            visibility=c.visibility, org_id=c.org_id,
            created_at=_iso(c.created_at), updated_at=_iso(c.updated_at),
            evidence_items=evidence_out,
        ))

    memberships = (
        db.query(DBOrgMember, DBOrg)
        .join(DBOrg, DBOrg.id == DBOrgMember.org_id)
        .filter(DBOrgMember.user_id == user.id)
        .all()
    )
    export_memberships = [
        ExportOrgMembership(org_id=o.id, org_slug=o.slug, role=m.role, joined_at=_iso(m.joined_at))
        for (m, o) in memberships
        if include_deleted or o.deleted_at is None
    ]

    payload = UserExport(
        export_version="1.0",
        exported_at=_iso(datetime.now(timezone.utc)),
        user=ExportUser(
            id=user.id, email=user.email, display_name=user.display_name,
            language=user.lang, created_at=_iso(user.created_at),
            deleted_at=_iso(user.deleted_at),
        ),
        cases=export_cases,
        org_memberships=export_memberships,
    )

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"safevoice-export-{user.id}-{today}.json"
    return JSONResponse(
        content=payload.model_dump(),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
