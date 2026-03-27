"""
Tests for PDF export.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.pdf_generator import generate_pdf
from app.data.mock_data import get_case_by_id


@pytest.fixture
def client():
    return TestClient(app)


class TestPdfGenerator:
    def test_generates_bytes(self):
        case = get_case_by_id("case-001")
        pdf = generate_pdf(case, "general", "de")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_pdf_header(self):
        """Valid PDF starts with %PDF."""
        case = get_case_by_id("case-001")
        pdf = generate_pdf(case, "general", "de")
        assert pdf[:5] == b"%PDF-"

    def test_all_report_types(self):
        case = get_case_by_id("case-001")
        for rt in ("general", "netzdg", "police"):
            pdf = generate_pdf(case, rt, "de")
            assert pdf[:5] == b"%PDF-"

    def test_both_languages(self):
        case = get_case_by_id("case-002")
        pdf_de = generate_pdf(case, "general", "de")
        pdf_en = generate_pdf(case, "general", "en")
        assert pdf_de[:5] == b"%PDF-"
        assert pdf_en[:5] == b"%PDF-"
        # Different languages should produce different PDFs
        assert pdf_de != pdf_en

    def test_all_cases(self):
        for case_id in ("case-001", "case-002", "case-003", "case-004"):
            case = get_case_by_id(case_id)
            pdf = generate_pdf(case, "general", "de")
            assert pdf[:5] == b"%PDF-"


class TestPdfEndpoint:
    def test_pdf_endpoint_returns_pdf(self, client):
        resp = client.get("/reports/case-001/pdf?report_type=general&lang=de")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:5] == b"%PDF-"

    def test_pdf_endpoint_netzdg(self, client):
        resp = client.get("/reports/case-002/pdf?report_type=netzdg&lang=de")
        assert resp.status_code == 200
        assert "attachment" in resp.headers["content-disposition"]

    def test_pdf_endpoint_police_en(self, client):
        resp = client.get("/reports/case-003/pdf?report_type=police&lang=en")
        assert resp.status_code == 200
        assert resp.content[:5] == b"%PDF-"

    def test_pdf_endpoint_404(self, client):
        resp = client.get("/reports/nonexistent/pdf")
        assert resp.status_code == 404
