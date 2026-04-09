"""
API request/response schemas for the database-backed endpoints.
Separate from SQLAlchemy models (database.py) and legacy Pydantic models (models/evidence.py).
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# ── Response schemas ──

class CategoryOut(BaseModel):
    id: str
    name: str
    name_de: Optional[str] = None

    model_config = {"from_attributes": True}


class LawOut(BaseModel):
    id: str
    code: str
    section: str
    name: Optional[str] = None
    name_de: Optional[str] = None
    max_penalty: Optional[str] = None

    model_config = {"from_attributes": True}


class ClassificationOut(BaseModel):
    id: str
    severity: str
    confidence: float
    classifier_tier: Optional[int] = None
    summary: Optional[str] = None
    summary_de: Optional[str] = None
    potential_consequences: Optional[str] = None
    potential_consequences_de: Optional[str] = None
    recommended_actions: Optional[str] = None
    recommended_actions_de: Optional[str] = None
    categories: list[CategoryOut] = []
    laws: list[LawOut] = []
    classified_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EvidenceOut(BaseModel):
    id: str
    content_type: str
    raw_content: str
    extracted_text: Optional[str] = None
    content_hash: Optional[str] = None
    hash_chain_previous: Optional[str] = None
    platform: Optional[str] = None
    source_url: Optional[str] = None
    archived_url: Optional[str] = None
    timestamp_utc: Optional[datetime] = None
    classification: Optional[ClassificationOut] = None

    model_config = {"from_attributes": True}


class CaseOut(BaseModel):
    id: str
    title: Optional[str] = None
    summary: Optional[str] = None
    summary_de: Optional[str] = None
    status: str = "open"
    overall_severity: str = "none"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    evidence_count: int = 0
    evidence_items: list[EvidenceOut] = []

    model_config = {"from_attributes": True}


class CaseListOut(BaseModel):
    """Lighter schema for listing cases (no nested evidence)."""
    id: str
    title: Optional[str] = None
    status: str = "open"
    overall_severity: str = "none"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    evidence_count: int = 0

    model_config = {"from_attributes": True}


# ── Request schemas ──

class CaseCreate(BaseModel):
    title: Optional[str] = None
    victim_context: Optional[str] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    victim_context: Optional[str] = None


class EvidenceCreate(BaseModel):
    """Add evidence to a case — text, URL, or pre-extracted content."""
    content_type: str = "text"  # text | url | screenshot
    text: str
    source_url: Optional[str] = None
    author_username: str = "unknown"
    platform: Optional[str] = None


class AnalyzeTextRequest(BaseModel):
    text: str


class IngestRequest(BaseModel):
    text: str
    author_username: str = "unknown"
    url: str = ""
    case_id: Optional[str] = None


class AnalyzeUrlRequest(BaseModel):
    url: str
    case_id: Optional[str] = None
