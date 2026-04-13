"""
Database setup for SafeVoice — SQLAlchemy + PostgreSQL

Converts the schema.dbml design into working SQLAlchemy models.
Supports both PostgreSQL (production) and SQLite (development/testing).
"""

import os
from sqlalchemy import create_engine, Column, String, Text, DateTime, Float, Integer, Boolean, ForeignKey, Table, Enum as SAEnum
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from datetime import datetime
import uuid
import enum

# Database URL — defaults to SQLite for development
# Railway/Heroku may provide postgres:// which SQLAlchemy 2.x doesn't accept
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./safevoice.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite doesn't support ARRAY/UUID natively
is_sqlite = "sqlite" in DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if is_sqlite else {},
    echo=os.getenv("SQL_DEBUG", "").lower() == "true",
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for FastAPI — yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def gen_uuid():
    return str(uuid.uuid4())


# ── Enums ──

class SeverityLevel(str, enum.Enum):
    none = "none"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class EvidenceSource(str, enum.Enum):
    user_input = "user_input"
    ai_populated = "ai_populated"
    system_generated = "system_generated"


# ── Junction Tables ──

classification_categories = Table(
    "classification_categories", Base.metadata,
    Column("classification_id", String, ForeignKey("classifications.id"), primary_key=True),
    Column("category_id", String, ForeignKey("categories.id"), primary_key=True),
)

classification_laws = Table(
    "classification_laws", Base.metadata,
    Column("classification_id", String, ForeignKey("classifications.id"), primary_key=True),
    Column("law_id", String, ForeignKey("laws.id"), primary_key=True),
)


# ── Models ──

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False)
    display_name = Column(String)
    language = Column(String, default="de")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)  # GDPR soft delete

    # Relationships
    cases = relationship("Case", back_populates="user", foreign_keys="Case.user_id")
    org_memberships = relationship(
        "OrgMember",
        back_populates="user",
        foreign_keys="OrgMember.user_id",  # disambiguate from invited_by
    )


class Org(Base):
    """An organization (NGO, victim support service, etc.) that uses SafeVoice."""
    __tablename__ = "orgs"

    id = Column(String, primary_key=True, default=gen_uuid)
    slug = Column(String, unique=True, nullable=False)  # URL-safe: "hateaid", "weisser-ring"
    display_name = Column(String, nullable=False)
    contact_email = Column(String)
    # Org-level settings (PDF letterhead URL, default language, branding color, etc.)
    settings_json = Column(Text, default="{}")
    status = Column(String, default="active")  # active / suspended / deleted
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    members = relationship("OrgMember", back_populates="org", cascade="all, delete-orphan")
    cases = relationship("Case", back_populates="org")


