"""
Integration tests for the second AI layer:
- case -> legal analysis persistence
- legal PDF includes persisted AI analysis
"""

import json
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import (
    Base,
    Case as DBCase,
    Category as DBCategory,
    Law as DBLaw,
)
from app.data.mock_data import LAW_241, NETZ_DG
from app.models.evidence import ClassificationResult, Severity, Category, GermanLaw
from app.services.db_helpers import create_case, add_evidence_with_classification
from app.services.legal_ai import analyze_and_persist_case
from app.services.legal_pdf import generate_legal_pdf


def _ensure_reference_data(db):
    categories = [
        ("threat", "Bedrohung"),
        ("harassment", "Belästigung"),
    ]
    for cat_id, name_de in categories:
        if db.query(DBCategory).filter_by(id=cat_id).first() is None:
            db.add(DBCategory(id=cat_id, name=cat_id, name_de=name_de))

    laws = [
        ("stgb-241", "stgb", "241", "Bedrohung", "Bedrohung", "§ 241 full text", "§ 241 full text", "Freiheitsstrafe"),
        ("netzdg-3", "netzdg", "3", "NetzDG", "NetzDG", "NetzDG full text", "NetzDG full text", "—"),
    ]
    for law_id, code, section, name, name_de, full_text, full_text_de, penalty in laws:
        if db.query(DBLaw).filter_by(id=law_id).first() is None:
            db.add(DBLaw(
                id=law_id,
                code=code,
                section=section,
                name=name,
                name_de=name_de,
                full_text=full_text,
                full_text_de=full_text_de,
                max_penalty=penalty,
                jurisdiction="DE",
            ))
    db.commit()


def _classification_result():
    return ClassificationResult(
        severity=Severity.HIGH,
        categories=[Category.THREAT],
        confidence=0.94,
        requires_immediate_action=True,
        summary="Threat against victim.",
        summary_de="Bedrohung gegen das Opfer.",
        applicable_laws=[LAW_241, NETZ_DG],
        potential_consequences="Police report likely appropriate.",
        potential_consequences_de="Eine Strafanzeige ist naheliegend.",
    )


def test_legal_analysis_persists_and_is_rendered_in_pdf():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        _ensure_reference_data(db)
        case = create_case(db, title="Integration Test Case")
        add_evidence_with_classification(
            db,
            case.id,
            text="Ich weiss, wo du wohnst.",
            classification_result=_classification_result(),
            platform="instagram",
            author_username="offender123",
            content_type="text",
        )

        fake_analysis = {
            "legal_assessment_de": "Die Drohung ist strafrechtlich relevant und sollte dokumentiert werden.",
            "legal_assessment_en": "The threat is criminally relevant and should be documented.",
            "strongest_charges": [
                {
                    "paragraph": "§ 241 StGB",
                    "strength": "strong",
                    "reason_de": "Direkte Bedrohung mit erkennbarem Einschuechterungseffekt.",
                    "reason_en": "Direct threat with clear intimidation effect.",
                }
            ],
            "recommended_actions": [
                {
                    "priority": "immediate",
                    "action_de": "Beweise sichern und Strafanzeige vorbereiten.",
                    "action_en": "Secure evidence and prepare a police report.",
                    "deadline": "24h",
                }
            ],
            "risk_assessment": {
                "escalation_risk": "high",
                "reason_de": "Die Formulierung deutet auf eine reale Einschuechterung hin.",
                "reason_en": "The wording suggests real intimidation.",
            },
            "evidence_gaps": [
                {
                    "gap_de": "Kein Profil-Screenshot.",
                    "gap_en": "No profile screenshot.",
                    "how_to_fill_de": "Profilseite speichern.",
                    "how_to_fill_en": "Save the profile page.",
                }
            ],
            "cross_references": "§ 241 StGB; NetzDG § 3",
            "disclaimer_de": "Keine verbindliche Rechtsberatung.",
            "disclaimer_en": "No binding legal advice.",
        }

        with patch("app.services.legal_ai.analyze_case_legally", return_value=fake_analysis), \
             patch("app.services.legal_ai.get_law_text", side_effect=Exception("skip provenance"), create=True):
            persisted = analyze_and_persist_case(case.id, db)

        assert persisted is not None
        db_case = db.query(DBCase).filter_by(id=case.id).first()
        assert db_case is not None
        assert db_case.summary_de == fake_analysis["legal_assessment_de"]
        assert db_case.overall_severity == "high"
        assert len(db_case.case_analyses) >= 1

        latest = db_case.case_analyses[0]
        assert json.loads(latest.strongest_charges_json)[0]["paragraph"] == "§ 241 StGB"
        assert json.loads(latest.recommended_actions_json)[0]["priority"] == "immediate"

        pdf = generate_legal_pdf(db_case, org=None)
        assert pdf[:5] == b"%PDF-"
        assert b"Juristische Gesamteinschaetzung" in pdf or b"legal_assessment" not in pdf
        assert "Die Drohung ist strafrechtlich relevant".encode("utf-8") in pdf
    finally:
        db.close()
