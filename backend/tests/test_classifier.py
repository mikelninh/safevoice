"""
Tests for the 3-tier classifier system.
Tests regex (always available) and the unified classify() fallback chain.
"""

import pytest
from app.services.classifier import classify, classify_regex
from app.models.evidence import Severity, Category


# === REGEX CLASSIFIER TESTS (Tier 3 — always works) ===

class TestRegexClassifier:
    """Regex classifier must detect all key categories."""

    def test_death_threat_en(self):
        result = classify_regex("I will kill you and your family")
        assert Severity.CRITICAL == result.severity
        assert Category.DEATH_THREAT in result.categories
        assert result.requires_immediate_action is True

    def test_death_threat_de(self):
        result = classify_regex("Ich werde dich umbringen")
        assert Severity.CRITICAL == result.severity
        assert Category.DEATH_THREAT in result.categories

    def test_threat_en(self):
        result = classify_regex("You'll regret this, watch yourself")
        assert result.severity in (Severity.HIGH, Severity.CRITICAL)
        assert Category.THREAT in result.categories

    def test_misogyny_en(self):
        result = classify_regex("Women should stay in the kitchen and shut up")
        assert Category.MISOGYNY in result.categories

    def test_misogyny_de(self):
        result = classify_regex("Frauen gehören in die Küche, du Schlampe")
        assert Category.MISOGYNY in result.categories

    def test_sexual_harassment(self):
        result = classify_regex("Send me nudes or I'll find you")
        assert Category.SEXUAL_HARASSMENT in result.categories
        assert result.requires_immediate_action is True

    def test_harassment_en(self):
        result = classify_regex("You're such a stupid idiot, nobody cares about you")
        assert Category.HARASSMENT in result.categories

    def test_harassment_de(self):
        result = classify_regex("Halt die Klappe du Vollidiot")
        assert Category.HARASSMENT in result.categories

    def test_scam_crypto(self):
        result = classify_regex("Send bitcoin to my wallet address for guaranteed return of 30% monthly")
        assert Category.SCAM in result.categories
        assert Severity.CRITICAL == result.severity

    def test_phishing(self):
        result = classify_regex("Your account suspended, click here to verify your account")
        assert Category.PHISHING in result.categories

    def test_romance_scam(self):
        result = classify_regex("I love you baby, please send money, I am stranded and need help")
        assert Category.ROMANCE_SCAM in result.categories

    def test_impersonation(self):
        result = classify_regex("I am from Instagram support team, urgent: your account will be deleted")
        assert Category.IMPERSONATION in result.categories

    def test_benign_defaults_to_low(self):
        result = classify_regex("Nice photo! Love the colors.")
        assert result.severity == Severity.LOW

    def test_netzDG_always_included(self):
        result = classify_regex("any text at all")
        law_paragraphs = [l.paragraph for l in result.applicable_laws]
        assert "NetzDG § 3" in law_paragraphs

    def test_bilingual_summaries(self):
        result = classify_regex("I will kill you")
        assert result.summary  # English
        assert result.summary_de  # German
        assert result.potential_consequences
        assert result.potential_consequences_de

    def test_confidence_in_range(self):
        result = classify_regex("You idiot, die already")
        assert 0.0 <= result.confidence <= 1.0


# === TURKISH CLASSIFIER TESTS ===

class TestTurkishClassifier:
    """Regex classifier must detect Turkish harassment."""

    def test_death_threat_tr(self):
        result = classify_regex("Seni öldüreceğim, dikkat et")
        assert Category.DEATH_THREAT in result.categories
        assert result.severity == Severity.CRITICAL

    def test_threat_tr(self):
        result = classify_regex("Pişman olursun, nerede olduğunu biliyorum")
        assert Category.THREAT in result.categories

    def test_misogyny_tr(self):
        result = classify_regex("Kadınlar sussun, sen bir kaltak")
        assert Category.MISOGYNY in result.categories

    def test_harassment_tr(self):
        result = classify_regex("Sen bir aptal gerizekalı, kapa çeneni")
        assert Category.HARASSMENT in result.categories

    def test_body_shaming_tr(self):
        result = classify_regex("Sen çok şişko ve çirkin bir insansın")
        assert Category.BODY_SHAMING in result.categories


# === ARABIC CLASSIFIER TESTS ===

class TestArabicClassifier:
    """Regex classifier must detect Arabic harassment."""

    def test_death_threat_ar(self):
        result = classify_regex("سأقتلك يا كلب")
        assert Category.DEATH_THREAT in result.categories
        assert result.severity == Severity.CRITICAL

    def test_threat_ar(self):
        result = classify_regex("ستندم على كلامك، اعرف وين تسكن")
        assert Category.THREAT in result.categories

    def test_misogyny_ar(self):
        result = classify_regex("اسكتي يا شرموطة، المرأة مكانها البيت")
        assert Category.MISOGYNY in result.categories

    def test_harassment_ar(self):
        result = classify_regex("انت غبي وحمار، اخرس")
        assert Category.HARASSMENT in result.categories

    def test_body_shaming_ar(self):
        result = classify_regex("انتي سمينة وقبيحة")
        assert Category.BODY_SHAMING in result.categories


# === UNIFIED CLASSIFY TESTS (fallback chain) ===

class TestUnifiedClassify:
    """The unified classify() should always return a result regardless of tier availability."""

    def test_always_returns_result(self):
        """classify() must never return None — regex fallback guarantees it."""
        result = classify("Some random text")
        assert result is not None
        assert result.severity is not None
        assert len(result.categories) > 0

    def test_death_threat_detected(self):
        result = classify("I'm going to kill you and your whole family")
        assert result.severity in (Severity.HIGH, Severity.CRITICAL)
        assert any(c in result.categories for c in [Category.THREAT, Category.DEATH_THREAT])

    def test_scam_detected(self):
        result = classify("Guaranteed return of 40% monthly, send bitcoin to wallet address now, act now")
        assert Category.SCAM in result.categories or Category.INVESTMENT_FRAUD in result.categories

    def test_german_content_works(self):
        result = classify("Frauen wie du gehören bestraft. Halt die Klappe, Schlampe.")
        assert result.severity in (Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL)
        assert any(c in result.categories for c in [Category.MISOGYNY, Category.HARASSMENT])


# === INTEGRATION: API endpoint ===

class TestAnalyzeEndpoint:
    """Test the /analyze/text endpoint returns valid classification."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    def test_analyze_text_endpoint(self, client):
        resp = client.post("/analyze/text", json={"text": "You're a worthless idiot"})
        assert resp.status_code == 200
        data = resp.json()
        assert "severity" in data
        assert "categories" in data
        assert "applicable_laws" in data

    def test_analyze_ingest_endpoint(self, client):
        resp = client.post("/analyze/ingest", json={
            "text": "I will kill you",
            "author_username": "threat_user",
            "url": "https://instagram.com/p/test"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "evidence" in data
        assert data["evidence"]["classification"]["severity"] in ["high", "critical"]

    def test_health_shows_classifier_tier(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "classifier_tier" in data
        assert data["classifier_tier"] in ("claude_api", "transformer", "regex")