class OrgMember(Base):
    """Many-to-many: users belong to orgs with a role."""
    __tablename__ = "org_members"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    org_id = Column(String, ForeignKey("orgs.id"), primary_key=True)
    # owner > admin > caseworker > viewer
    role = Column(String, nullable=False, default="caseworker")
    joined_at = Column(DateTime, default=datetime.utcnow)
    invited_by = Column(String, ForeignKey("users.id"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="org_memberships", foreign_keys=[user_id])
    org = relationship("Org", back_populates="members")


class Case(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    org_id = Column(String, ForeignKey("orgs.id"), nullable=True)  # Multi-tenant: optional org ownership
    assigned_to = Column(String, ForeignKey("users.id"), nullable=True)  # Which caseworker owns this
    visibility = Column(String, default="private")  # private (creator only) / org (all org members)

    title = Column(String)  # AI_POPULATED initially, user-editable
    summary = Column(Text)  # AI_POPULATED
    summary_de = Column(Text)  # AI_POPULATED
    status = Column(String, default="open")  # open / in_progress / closed
    overall_severity = Column(String, default="none")  # AI_POPULATED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="cases", foreign_keys=[user_id])
    assignee = relationship("User", foreign_keys=[assigned_to])
    org = relationship("Org", back_populates="cases")
    evidence_items = relationship("EvidenceItem", back_populates="case")


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id = Column(String, primary_key=True, default=gen_uuid)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    content_type = Column(String, nullable=False)  # USER INPUT: text/url/screenshot
    raw_content = Column(Text, nullable=False)  # USER INPUT: original text/URL
    extracted_text = Column(Text)  # AI_POPULATED: OCR result or scraped text
    content_hash = Column(String)  # system_generated: SHA-256
    hash_chain_previous = Column(String)  # system_generated: previous hash in chain
    platform = Column(String)  # AI_POPULATED: detected platform (instagram/x/etc)
    source_url = Column(String)  # USER INPUT: original URL if applicable
    archived_url = Column(String)  # system_generated: archive.org URL
    timestamp_utc = Column(DateTime, default=datetime.utcnow)  # system_generated
    metadata_json = Column(Text)  # system_generated: additional metadata as JSON

    # Relationships
    case = relationship("Case", back_populates="evidence_items")
    classification = relationship("Classification", back_populates="evidence_item", uselist=False)


class Classification(Base):
    __tablename__ = "classifications"

    id = Column(String, primary_key=True, default=gen_uuid)
    evidence_item_id = Column(String, ForeignKey("evidence_items.id"), nullable=False, unique=True)
    severity = Column(String, default="none")  # AI_POPULATED
    confidence = Column(Float, default=0.0)  # AI_POPULATED: 0.0-1.0
    classifier_tier = Column(Integer)  # system_generated: 1=LLM, 2=transformer, 3=regex
    summary = Column(Text)  # AI_POPULATED
    summary_de = Column(Text)  # AI_POPULATED
    potential_consequences = Column(Text)  # AI_POPULATED
    potential_consequences_de = Column(Text)  # AI_POPULATED
    recommended_actions = Column(Text)  # AI_POPULATED
    recommended_actions_de = Column(Text)  # AI_POPULATED
    classified_at = Column(DateTime, default=datetime.utcnow)  # system_generated

    # Relationships
    evidence_item = relationship("EvidenceItem", back_populates="classification")
    categories = relationship("Category", secondary=classification_categories)
    laws = relationship("Law", secondary=classification_laws)


class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, unique=True, nullable=False)
    name_de = Column(String)
    description = Column(Text)
    description_de = Column(Text)


class Law(Base):
    __tablename__ = "laws"

    id = Column(String, primary_key=True, default=gen_uuid)
    code = Column(String, nullable=False)  # e.g. "stgb"
    section = Column(String, nullable=False)  # e.g. "185"
    name = Column(String)  # e.g. "Beleidigung"
    name_de = Column(String)  # e.g. "Insult"
    full_text = Column(Text)
    full_text_de = Column(Text)
    max_penalty = Column(String)
    jurisdiction = Column(String, default="DE")


# ── Create all tables ──

def init_db():
    """Create all tables. Call once on startup."""
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized: {DATABASE_URL}")


def seed_categories_and_laws():
    """Seed reference data — categories and German law paragraphs."""
    db = SessionLocal()

    # Categories
    categories = [
        ("harassment", "Harassment", "Belästigung"),
        ("threat", "Threat", "Bedrohung"),
        ("hate_speech", "Hate Speech", "Hassrede"),
        ("defamation", "Defamation", "Üble Nachrede"),
        ("slander", "Slander", "Verleumdung"),
        ("fraud", "Fraud", "Betrug"),
        ("identity_theft", "Identity Theft", "Identitätsdiebstahl"),
        ("cyberstalking", "Cyberstalking / Stalking", "Cyberstalking / Nachstellung"),
        ("sexual_harassment", "Sexual Harassment", "Sexuelle Belästigung"),
        ("volksverhetzung", "Incitement to Hatred", "Volksverhetzung"),
        ("intimate_images", "Non-consensual Intimate Images / Deepfakes", "Nicht einvernehmliche intime Bildaufnahmen / Deepfakes"),
        ("body_shaming", "Body Shaming", "Body-Shaming"),
        ("misogyny", "Misogyny", "Misogynie"),
        ("scam", "Scam / Fraud", "Betrug / Scam"),
        ("phishing", "Phishing", "Phishing"),
    ]

    for id_name, name, name_de in categories:
        existing = db.query(Category).filter_by(id=id_name).first()
        if existing:
            existing.name = name
            existing.name_de = name_de
        else:
            db.add(Category(id=id_name, name=name, name_de=name_de))

    # German laws
    laws = [
        ("stgb-130", "stgb", "130", "Incitement to Hatred", "Volksverhetzung", "Up to 5 years"),
        ("stgb-185", "stgb", "185", "Insult", "Beleidigung", "Up to 1 year or fine"),
        ("stgb-186", "stgb", "186", "Defamation", "Üble Nachrede", "Up to 1 year or fine"),
        ("stgb-187", "stgb", "187", "Slander", "Verleumdung", "Up to 5 years"),
        ("stgb-201a", "stgb", "201a", "Intimate Image Violation", "Verletzung des höchstpersönlichen Lebensbereichs durch Bildaufnahmen", "Up to 2 years"),
        ("stgb-238", "stgb", "238", "Stalking", "Nachstellung", "Up to 3 years (up to 5 in serious cases)"),
        ("stgb-241", "stgb", "241", "Threat", "Bedrohung", "Up to 1 year or fine"),
        ("stgb-126a", "stgb", "126a", "Criminal Threat", "Schwere Drohung", "Up to 3 years"),
        ("stgb-263", "stgb", "263", "Fraud", "Betrug", "Up to 5 years or fine"),
        ("stgb-269", "stgb", "269", "Data Falsification", "Urkundenfälschung", "Up to 5 years"),
        ("netzdg-3", "netzdg", "3", "NetzDG Platform Obligations", "NetzDG Plattformpflichten", "Up to 50M fine"),
    ]

    for id_name, code, section, name, name_de, penalty in laws:
        existing = db.query(Law).filter_by(id=id_name).first()
        if existing:
            existing.code = code
            existing.section = section
            existing.name = name
            existing.name_de = name_de
            existing.max_penalty = penalty
        else:
            db.add(Law(id=id_name, code=code, section=section, name=name, name_de=name_de, max_penalty=penalty))

    db.commit()
    db.close()
    print("Seeded categories and laws.")


if __name__ == "__main__":
    init_db()
    seed_categories_and_laws()
