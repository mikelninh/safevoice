"""
Authentication service — magic link auth, DB-backed.

No passwords. Email-only login. Tokens and sessions persist to the database
so they survive Railway cold-starts, multi-instance deployments, and app
restarts.

Flow:
1. User enters email → POST /auth/login
2. Service creates/finds User in DB, issues a magic-link token (15 min TTL),
   persists it to `magic_link_tokens`
3. User clicks link → POST /auth/verify with the token
4. Service marks the magic link as used, creates a session (30 day TTL),
   persists it to `session_tokens`, returns session token
5. All authenticated requests use Authorization: Bearer <session_token>
"""

from __future__ import annotations

import secrets
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session as SASession

from app.database import (
    SessionLocal,
    User as UserORM,
    MagicLinkToken,
    SessionToken,
)
from app.models.user import User, MagicLink, Session, UserStatus

logger = logging.getLogger(__name__)

MAGIC_LINK_EXPIRY = timedelta(minutes=15)
SESSION_EXPIRY = timedelta(days=30)

# ── Legacy test shims ──
# The pre-migration implementation exposed module-level dicts that some tests
# import for convenience. Keep empty dicts so those imports still succeed; the
# actual data lives in the database now.
_magic_links: dict[str, object] = {}
_sessions: dict[str, object] = {}
_users: dict[str, object] = {}


# ── Helpers ─────────────────────────────────────────────────────────────

def _orm_user_to_domain(u: UserORM) -> User:
    """Map the SQLAlchemy User to the Pydantic domain object the router uses."""
    status = UserStatus.DELETED if u.deleted_at else UserStatus.ACTIVE
    return User(
        id=u.id,
        email=u.email,
        display_name=u.display_name,
        lang=(u.language or "de"),
        status=status,
        created_at=u.created_at or datetime.now(timezone.utc),
        last_login=u.last_login,
        deleted_at=u.deleted_at,
    )


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Public API (signatures preserved for the router) ────────────────────

def request_magic_link(email: str) -> MagicLink:
    """Create a magic link for the given email. If user doesn't exist, create them."""
    email = email.lower().strip()
    now = _utcnow()

    db: SASession = SessionLocal()
    try:
        user_row = db.execute(
            select(UserORM).where(UserORM.email == email)
        ).scalar_one_or_none()

        if not user_row:
            user_row = UserORM(email=email, language="de", status="active")
            db.add(user_row)
            db.flush()  # assign id

        token = secrets.token_urlsafe(32)
        expires_at = now + MAGIC_LINK_EXPIRY
        mlt = MagicLinkToken(
            user_id=user_row.id,
            token=token,
            email=email,
            created_at=now,
            expires_at=expires_at,
        )
        db.add(mlt)
        db.commit()
        db.refresh(mlt)

        logger.info(f"Magic link created for {email} (expires {expires_at})")

        return MagicLink(
            id=mlt.id,
            user_id=mlt.user_id,
            token=mlt.token,
            email=mlt.email,
            created_at=mlt.created_at,
            expires_at=mlt.expires_at,
            used=mlt.used_at is not None,
        )
    finally:
        db.close()


def verify_magic_link(token: str) -> Session | None:
    """Verify a magic-link token; on success create + return a session. None otherwise."""
    db: SASession = SessionLocal()
    try:
        link = db.execute(
            select(MagicLinkToken).where(MagicLinkToken.token == token)
        ).scalar_one_or_none()
        if not link:
            return None

        now = _utcnow()
        if link.used_at is not None:
            return None
        # Normalise possibly-naive DB timestamps for comparison.
        expires_at = link.expires_at.replace(tzinfo=timezone.utc) if link.expires_at.tzinfo is None else link.expires_at
        if now > expires_at:
            return None

        user_row = db.get(UserORM, link.user_id)
        if not user_row or user_row.deleted_at is not None:
            return None

        # Burn the magic link — single use.
        link.used_at = now

        # Touch the user.
        user_row.last_login = now

        # Issue a session.
        session_token = secrets.token_urlsafe(48)
        sess_row = SessionToken(
            user_id=user_row.id,
            token=session_token,
            created_at=now,
            expires_at=now + SESSION_EXPIRY,
            active=True,
        )
        db.add(sess_row)
        db.commit()
        db.refresh(sess_row)

        return Session(
            id=sess_row.id,
            user_id=sess_row.user_id,
            token=sess_row.token,
            created_at=sess_row.created_at,
            expires_at=sess_row.expires_at,
            active=sess_row.active,
        )
    finally:
        db.close()


