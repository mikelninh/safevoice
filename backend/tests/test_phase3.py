"""
Tests for Phase 3 features:
- Partner API (3.3)
- Dashboard (3.4)
- Court export (3.6)
- Institutional accounts (3.7)
- Case assignment (3.2)
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.partner_store import (
    create_organization, get_org_by_api_key, add_member,
    assign_case, get_org_assignments, seed_demo_org,
    list_organizations,
)
from app.models.partner import OrgType, OrgRole
from app.services.court_export import generate_court_package
from app.data.mock_data import get_case_by_id
import zipfile
import io
import json


@pytest.fixture
def client():
    return TestClient(app)


# === Partner API (3.3) ===

class TestPartnerAPI:
    def test_create_organization(self, client):
        resp = client.post("/partners/organizations", json={
            "name": "Test Police Unit",
            "org_type": "police",
            "contact_email": "test@polizei.de",
            "bundesland": "Berlin",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "api_key" in data
        assert data["api_key"].startswith("sv_")
        assert data["organization"]["name"] == "Test Police Unit"

    def test_list_organizations(self, client):
        resp = client.get("/partners/organizations")
        assert resp.status_code == 200
        orgs = resp.json()
        assert len(orgs) >= 2  # demo orgs seeded

    def test_submit_case_requires_api_key(self, client):
        resp = client.post("/partners/cases/submit", json={
            "text": "test harassment",
        })
        assert resp.status_code == 401

    def test_submit_case_with_api_key(self, client):
        # Get an API key from demo org
        orgs = list_organizations()
        api_key = orgs[0].api_key

        resp = client.post(
            "/partners/cases/submit",
            json={"text": "I will kill you", "platform": "instagram", "author_username": "threat_user"},
            headers={"X-API-Key": api_key},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "evidence" in data
        assert "classification" in data
        assert data["submitted_by"] == orgs[0].name

    def test_invalid_api_key_rejected(self, client):
        resp = client.post(
            "/partners/cases/submit",
            json={"text": "test"},
            headers={"X-API-Key": "sv_invalid_key"},
        )
        assert resp.status_code == 403

    def test_add_and_list_members(self, client):
        orgs = list_organizations()
        api_key = orgs[0].api_key

        resp = client.post(
            "/partners/members",
            json={"email": "new@test.de", "display_name": "New Member", "role": "analyst"},
            headers={"X-API-Key": api_key},
        )
        assert resp.status_code == 200

        resp = client.get("/partners/members", headers={"X-API-Key": api_key})
        assert resp.status_code == 200
        members = resp.json()
        assert any(m["email"] == "new@test.de" for m in members)


# === Case Assignment (3.2) ===

class TestCaseAssignment:
    def test_assign_case(self, client):
        orgs = list_organizations()
        api_key = orgs[0].api_key

        resp = client.post(
            "/partners/cases/assign",
            json={
                "case_id": "case-001",
                "jurisdiction": "Berlin",
                "unit_type": "cybercrime",
            },
            headers={"X-API-Key": api_key},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["case_id"] == "case-001"
        assert data["jurisdiction"] == "Berlin"
        assert data["unit_type"] == "cybercrime"

    def test_list_assigned_cases(self, client):
        orgs = list_organizations()
        api_key = orgs[0].api_key

        # First assign a case
        client.post(
            "/partners/cases/assign",
            json={"case_id": "case-002"},
            headers={"X-API-Key": api_key},
        )

        resp = client.get("/partners/cases", headers={"X-API-Key": api_key})
        assert resp.status_code == 200
        cases = resp.json()
        assert len(cases) >= 1

    def test_update_assignment_status(self, client):
        orgs = list_organizations()
        api_key = orgs[0].api_key

        # Assign
        assign_resp = client.post(
            "/partners/cases/assign",
            json={"case_id": "case-003"},
            headers={"X-API-Key": api_key},
        )
        assignment_id = assign_resp.json()["id"]

        # Update
        resp = client.put(
            f"/partners/assignments/{assignment_id}",
            json={"status": "in_review", "notes": "Being investigated"},
            headers={"X-API-Key": api_key},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_review"


# === Dashboard (3.4) ===

class TestDashboard:
    def test_stats_endpoint(self, client):
        resp = client.get("/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_cases"] > 0
        assert data["total_evidence_items"] > 0
        assert "severity_distribution" in data
        assert "category_distribution" in data

    def test_category_breakdown(self, client):
        resp = client.get("/dashboard/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert "categories" in data
        assert len(data["categories"]) > 0

    def test_platform_stats(self, client):
        resp = client.get("/dashboard/platforms")
        assert resp.status_code == 200
        data = resp.json()
        assert "platforms" in data
        assert "instagram" in data["platforms"]


# === Court Export (3.6) ===

class TestCourtExport:
    def test_generates_valid_zip(self):
        case = get_case_by_id("case-001")
        zip_bytes = generate_court_package(case, "de")
        assert zip_bytes[:2] == b"PK"  # ZIP magic bytes

    def test_zip_contains_required_files(self):
        case = get_case_by_id("case-001")
        zip_bytes = generate_court_package(case, "de")

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert "manifest.json" in names
            assert "README.txt" in names
            assert "verification/hash_verification.txt" in names
            assert "verification/chain_of_evidence.txt" in names
            assert any(n.startswith("reports/") and n.endswith(".pdf") for n in names)
            assert any(n.startswith("evidence/") for n in names)

    def test_manifest_is_valid_json(self):
        case = get_case_by_id("case-002")
        zip_bytes = generate_court_package(case, "en")

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            manifest = json.loads(zf.read("manifest.json"))
            assert manifest["case"]["id"] == "case-002"
            assert len(manifest["evidence"]) > 0

    def test_hash_verification_included(self):
        case = get_case_by_id("case-001")
        zip_bytes = generate_court_package(case, "de")

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            hash_report = zf.read("verification/hash_verification.txt").decode()
            assert "SHA-256" in hash_report
            assert "VALID" in hash_report

    def test_court_package_endpoint(self, client):
        resp = client.get("/reports/case-001/court-package?lang=de")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/zip"
        assert resp.content[:2] == b"PK"

    def test_court_package_endpoint_en(self, client):
        resp = client.get("/reports/case-004/court-package?lang=en")
        assert resp.status_code == 200

    def test_court_package_404(self, client):
        resp = client.get("/reports/nonexistent/court-package")
        assert resp.status_code == 404


# === Partner Store ===

class TestPartnerStore:
    def test_create_org_returns_api_key(self):
        org = create_organization("Test Org", OrgType.NGO, "test@ngo.org")
        assert org.api_key.startswith("sv_")
        assert len(org.api_key) > 20

    def test_lookup_by_api_key(self):
        org = create_organization("Lookup Test", OrgType.LAW_FIRM, "law@test.de")
        found = get_org_by_api_key(org.api_key)
        assert found is not None
        assert found.id == org.id

    def test_invalid_api_key_returns_none(self):
        assert get_org_by_api_key("invalid_key") is None

    def test_add_member(self):
        org = create_organization("Member Test", OrgType.POLICE, "police@test.de")
        member = add_member(org.id, "officer@test.de", "Officer Test", OrgRole.ANALYST)
        assert member is not None
        assert member.role == OrgRole.ANALYST

    def test_case_assignment(self):
        org = create_organization("Assign Test", OrgType.POLICE, "assign@test.de")
        assignment = assign_case("case-001", org.id, "Berlin", "cybercrime")
        assert assignment.case_id == "case-001"
        assert assignment.jurisdiction == "Berlin"

        assignments = get_org_assignments(org.id)
        assert len(assignments) == 1
