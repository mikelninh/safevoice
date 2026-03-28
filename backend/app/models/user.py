"""
User account models.
Magic link auth — no passwords.
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum


class UserStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"  # soft-deleted, pending hard delete


class User(BaseModel):
    id: str
    email: str
    display_name: str | None = None
    lang: str = "de"
    created_at: datetime
    last_login: datetime | None = None
    status: UserStatus = UserStatus.ACTIVE
    deleted_at: datetime | None = None  # when soft-delete was triggered


class MagicLink(BaseModel):
    id: str
    user_id: str
    token: str  # URL-safe random token
    email: str
    created_at: datetime
    expires_at: datetime
    used: bool = False


class Session(BaseModel):
    id: str
    user_id: str
    token: str
    created_at: datetime
    expires_at: datetime
    active: bool = True


class UserCase(BaseModel):
    """Links a user to their cases (ownership)."""
    user_id: str
    case_id: str
    created_at: datetime
    shared_with: list[str] = []  # org IDs the user has shared this case with