def get_session(token: str) -> Session | None:
    """Validate a session token. Returns None if missing, inactive or expired."""
    db: SASession = SessionLocal()
    try:
        row = db.execute(
            select(SessionToken).where(SessionToken.token == token)
        ).scalar_one_or_none()
        if not row or not row.active:
            return None
        expires_at = row.expires_at.replace(tzinfo=timezone.utc) if row.expires_at.tzinfo is None else row.expires_at
        if _utcnow() > expires_at:
            row.active = False
            db.commit()
            return None
        return Session(
            id=row.id,
            user_id=row.user_id,
            token=row.token,
            created_at=row.created_at,
            expires_at=row.expires_at,
            active=row.active,
        )
    finally:
        db.close()


def get_user(user_id: str) -> User | None:
    """Get user by ID — None if missing or soft-deleted."""
    db: SASession = SessionLocal()
    try:
        row = db.get(UserORM, user_id)
        if not row or row.deleted_at is not None:
            return None
        return _orm_user_to_domain(row)
    finally:
        db.close()


def get_user_by_session(token: str) -> User | None:
    """Resolve a session token to a domain User (or None)."""
    sess = get_session(token)
    if not sess:
        return None
    return get_user(sess.user_id)


def logout(token: str) -> bool:
    """Invalidate a session (idempotent). Returns True if a row was touched."""
    db: SASession = SessionLocal()
    try:
        row = db.execute(
            select(SessionToken).where(SessionToken.token == token)
        ).scalar_one_or_none()
        if not row:
            return False
        row.active = False
        db.commit()
        return True
    finally:
        db.close()


def soft_delete_user(user_id: str) -> bool:
    """GDPR Art. 17 soft-delete — 7-day recovery window. Invalidates all sessions."""
    db: SASession = SessionLocal()
    try:
        row = db.get(UserORM, user_id)
        if not row:
            return False
        row.deleted_at = _utcnow()
        # Invalidate sessions for this user.
        sessions = db.execute(
            select(SessionToken).where(SessionToken.user_id == user_id)
        ).scalars().all()
        for s in sessions:
            s.active = False
        db.commit()
        return True
    finally:
        db.close()


def emergency_delete_user(user_id: str) -> bool:
    """EMERGENCY: immediate hard-delete of user + all their magic links + sessions.

    No recovery. For victims in danger (perpetrator has device access).
    """
    db: SASession = SessionLocal()
    try:
        row = db.get(UserORM, user_id)
        if not row:
            return False
        email = row.email

        # Delete magic links + sessions for this user first (FK constraints).
        db.query(MagicLinkToken).filter(MagicLinkToken.user_id == user_id).delete(synchronize_session=False)
        db.query(SessionToken).filter(SessionToken.user_id == user_id).delete(synchronize_session=False)
        db.delete(row)
        db.commit()

        logger.info(f"EMERGENCY DELETE: user {user_id} ({email}) hard-deleted")
        return True
    finally:
        db.close()


def cleanup_expired():
    """Periodic housekeeping: drop expired magic links + sessions, hard-delete past grace."""
    now = _utcnow()
    db: SASession = SessionLocal()
    try:
        # Expired magic links.
        db.query(MagicLinkToken).filter(MagicLinkToken.expires_at < now).delete(synchronize_session=False)
        # Expired sessions.
        db.query(SessionToken).filter(SessionToken.expires_at < now).delete(synchronize_session=False)

        # Hard-delete soft-deleted users past the 7-day window.
        cutoff = now - timedelta(days=7)
        stale = db.execute(
            select(UserORM).where(UserORM.deleted_at.isnot(None)).where(UserORM.deleted_at < cutoff)
        ).scalars().all()
        for u in stale:
            db.query(MagicLinkToken).filter(MagicLinkToken.user_id == u.id).delete(synchronize_session=False)
            db.query(SessionToken).filter(SessionToken.user_id == u.id).delete(synchronize_session=False)
            db.delete(u)

        db.commit()
    finally:
        db.close()
