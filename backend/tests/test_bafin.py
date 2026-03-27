"""
Tests for BaFin scam report generation.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.bafin_report import generate_bafin_report
from app.data.mock_data import get_case_by_id


@pytest.fixture
def client():
    return TestClient(app)


class TestBafinReportGenerator:
    def test_generates_for_scam_case(self):
        case = get_case_by_id("case-004")  # Investment scam case
        report = generate_bafin_report(case, "de")
        assert report is not None
        assert report["report_type"] == "bafin"
        assert "Betrug" in report["scam_type"] or "Investition" in report["scam_type"]

    def test_returns_none_for_non_scam(self):
        case = get_case_by_id("case-003")  # Body shaming case
        report = generate_bafin_report(case, "de")
        assert report is None

    def test_extracts_perpetrator_accounts(self):
        case = get_case_by_id("case-004")
        report = generate_bafin_report(case, "de")
        assert "crypto_advisor_thomas_w" in report["perpetrator_accounts"]

    def test_includes_body_text(self):
        case = get_case_by_id("case-004")
        report = generate_bafin_report(case, "de")
        assert "VERDACHTSMELDUNG" in report["body"]

    def test_english_version(self):
        case = get_case_by_id("case-004")
        report = generate_bafin_report(case, "en")
        assert "SUSPICIOUS ACTIVITY REPORT" in report["body"]

    def test_includes_submit_url(self):
        case = get_case_by_id("case-004")
        report = generate_bafin_report(case, "de")
        assert "bafin.de" in report["submit_url"]


class TestBafinEndpoint:
    def test_bafin_endpoint_scam_case(self, client):
        resp = client.get("/reports/case-004/bafin?lang=de")
        assert resp.status_code == 200
        data = resp.json()
        assert data["report_type"] == "bafin"

    def test_bafin_endpoint_non_scam_returns_422(self, client):
        resp = client.get("/reports/case-003/bafin?lang=de")
        assert resp.status_code == 422

    def test_bafin_endpoint_404(self, client):
        resp = client.get("/reports/nonexistent/bafin")
        assert resp.status_code == 404
