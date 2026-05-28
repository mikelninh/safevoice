"""
Tool eval — verifies each MCP tool wraps the underlying SafeVoice service correctly
and returns a JSON-serialisable dict shape that an MCP client can consume.

We don't re-test the underlying services here (the backend has its own suite for
that). What we test is the *wrapper contract*: input shape, output shape pinned to
the actual service-layer schema, error handling, and JSON-serialisability at the
MCP boundary.

The `classify` tool needs OPENAI_API_KEY — those tests skip when missing so CI
without secrets still passes the rest.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from safevoice_mcp.server import (  # noqa: E402
    check_strafantrag_frist,
    classify,
    detect_anonymisierung_needed,
    detect_patterns,
    determine_jurisdiction,
    get_applicable_laws,
)

LLM_AVAILABLE = bool(os.getenv("OPENAI_API_KEY"))
llm_only = pytest.mark.skipif(not LLM_AVAILABLE, reason="classify needs OPENAI_API_KEY")


# Helper — build the minimum-valid EvidenceItem dict the wrapper expects.
def _ev(idx: int, *, author: str = "troll_a", text: str = "Test message") -> dict:
    return {
        "id": f"ev{idx}",
        "url": f"https://example.com/post/{idx}",
        "captured_at": f"2026-05-01T12:{idx:02d}:00Z",
        "author_username": author,
        "content_text": text,
        "content_hash": f"hash{idx}",
    }


# ── classify ─────────────────────────────────────────────────────────────


def test_classify_returns_dict_envelope():
    """Whether or not the LLM is reachable, classify must return a dict — never raise."""
    result = classify("Test text", jurisdiction="DE")
    assert isinstance(result, dict)
    # Either a real classification or a clean error envelope.
    assert "error" in result or "categories" in result


@llm_only
def test_classify_clear_threat_returns_non_empty_categories():
    result = classify(
        "Wenn du nochmal etwas postest, weiß ich wo du wohnst.",
        jurisdiction="DE",
        user_lang="de",
    )
    if "error" in result:
        pytest.skip(f"classifier unavailable: {result.get('message')}")
    assert isinstance(result, dict)
    assert "categories" in result
    assert len(result["categories"]) > 0
    assert result["severity"] in {"low", "medium", "high", "critical"}
    json.dumps(result)  # serialisable


# ── detect_patterns ──────────────────────────────────────────────────────


def test_detect_patterns_empty_input_returns_empty_list():
    assert detect_patterns([]) == []


def test_detect_patterns_handles_single_item():
    """One item can't form a pattern — empty list, no crash."""
    result = detect_patterns([_ev(0)])
    assert isinstance(result, list)
    assert len(result) == 0


def test_detect_patterns_with_multiple_items_returns_well_formed_flags():
    """Whatever the heuristic decides, each flag must be a JSON-serialisable dict."""
    items = [_ev(i, author=f"a{i}") for i in range(5)]
    result = detect_patterns(items)
    assert isinstance(result, list)
    for flag in result:
        assert isinstance(flag, dict)
        # Every PatternFlag has at minimum these fields per the model.
        assert "type" in flag
        assert "severity" in flag
        assert "evidence_count" in flag
        json.dumps(flag)


def test_detect_patterns_invalid_input_raises_validation_error():
    """A dict missing required EvidenceItem fields must surface a clear error envelope."""
    result = detect_patterns([{"id": "ev0", "text": "missing required fields"}])
    # The traced wrapper catches the ValidationError and returns an envelope.
    assert isinstance(result, dict)
    assert result.get("error") == "internal_error"


# ── get_applicable_laws ──────────────────────────────────────────────────


def test_get_applicable_laws_returns_well_formed_list():
    """Categories + country + severity → list of GermanLaw dicts, all JSON-serialisable."""
    laws = get_applicable_laws(categories=["beleidigung"], country="DE", severity="medium")
    assert isinstance(laws, list)
    # The mapping for beleidigung+medium should yield at least one statute.
    assert len(laws) > 0
    for law in laws:
        assert isinstance(law, dict)
        # GermanLaw model has at minimum: paragraph + title (+ many optional fields).
        assert "paragraph" in law
        assert "title" in law
        json.dumps(law)


def test_get_applicable_laws_unknown_country_returns_clean_error_envelope():
    """Unknown country triggers ValueError in the service — wrapper must catch + return envelope."""
    result = get_applicable_laws(categories=["beleidigung"], country="XX", severity="medium")
    # The traced wrapper converts the ValueError to a structured error dict.
    assert isinstance(result, dict)
    assert result.get("error") == "internal_error"
    assert "Unsupported country" in result.get("message", "")


