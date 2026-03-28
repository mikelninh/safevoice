"""
Tests for Phase 4 features:
- AI legal analysis (4.5)
- Serial offender database (4.6)
- Platform NetzDG submission (4.7)
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.legal_ai import _fallback_analysis
from app.services.offender_db import (
    check_offender, index_case, get_serial_offenders, get_offender_stats,
    _hash_username,
)
from app.services.platform_submit import generate_platform_submission
from app.data.mock_data import get_case_by_id, get_all_cases


@pytest.fixture
def client():
    return TestClient(app)


# === AI Legal Analysis (4.5) ===

class TestLegalAnalysis:
    def test_fallback_analysis_returns_structure(self):
        case = get_case_by_id("case-001")
        result = _fallback_analysis(case)
        assert "legal_assessment_de" in result
        assert "legal_assessment_en" in result
        assert "recommended_actions" in result
        assert "risk_assessment" in result
        assert "disclaimer_de" in result

    def test_fallback_analysis_critical_case(self):
        case = get_case_by_id("case-002")  # death threat — CRITICAL
        result = _fallback_analysis(case)
        assert result["risk_assessment"]["escalation_risk"] == "high"
        assert any(a["priority"] == "immediate" for a in result["recommended_actions"])

    def test_fallback_analysis_scam_case(self):
        case = get_case_by_id("case-004")  # scam
        result = _fallback_analysis(case)
        assert "§ 263 StGB" in result["legal_assessment_de"]

    def test_legal_endpoint(self, client):
        resp = client.get("/legal/case-001")
        assert resp.status_code == 200
        data = resp.json()
        assert "analysis" in data
        assert "ai_available" in data

    def test_legal_endpoint_404(self, client):
        resp = client.get("/legal/nonexistent")
        assert resp.status_code == 404


# === Serial Offender Database (4.6) ===

class TestOffenderDB:
    def test_hash_username_deterministic(self):
        assert _hash_username("user1") == _hash_username("user1")

    def test_hash_username_case_insensitive(self):
        assert _hash_username("User1") == _hash_username("user1")

    def test_check_unknown_offender(self):
        result = check_offender("completely_unknown_user_xyz")
        assert result.is_known is False
        assert result.risk_level == "low"

    def test_check_known_offender(self):
        # Mock data has "beef_truth99" in case-001
        result = check_offender("beef_truth99")
        assert result.is_known is True
        assert result.prior_evidence >= 1

    def test_offender_stats(self):
        stats = get_offender_stats()
        assert "total_tracked" in stats
        assert stats["total_tracked"] > 0

    def test_offender_check_endpoint(self, client):
        resp = client.get("/offenders/check/beef_truth99")
        assert resp.status_code == 200
        data = resp.json()
        assert data["match"]["is_known"] is True

    def test_offender_stats_endpoint(self, client):
        resp = client.get("/offenders/stats")
        assert resp.status_code == 200
        assert "total_tracked" in resp.json()

    def test_serial_offenders_endpoint(self, client):
        resp = client.get("/offenders/serial")
        assert resp.status_code == 200
        assert "serial_offenders" in resp.json()


# === Platform NetzDG Submission (4.7) ===

class TestPlatformSubmission:
    def test_instagram_submission(self):
        case = get_case_by_id("case-001")
        result = generate_platform_submission(case, "instagram", "de")
        assert "Meta" in result["platform"]
        assert result["submission_url"] is not None
        assert "NetzDG" in result["submission_type"]
        assert len(result["fields"]["reported_content_urls"]) > 0

    def test_x_submission(self):
        case = get_case_by_id("case-001")
        result = generate_platform_submission(case, "x", "en")
        assert "X Corp" in result["platform"]
        assert "twitter.com" in result["submission_url"]

    def test_tiktok_submission(self):
        case = get_case_by_id("case-001")
        result = generate_platform_submission(case, "tiktok", "de")
        assert "TikTok" in result["platform"]

    def test_generic_submission(self):
        case = get_case_by_id("case-001")
        result = generate_platform_submission(case, "unknown_platform", "de")
        assert result["submission_url"] is None

    def test_urgent_deadline_for_critical(self):
        case = get_case_by_id("case-002")  # CRITICAL severity
        result = generate_platform_submission(case, "instagram", "de")
        assert "24" in result["deadline"]
        assert result["is_urgent"] is True

    def test_submission_endpoint(self, client):
        resp = client.get("/submit/case-001/instagram?lang=de")
        assert resp.status_code == 200
        data = resp.json()
        assert "fields" in data
        assert "instructions_de" in data

    def test_submission_endpoint_404(self, client):
        resp = client.get("/submit/nonexistent/instagram")
        assert resp.status_code == 404
