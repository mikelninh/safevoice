from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Category(str, Enum):
    HARASSMENT = "harassment"
    THREAT = "threat"
    DEATH_THREAT = "death_threat"
    DEFAMATION = "defamation"
    MISOGYNY = "misogyny"
    BODY_SHAMING = "body_shaming"
    COORDINATED_ATTACK = "coordinated_attack"
    FALSE_FACTS = "false_facts"
    SEXUAL_HARASSMENT = "sexual_harassment"
    SCAM = "scam"
    PHISHING = "phishing"
    INVESTMENT_FRAUD = "investment_fraud"
    ROMANCE_SCAM = "romance_scam"
    IMPERSONATION = "impersonation"


class GermanLaw(BaseModel):
    paragraph: str
    title: str
    title_de: str
    description: str
    description_de: str
    max_penalty: str
    applies_because: str
    applies_because_de: str


class ClassificationResult(BaseModel):
    severity: Severity
    categories: list[Category]
    confidence: float = Field(ge=0.0, le=1.0)
    requires_immediate_action: bool
    summary: str
    summary_de: str
    applicable_laws: list[GermanLaw]
    potential_consequences: str
    potential_consequences_de: str


class EvidenceItem(BaseModel):
    id: str
    url: str
    platform: str = "instagram"
    captured_at: datetime
    author_username: str
    author_display_name: Optional[str] = None
    content_text: str
    content_type: str = "comment"
    archived_url: Optional[str] = None
    screenshot_path: Optional[str] = None
    content_hash: str
    classification: Optional[ClassificationResult] = None


class PatternFlag(BaseModel):
    type: str
    description: str
    description_de: str
    evidence_count: int
    severity: Severity


class Case(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    victim_context: Optional[str] = None
    evidence_items: list[EvidenceItem] = []
    pattern_flags: list[PatternFlag] = []
    overall_severity: Severity = Severity.LOW
    status: str = "open"
    title: str = "New Case"
