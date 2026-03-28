"""
Authentication service — magic link auth.
No passwords. Email-only login.

Flow:
1. User enters email → POST /auth/login
2. We generate a magic link token and "send" it (MVP: return in response)
3. User clicks link → POST /auth/verify?token=xxx
4. We create a session and return a session token
5. All authenticated requests use Authorization: Bearer <session_token>
"""

import secrets
import uuid
import logging
from datetime import datetime, timezone, timedelta

from app.models.user import User, MagicLink, Session, UserStatus

logger = logging.getLogger(__name__)

# In-memory stores (production: PostgreSQL)
_users: dict[str, User] = {}
_users_by_email: dict[str, str] = {}  # email -> user_id
_magic_links: dict[str, MagicLink] = {}  # token -> MagicLink
_sessions: dict[str, Session] = {}  # token -> Session

MAGIC_LINK_EXPIRY = timedelta(minutes=15)
SESSION_EXPIRY = timedelta(days=30)


def request_magic_link(email: str) -> MagicLink:
    """
    Create a magic link for the given email.
    If user doesn't exist, create them.
    """
    email = email.lower().strip()

    # Find or create user
    user_id = _users_by_email.get(email)
    if not user_id:
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email=email,
            created_at=datetime.now(timezone.utc),
        )
        _users[user_id] = user
        _users_by_email[email] = user_id

    now = datetime.now(timezone.utc)
    token = secrets.token_urlsafe(32)

    link = MagicLink(
        id=str(uuid.uuid4()),
        user_id=user_id,
        token=token,
        email=email,
        created_at=now,
        expires_at=now + MAGIC_LINK_EXPIRY,
    )
    _magic_links[token] = link

    logger.info(f"Magic link created for {email} (expires {link.expires_at})")
    return link


def verify_magic_link(token: str) -> Session | None:
    """
    Verify a magic link token and create a session.
    Returns None if token is invalid, expired, or already used.
    """
    link = _magic_links.get(token)
    if not link:
        return None

    now = datetime.now(timezone.utc)

    if link.used:
        return None
    if now > link.expires_at:
        return None

    # Mark as used
    link.used = True

    # Get user
    user = _users.get(link.user_id)
    if not user or user.status != UserStatus.ACTIVE:
        return None

    # Update last login
    user.last_login = now

    # Create session
    session_token = secrets.token_urlsafe(48)
    session = Session(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token=session_token,
        created_at=now,
        expires_at=now + SESSION_EXPIRY,
    )
    _sessions[session_token] = session

    return session


def get_session(token: str) -> Session | None:
    """Validate a session token."""
    session = _sessions.get(token)
    if not session:
        return None
    if not session.active:
        return None
    if datetime.now(timezone.utc) > session.expires_at:
        session.active = False
        return None
    return session


def get_user(user_id: str) -> User | None:
    """Get user by ID."""
    user = _users.get(user_id)
    if user and user.status == UserStatus.DELETED:
        return None
    return user


def get_user_by_session(token: str) -> User | None:
    """Get user from session token."""
    session = get_session(token)
    if not session:
        return None
    return get_user(session.user_id)


def logout(token: str) -> bool:
    """Invalidate a session."""
    session = _sessions.get(token)
    if session:
        session.active = False
        return True
    return False


def soft_delete_user(user_id: str) -> bool:
    """Soft-delete a user. Hard delete happens after 7 days."""
    user = _users.get(user_id)
    if not user:
        return False
    user.status = UserStatus.DELETED
    user.deleted_at = datetime.now(timezone.utc)

    # Invalidate all sessions
    for session in _sessions.values():
        if session.user_id == user_id:
            session.active = False

    return True


def emergency_delete_user(user_id: str) -> bool:
    """
    EMERGENCY: Immediately hard-delete all user data.
    No recovery. For victims in danger.
    """
    user = _users.get(user_id)
    if not user:
        return False

    email = user.email

    # Delete user
    del _users[user_id]
    _users_by_email.pop(email, None)

    # Delete all sessions
    to_delete = [t for t, s in _sessions.items() if s.user_id == user_id]
    for t in to_delete:
        del _sessions[t]

    # Delete all magic links
    to_delete = [t for t, l in _magic_links.items() if l.user_id == user_id]
    for t in to_delete:
        del _magic_links[t]

    logger.info(f"EMERGENCY DELETE: user {user_id} hard-deleted")
    return True


def cleanup_expired():
    """Remove expired magic links and sessions. Run periodically."""
    now = datetime.now(timezone.utc)

    # Expired magic links
    expired_links = [t for t, l in _magic_links.items() if now > l.expires_at]
    for t in expired_links:
        del _magic_links[t]

    # Expired sessions
    expired_sessions = [t for t, s in _sessions.items() if now > s.expires_at]
    for t in expired_sessions:
        del _sessions[t]

    # Hard-delete users past 7-day window
    hard_delete_cutoff = now - timedelta(days=7)
    to_hard_delete = [
        uid for uid, u in _users.items()
        if u.status == UserStatus.DELETED and u.deleted_at and u.deleted_at < hard_delete_cutoff
    ]
    for uid in to_hard_delete:
        emergency_delete_user(uid)