def test_get_applicable_laws_returns_paragraph_strings():
    """Spot-check the shape — paragraph values look like '§ NNN ABBR' or 'ABBR § NNN'."""
    laws = get_applicable_laws(categories=["beleidigung"], country="DE", severity="medium")
    for law in laws:
        # Real-world refs include '§', 'Art', 'NetzDG §', etc. — pin only the shape, not the value.
        assert isinstance(law["paragraph"], str)
        assert len(law["paragraph"]) > 0


# ── check_strafantrag_frist ──────────────────────────────────────────────


def test_check_frist_for_beleidigung_returns_3_month_window():
    """§ 185 StGB has a 3-month Strafantragsfrist — pin the wrapper's return shape."""
    result = check_strafantrag_frist(
        earliest_evidence_iso="2026-05-01T00:00:00Z",
        applicable_laws=["stgb:185"],
    )
    assert isinstance(result, dict)
    assert "applicable_antragsdelikte" in result
    assert "warning_level" in result
    assert "summary" in result
    assert len(result["applicable_antragsdelikte"]) == 1
    entry = result["applicable_antragsdelikte"][0]
    assert entry["law"] == "stgb:185"
    assert entry["frist_months"] == 3
    assert "days_left" in entry
    assert "deadline_utc" in entry
    assert isinstance(entry["expired"], bool)


def test_check_frist_unparseable_timestamp_returns_clean_error():
    result = check_strafantrag_frist(
        earliest_evidence_iso="this is not a timestamp",
        applicable_laws=["stgb:185"],
    )
    assert "error" in result


def test_check_frist_unknown_law_skipped_silently():
    """Laws without a known Antragsfrist must be skipped, not error."""
    result = check_strafantrag_frist(
        earliest_evidence_iso="2026-05-01T00:00:00Z",
        applicable_laws=["stgb:99999_fake"],
    )
    assert result.get("applicable_antragsdelikte") == []


def test_check_frist_old_evidence_marks_expired():
    """Evidence > 6 months old should mark the 3-month-Frist as expired."""
    result = check_strafantrag_frist(
        earliest_evidence_iso="2024-01-01T00:00:00Z",
        applicable_laws=["stgb:185"],
    )
    assert result["applicable_antragsdelikte"][0]["expired"] is True
    assert result["warning_level"] in {"expired", "urgent", "ok"}


# ── determine_jurisdiction ───────────────────────────────────────────────


def test_determine_jurisdiction_berlin_returns_staatsanwaltschaft():
    result = determine_jurisdiction("BE")
    assert isinstance(result, dict)
    assert "staatsanwaltschaft" in result
    assert "rechtsgrundlage" in result
    assert result["bundesland_code"] == "BE"


@pytest.mark.parametrize("code", ["BE", "BY", "NW", "HE"])
def test_determine_jurisdiction_all_major_bundeslaender_resolve(code):
    result = determine_jurisdiction(code)
    assert "staatsanwaltschaft" in result, f"{code} missing Staatsanwaltschaft"


def test_determine_jurisdiction_unknown_code_returns_error_with_available_list():
    result = determine_jurisdiction("ZZ")
    assert "error" in result
    assert "available" in result
    assert "BE" in result["available"]


def test_determine_jurisdiction_lowercase_normalised():
    result = determine_jurisdiction("be")
    assert result.get("bundesland_code") == "BE"


# ── detect_anonymisierung_needed ─────────────────────────────────────────


def test_detect_anonymisierung_returns_real_schema():
    """Return shape: {needed, rechtsgrundlage, begruendung, triggering_categories}."""
    result = detect_anonymisierung_needed(categories=["beleidigung"], severity="low")
    assert isinstance(result, dict)
    assert "needed" in result
    assert isinstance(result["needed"], bool)
    assert "begruendung" in result
    assert "triggering_categories" in result


def test_detect_anonymisierung_low_severity_does_not_trigger():
    result = detect_anonymisierung_needed(categories=["beleidigung"], severity="low")
    assert result["needed"] is False


def test_detect_anonymisierung_handles_empty_categories():
    result = detect_anonymisierung_needed(categories=[], severity="low")
    assert result["needed"] is False


# ── Tool surface sanity ──────────────────────────────────────────────────


def test_all_tools_returns_are_json_serialisable():
    """Every tool's return value must round-trip through json — that's the MCP contract."""
    json.dumps(determine_jurisdiction("BE"))
    json.dumps(get_applicable_laws(categories=["beleidigung"], country="DE"))
    json.dumps(check_strafantrag_frist("2026-05-01T00:00:00Z", ["stgb:185"]))
    json.dumps(detect_anonymisierung_needed(categories=["beleidigung"], severity="medium"))
    json.dumps(detect_patterns([]))
