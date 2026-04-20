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
    # Optional embedded screenshot as data URL ("data:image/png;base64,...") or raw base64.
    # When present, gets stored in metadata_json and embedded into legal PDFs.
    # Max ~10 MB recommended — larger images are still accepted but slow the PDF.
    screenshot_base64: Optional[str] = None


class AnalyzeTextRequest(BaseModel):
    text: str
    # Optional dynamic-prompt context — richer classification when provided.
    # Omitting these reproduces the legacy prompt byte-for-byte.
    victim_context: Optional[str] = None
    jurisdiction: str = "DE"
    user_lang: str = "de"


class IngestRequest(BaseModel):
    text: str
    author_username: str = "unknown"
    url: str = ""
    case_id: Optional[str] = None
    # Same optional context as AnalyzeTextRequest
    victim_context: Optional[str] = None
    jurisdiction: str = "DE"
    user_lang: str = "de"


class AnalyzeUrlRequest(BaseModel):
    url: str
    case_id: Optional[str] = None
    # Same optional context
    victim_context: Optional[str] = None
    jurisdiction: str = "DE"
    user_lang: str = "de"


# ── Org / multi-tenant schemas ──

class OrgCreate(BaseModel):
    slug: str
    display_name: str
    contact_email: Optional[str] = None


class OrgUpdate(BaseModel):
    display_name: Optional[str] = None
    contact_email: Optional[str] = None
    settings: Optional[dict] = None


class OrgOut(BaseModel):
    id: str
    slug: str
    display_name: str
    contact_email: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    settings: dict = {}
    member_count: int = 0
    my_role: Optional[str] = None  # only populated when user is a member

    model_config = {"from_attributes": True}


class MemberInvite(BaseModel):
    email: str
    role: str = "caseworker"  # owner / admin / caseworker / viewer


class MemberRoleUpdate(BaseModel):
    role: str


class MemberOut(BaseModel):
    user_id: str
    org_id: str
    role: str
    joined_at: Optional[datetime] = None
    email: Optional[str] = None  # denormalized for convenience
    display_name: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Bulk import ──

class BulkImportItem(BaseModel):
    """One row from a bulk import CSV."""
    text: str
    source_url: Optional[str] = None
    author_username: str = "unknown"
    platform: Optional[str] = None


class BulkImportRequest(BaseModel):
    case_id: str
    items: list[BulkImportItem]


class BulkImportResult(BaseModel):
    case_id: str
    imported: int
    failed: int
    evidence_ids: list[str]
    errors: list[str] = []


# ── GDPR Art. 20 data portability export ──

class ExportClassification(BaseModel):
    severity: str = "none"
    confidence: float = 0.0
    summary: Optional[str] = None
    summary_de: Optional[str] = None
    potential_consequences: Optional[str] = None
    potential_consequences_de: Optional[str] = None
    categories: list[str] = []  # names only; reference data not included
    laws: list[str] = []  # paragraph strings only; reference data not included
    classified_at: Optional[str] = None


class ExportEvidence(BaseModel):
    id: str
    content_type: str
    raw_content: str
    content_hash: Optional[str] = None
    hash_chain_previous: Optional[str] = None
    platform: Optional[str] = None
    source_url: Optional[str] = None
    archived_url: Optional[str] = None
    timestamp_utc: Optional[str] = None
    classification: Optional[ExportClassification] = None


class ExportCase(BaseModel):
    id: str
    title: Optional[str] = None
    status: str = "open"
    overall_severity: str = "none"
    visibility: Optional[str] = None
    org_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    evidence_items: list[ExportEvidence] = []


class ExportOrgMembership(BaseModel):
    org_id: str
    org_slug: str
    role: str
    joined_at: Optional[str] = None


class ExportUser(BaseModel):
    id: str
    email: str
    display_name: Optional[str] = None
    language: Optional[str] = None
    created_at: Optional[str] = None
    deleted_at: Optional[str] = None


class UserExport(BaseModel):
    export_version: str = "1.0"
    exported_at: str
    user: ExportUser
    cases: list[ExportCase] = []
    org_memberships: list[ExportOrgMembership] = []


class EmlBuildRequest(BaseModel):
    """Request to build a downloadable .eml file for a case."""
    recipient_email: str
    victim_name: Optional[str] = None
    victim_email: Optional[str] = None
    victim_address: Optional[str] = None
    victim_phone: Optional[str] = None
    # Which report template to use. Default is 'police' (Strafanzeige).
    # Set to 'netzdg' when sending to platforms (Meta/X/TikTok takedown).
    report_type: Optional[str] = "police"  # 'general' | 'netzdg' | 'police'
    # Optional overrides — default to the chosen report_type's template
    subject: Optional[str] = None
    body: Optional[str] = None
