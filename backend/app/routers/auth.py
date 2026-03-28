"""
Authentication router — magic link login.
No passwords. Email-only.
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

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
