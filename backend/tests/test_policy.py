"""
Tests for Phase 5: Policy Impact APIs.

Covers:
  5.1  Evidence Standard (Bundestag)
  5.2  DSA Transparency Report (EU)
  5.3  Research Dataset + Data Dictionary (Academic)
  5.4  Digitale-Gewalt-Gesetz Submission (German Parliament)
  5.5  Europol SIENA Cross-Border Package
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.data.mock_data import get_all_cases
from app.services.policy_export import (
    generate_evidence_standard,
    generate_dsa_report,
    generate_research_dataset,
    generate_dgeg_submission,
    generate_europol_siena,
    _build_data_dictionary,
    _hash_id,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def cases():
    return get_all_cases()


# ======================================================================
# 5.1 Evidence Standard
# ======================================================================

class TestEvidenceStandard:
    def test_has_version(self):
        result = generate_evidence_standard()
        assert "version" in result
        assert result["version"] == "1.0.0"

    def test_has_required_fields(self):
        result = generate_evidence_standard()
        fields = result["fields"]
        for key in ("id", "url", "platform", "captured_at", "content_text", "content_hash", "classification"):
            assert key in fields, f"Missing field: {key}"

    def test_classification_has_severity_categories_laws(self):
        result = generate_evidence_standard()
        cls = result["fields"]["classification"]["properties"]
        assert "severity" in cls
        assert "categories" in cls
        assert "laws" in cls

    def test_metadata_present(self):
        result = generate_evidence_standard()
        meta = result["metadata"]
        assert meta["hash_algorithm"] == "SHA-256"
        assert "ISO-8601" in meta["timestamp_format"]
        assert "DE" in meta["supported_countries"]

    def test_endpoint_returns_200(self, client):
        resp = client.get("/policy/evidence-standard")
        assert resp.status_code == 200
        data = resp.json()
        assert "fields" in data
        assert "metadata" in data


# ======================================================================
# 5.2 DSA Transparency Report
# ======================================================================

class TestDSAReport:
    def test_has_reporting_period(self, cases):
        result = generate_dsa_report(cases)
        assert "reporting_period" in result
        assert "start" in result["reporting_period"]
        assert "end" in result["reporting_period"]

    def test_has_removal_rate(self, cases):
        result = generate_dsa_report(cases)
        assert "removal_rate" in result
        assert 0 <= result["removal_rate"] <= 1

    def test_has_reports_by_category(self, cases):
        result = generate_dsa_report(cases)
        assert "reports_by_category" in result
        assert len(result["reports_by_category"]) > 0

    def test_has_methodology(self, cases):
        result = generate_dsa_report(cases)
        assert "methodology_description" in result

    def test_lang_en(self, cases):
        result = generate_dsa_report(cases, lang="en")
        assert "DSA" in result["report_title"]
        assert "SafeVoice captures" in result["methodology_description"]

    def test_endpoint_returns_200(self, client):
        resp = client.get("/policy/dsa-report?lang=de")
        assert resp.status_code == 200
        data = resp.json()
        assert "reporting_period" in data

    def test_endpoint_en(self, client):
        resp = client.get("/policy/dsa-report?lang=en")
        assert resp.status_code == 200


# ======================================================================
# 5.3 Research Dataset (Anonymization Tests)
# ======================================================================

class TestResearchDataset:
    def test_no_usernames(self, cases):
        """CRITICAL: no raw usernames in the dataset."""
        result = generate_research_dataset(cases)
        raw = str(result)
        # Check known usernames from mock data
        for username in ("beef_truth99", "meatlovers_unite", "realfoodonly_k",
                         "anon_justice_x", "user_k2291", "dm_slides_23",
                         "crypto_advisor_thomas_w"):
            assert username not in raw, f"PII leak: username '{username}' found in dataset"

    def test_no_urls(self, cases):
        """CRITICAL: no URLs in the dataset."""
        result = generate_research_dataset(cases)
        raw = str(result)
        assert "instagram.com" not in raw
        assert "archive.org" not in raw
        assert "https://" not in raw
        assert "http://" not in raw

    def test_no_content_text(self, cases):
        """CRITICAL: no raw content text in the dataset."""
        result = generate_research_dataset(cases)
        raw = str(result)
        # Fragments from mock evidence
        assert "steak" not in raw.lower()
        assert "kitchen" not in raw.lower()
        assert "bitcoin" not in raw.lower()
        assert "disgusting" not in raw.lower()

    def test_no_victim_context(self, cases):
        """CRITICAL: no victim_context field in the dataset."""
        result = generate_research_dataset(cases)
        raw = str(result)
        assert "vegan" not in raw.lower()
        assert "reproductive" not in raw.lower()

    def test_no_display_names(self, cases):
        result = generate_research_dataset(cases)
        raw = str(result)
        assert "Beef Truth" not in raw
        assert "Thomas Weber" not in raw

    def test_case_ids_are_hashed(self, cases):
        result = generate_research_dataset(cases)
        for record in result["records"]:
            # Hashed IDs should NOT match the originals
            assert record["case_id"] not in ("case-001", "case-002", "case-003", "case-004")
            assert len(record["case_id"]) == 16  # truncated hash

    def test_timestamps_date_only(self, cases):
        result = generate_research_dataset(cases)
        for record in result["records"]:
            ts = record["timestamp"]
            # Should be YYYY-MM-DD only (10 chars)
            assert len(ts) == 10, f"Timestamp has time component: {ts}"
            assert "T" not in ts

    def test_has_data_dictionary(self, cases):
        result = generate_research_dataset(cases)
        assert "data_dictionary" in result
        assert len(result["data_dictionary"]) >= 5

    def test_records_have_expected_fields(self, cases):
        result = generate_research_dataset(cases)
        for record in result["records"]:
            assert "case_id" in record
            assert "category_counts" in record
            assert "severity" in record
            assert "timestamp" in record
            assert "platform" in record
            assert "country" in record
            assert "pattern_flags" in record

    def test_endpoint_returns_200(self, client):
        resp = client.get("/policy/research-dataset")
        assert resp.status_code == 200
        data = resp.json()
        assert "records" in data
        assert "data_dictionary" in data

    def test_dictionary_endpoint(self, client):
        resp = client.get("/policy/research-dictionary")
        assert resp.status_code == 200
        data = resp.json()
        assert "data_dictionary" in data
        assert len(data["data_dictionary"]) >= 5


# ======================================================================
# 5.4 Digitale-Gewalt-Gesetz Submission
# ======================================================================

class TestDGeGSubmission:
    def test_has_policy_recommendations(self, cases):
        result = generate_dgeg_submission(cases, lang="de")
        assert "policy_recommendations_de" in result
        assert "policy_recommendations_en" in result
        assert len(result["policy_recommendations_de"]) >= 3
        assert len(result["policy_recommendations_en"]) >= 3

    def test_has_severity_breakdown(self, cases):
        result = generate_dgeg_submission(cases)
        assert "severity_breakdown" in result
        assert "total_cases" in result

    def test_has_most_common_offenses(self, cases):
        result = generate_dgeg_submission(cases)
        assert "most_common_offenses" in result
        assert len(result["most_common_offenses"]) > 0
        first = result["most_common_offenses"][0]
        assert "offense" in first
        assert "count" in first

    def test_has_platform_compliance(self, cases):
        result = generate_dgeg_submission(cases)
        assert "platform_compliance_rates" in result

    def test_victim_demographics_anonymized(self, cases):
        result = generate_dgeg_submission(cases)
        raw = str(result["victim_demographics"])
        # Only platforms and categories — no usernames
        assert "beef_truth99" not in raw
        assert "anon_justice_x" not in raw

    def test_endpoint_returns_200(self, client):
        resp = client.get("/policy/dgeg-submission?lang=de")
        assert resp.status_code == 200
        data = resp.json()
        assert "policy_recommendations_de" in data

    def test_endpoint_en(self, client):
        resp = client.get("/policy/dgeg-submission?lang=en")
        assert resp.status_code == 200
        data = resp.json()
        assert "Digital Violence Act" in data["submission_title"]


# ======================================================================
# 5.5 Europol SIENA
# ======================================================================

class TestEuropolSIENA:
    def test_has_cross_border_indicators(self, cases):
        result = generate_europol_siena(cases)
        cbi = result["cross_border_indicators"]
        assert "multi_language_content" in cbi
        assert "foreign_platform_operators" in cbi

    def test_offenders_pseudonymized(self, cases):
        result = generate_europol_siena(cases)
        raw = str(result["flagged_offenders"])
        # No real usernames
        for username in ("beef_truth99", "anon_justice_x", "crypto_advisor_thomas_w"):
            assert username not in raw
        # But we do have hashed entries
        assert len(result["flagged_offenders"]) > 0
        for entry in result["flagged_offenders"]:
            assert "pseudonymized_id" in entry
            assert len(entry["pseudonymized_id"]) == 16

    def test_has_originating_country(self, cases):
        result = generate_europol_siena(cases)
        assert result["originating_country"] == "DE"

    def test_has_requesting_authority(self, cases):
        result = generate_europol_siena(cases)
        assert "requesting_authority" in result
        assert len(result["requesting_authority"]) > 0

    def test_has_offense_types(self, cases):
        result = generate_europol_siena(cases)
        assert "offense_types" in result
        assert len(result["offense_types"]) > 0

    def test_urgency_level_high_for_critical(self, cases):
        result = generate_europol_siena(cases)
        # Mock data has critical cases
        assert result["urgency_level"] == "high"

    def test_has_reference_number(self, cases):
        result = generate_europol_siena(cases)
        assert result["reference_number"].startswith("SV-SIENA-")

    def test_endpoint_returns_200(self, client):
        resp = client.get("/policy/europol-siena")
        assert resp.status_code == 200
        data = resp.json()
        assert "cross_border_indicators" in data
        assert "flagged_offenders" in data


# ======================================================================
# Helper function tests
# ======================================================================

class TestHelpers:
    def test_hash_id_deterministic(self):
        assert _hash_id("test") == _hash_id("test")

    def test_hash_id_different_inputs(self):
        assert _hash_id("case-001") != _hash_id("case-002")

    def test_hash_id_length(self):
        assert len(_hash_id("anything")) == 16

    def test_data_dictionary_fields(self):
        dd = _build_data_dictionary()
        field_names = {d["field"] for d in dd}
        assert "case_id" in field_names
        assert "severity" in field_names
        assert "timestamp" in field_names
        assert "platform" in field_names
