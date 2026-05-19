"""
Tests for the Court-Prep agent loop and its tools.

Strategy:
  - Pure tool functions (jurisdiction, frist, anonymisierung) get exhaustive
    unit tests — they encode legal logic and must not silently regress.
  - DB-bound tools (read_case, NetzDG draft, PDF generate) get smoke tests
    against the conftest-seeded mock case (case-001).
  - The agent loop itself is exercised via a fake `chat_with_tools` that
    scripts a deterministic 4-step plan. No real OpenAI call.
  - An end-to-end endpoint test runs through TestClient with the same fake.

The fake gateway is monkey-patched into `app.services.llm_gateway`; the
agent_loop imports lazily inside the function so the patch takes effect.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.database import AgentRun, SessionLocal, ToolCallLog
from app.main import app
from app.services import agent_loop, llm_gateway
from app.services.court_prep_tools import (
    check_strafantrag_frist,
    detect_anonymisierung_needed,
    determine_jurisdiction,
)


TEST_CASE_ID = "case-001"


# ── Pure-tool unit tests ─────────────────────────────────────────────────


class TestDetermineJurisdiction:
    def test_berlin(self):
        result = determine_jurisdiction({"bundesland_code": "BE"})
        assert "error" not in result
        assert "Berlin" in result["staatsanwaltschaft"]["name"]
        assert result["rechtsgrundlage"].startswith("§ 7 StPO")

    def test_lowercase_is_normalised(self):
        result = determine_jurisdiction({"bundesland_code": "by"})
        assert result["staatsanwaltschaft"]["name"].startswith(
            "Staatsanwaltschaft München"
        )

    def test_unknown_code_returns_error_with_choices(self):
        result = determine_jurisdiction({"bundesland_code": "XX"})
        assert "error" in result
        assert "BE" in result["available"]


class TestCheckStrafantragFrist:
    def _iso(self, days_ago: int) -> str:
        return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()

    def test_recent_evidence_is_ok(self):
        result = check_strafantrag_frist(
            {
                "earliest_evidence_iso": self._iso(7),
                "applicable_laws": ["stgb:185"],
            }
        )
        assert result["warning_level"] == "ok"
        assert result["applicable_antragsdelikte"][0]["expired"] is False

    def test_urgent_when_less_than_seven_days_left(self):
        # 3-month frist = 90 days; 85 days ago leaves ~5 days
        result = check_strafantrag_frist(
            {
                "earliest_evidence_iso": self._iso(85),
                "applicable_laws": ["stgb:185"],
            }
        )
        assert result["warning_level"] == "urgent"

    def test_expired_when_past_frist(self):
        result = check_strafantrag_frist(
            {
                "earliest_evidence_iso": self._iso(120),
                "applicable_laws": ["stgb:185"],
            }
        )
        assert result["warning_level"] == "expired"
        assert result["applicable_antragsdelikte"][0]["expired"] is True

    def test_offizialdelikte_only_returns_empty_relevant_list(self):
        result = check_strafantrag_frist(
            {
                "earliest_evidence_iso": self._iso(7),
                "applicable_laws": ["stgb:241", "stgb:130"],
            }
        )
        assert result["applicable_antragsdelikte"] == []

    def test_unparseable_timestamp(self):
        result = check_strafantrag_frist(
            {"earliest_evidence_iso": "not-a-date", "applicable_laws": ["stgb:185"]}
        )
        assert "error" in result


class TestDetectAnonymisierung:
    def test_doxxing_high_severity_triggers(self):
        result = detect_anonymisierung_needed(
            {"categories": ["doxxing"], "overall_severity": "high"}
        )
        assert result["needed"] is True
        assert "200a StPO" in result["rechtsgrundlage"]
        assert "doxxing" in result["triggering_categories"]

    def test_harassment_low_severity_does_not_trigger(self):
        result = detect_anonymisierung_needed(
            {"categories": ["harassment"], "overall_severity": "low"}
        )
        assert result["needed"] is False
        assert result["rechtsgrundlage"] is None

    def test_stalking_at_critical(self):
        result = detect_anonymisierung_needed(
            {
                "categories": ["stalking", "harassment"],
                "overall_severity": "critical",
            }
        )
        assert result["needed"] is True

    def test_trigger_category_without_severity_does_not_qualify(self):
        result = detect_anonymisierung_needed(
            {"categories": ["doxxing"], "overall_severity": "medium"}
        )
        assert result["needed"] is False

    def test_db_name_cyberstalking_still_triggers(self):
        # Real `read_case` returns DB category names. `stalking` → `cyberstalking`
        # via _CATEGORY_MAP. Trigger must catch the DB-side name too, otherwise
        # the agent silently misses stalking cases.
        result = detect_anonymisierung_needed(
            {"categories": ["cyberstalking"], "overall_severity": "high"}
        )
        assert result["needed"] is True


class TestReadCaseFlowsIntoAnonymisierung:
    """End-to-end via the real DB → tool data flow.

    Catches the silent category-loss bug surfaced 2026-05-19: classifier
    output `doxxing` was dropped by `db_helpers._CATEGORY_MAP`, so cases
    that should trigger § 200a StPO never did. Regression guard.
    """

    def test_doxxing_classifier_output_survives_to_anonymisierung(self):
        from app.database import (
            Category as DBCategory,
            Classification as DBClassification,
            EvidenceItem as DBEvidence,
            Case as DBCase,
        )
        from app.services.court_prep_tools import (
            detect_anonymisierung_needed,
            make_read_case,
        )

        db = SessionLocal()
        try:
            # Idempotent: drop any leftover from a previous failed run.
            existing = db.query(DBCase).filter_by(id="test-doxxing-flow").first()
            if existing:
                for old_ev in list(existing.evidence_items):
                    if old_ev.classification:
                        db.delete(old_ev.classification)
                    db.delete(old_ev)
                db.delete(existing)
                db.commit()

            # Build a synthetic case with a doxxing classification in the DB.
            case = DBCase(
                id="test-doxxing-flow",
                title="doxxing regression test",
                status="open",
                overall_severity="high",
            )
            db.add(case)
            db.flush()

            ev = DBEvidence(
                id="test-doxxing-flow-ev",
                case_id=case.id,
                content_type="text",
                raw_content="...victim's address posted...",
                content_hash="x" * 64,
                platform="x",
                source_url="https://x.com/example",
            )
            db.add(ev)
            db.flush()

            doxxing_cat = db.query(DBCategory).filter_by(id="doxxing").first()
            # If the seed is missing it, that itself is the bug — fail loudly.
            assert doxxing_cat is not None, (
                "seed must contain 'doxxing' category for § 200a StPO logic"
            )

            cls = DBClassification(
                id="test-doxxing-flow-cls",
                evidence_item_id=ev.id,
                severity="high",
                confidence=0.95,
                classifier_tier=1,
                summary_de="Doxxing: private Adresse veröffentlicht.",
            )
            db.add(cls)
            db.flush()
            cls.categories.append(doxxing_cat)
            db.commit()

            # Now read_case → detect_anon, exactly as the agent does.
            case_data = make_read_case(db)({"case_id": case.id})
            assert "error" not in case_data
            all_cats = {
                c
                for ev in case_data["evidence"]
                if ev.get("classification")
                for c in ev["classification"]["categories"]
            }
            assert "doxxing" in all_cats

            anon = detect_anonymisierung_needed(
                {
                    "categories": list(all_cats),
                    "overall_severity": case_data["overall_severity"],
                }
            )
            assert anon["needed"] is True, (
                f"§ 200a StPO must trigger for doxxing+high; got {anon}"
            )

            # Cleanup
            db.delete(cls)
            db.delete(ev)
            db.delete(case)
            db.commit()
        finally:
            db.close()


# ── DB-bound smoke test ──────────────────────────────────────────────────


class TestReadCaseTool:
    def test_loads_seeded_case(self):
        from app.services.court_prep_tools import make_read_case

        db = SessionLocal()
        try:
            handler = make_read_case(db)
            result = handler({"case_id": TEST_CASE_ID})
            assert "error" not in result
            assert result["case_id"] == TEST_CASE_ID
            assert result["evidence_count"] > 0
            ev = result["evidence"][0]
            assert "content_hash" in ev
            assert "classification" in ev
        finally:
            db.close()

    def test_missing_case_returns_error(self):
        from app.services.court_prep_tools import make_read_case

        db = SessionLocal()
        try:
            result = make_read_case(db)({"case_id": "does-not-exist"})
            assert "error" in result
        finally:
            db.close()


# ── Agent loop with scripted LLM ─────────────────────────────────────────


@dataclass
class _FakeUsage:
    prompt_tokens: int = 100
    completion_tokens: int = 30
    total_tokens: int = 130


@dataclass
class _FakeChatResult:
    content: str | None = None
    model: str = "gpt-4o-mini"
    usage: _FakeUsage = field(default_factory=_FakeUsage)
    estimated_cost_usd: float = 0.0001
    request_id: str = "req-test"
    raw_message: Any = None
    refusal: str | None = None
    parsed: Any = None
    error: str | None = None
    tool_calls: list[dict] = field(default_factory=list)


def _tool_call(name: str, args: dict, call_id: str) -> dict:
    return {
        "id": call_id,
        "name": name,
        "arguments": args,
        "arguments_raw": json.dumps(args),
    }


def _build_scripted_responses(case_id: str) -> list[_FakeChatResult]:
    """Script a deterministic 5-step plan for the agent."""
    return [
        # Step 1: read_case
        _FakeChatResult(
            content="",
            tool_calls=[_tool_call("read_case", {"case_id": case_id}, "tc-1")],
        ),
        # Step 2: parallel — check frist + detect anon
        _FakeChatResult(
            content="",
            tool_calls=[
                _tool_call(
                    "check_strafantrag_frist",
                    {
                        "earliest_evidence_iso": (
                            datetime.now(timezone.utc) - timedelta(days=10)
                        ).isoformat(),
                        "applicable_laws": ["stgb:185"],
                    },
                    "tc-2",
                ),
                _tool_call(
                    "detect_anonymisierung_needed",
                    {"categories": ["doxxing"], "overall_severity": "high"},
                    "tc-3",
                ),
            ],
        ),
        # Step 3: generate the PDF
        _FakeChatResult(
            content="",
            tool_calls=[
                _tool_call(
                    "generate_strafanzeige_pdf",
                    {"case_id": case_id, "victim_name": "Test Person"},
                    "tc-4",
                )
            ],
        ),
        # Step 4: final summary, no more tool calls
        _FakeChatResult(
            content=(
                "Fall enthält Evidence. § 185 StGB einschlägig. Frist im Rahmen. "
                "Anonymisierung empfohlen. Strafanzeige-PDF bereit. Nichts wurde versendet."
            ),
            tool_calls=[],
        ),
    ]


def _make_fake_chat_with_tools(responses: list[_FakeChatResult]):
    counter = {"i": 0}

    def fake(**kwargs):
        i = counter["i"]
        counter["i"] += 1
        if i >= len(responses):
            return _FakeChatResult(content="(no more script)", tool_calls=[])
        return responses[i]

    return fake


class TestAgentLoopScripted:
    def test_completes_with_artefacts(self, monkeypatch):
        # Patch the LLM gateway to use our scripted responses.
        responses = _build_scripted_responses(TEST_CASE_ID)
        monkeypatch.setattr(
            llm_gateway,
            "chat_with_tools",
            _make_fake_chat_with_tools(responses),
        )
        # Bypass the availability gate.
        monkeypatch.setattr(llm_gateway, "is_available", lambda: True)

        from app.services.court_prep_agent import run_court_prep, summarise_artefacts

        db = SessionLocal()
        try:
            result = run_court_prep(
                db=db,
                case_id=TEST_CASE_ID,
                victim_name="Test Person",
                bundesland_code=None,
            )
            assert result.status == "completed", result.error
            assert result.iterations >= 3
            artefacts = summarise_artefacts(result.tool_trace)
            assert artefacts["strafanzeige_pdf_base64"], "expected PDF artefact"
            assert artefacts["anonymisierung"]["needed"] is True
            assert artefacts["frist"]["warning_level"] in {"ok", "urgent", "expired"}

            # Audit trail persisted
            run_row = db.query(AgentRun).filter_by(id=result.agent_run_id).first()
            assert run_row is not None
            assert run_row.status == "completed"

            tc_rows = (
                db.query(ToolCallLog).filter_by(agent_run_id=result.agent_run_id).all()
            )
            assert len(tc_rows) >= 4
            assert {t.tool_name for t in tc_rows} >= {
                "read_case",
                "check_strafantrag_frist",
                "detect_anonymisierung_needed",
                "generate_strafanzeige_pdf",
            }
        finally:
            db.close()

    def test_idempotency_cache_hit(self, monkeypatch):
        # Script: read_case twice in a row with identical input. Second call
        # must be served from the in-run idempotency cache.
        responses = [
            _FakeChatResult(
                content="",
                tool_calls=[
                    _tool_call("read_case", {"case_id": TEST_CASE_ID}, "tc-a"),
                ],
            ),
            _FakeChatResult(
                content="",
                tool_calls=[
                    _tool_call("read_case", {"case_id": TEST_CASE_ID}, "tc-b"),
                ],
            ),
            _FakeChatResult(content="done", tool_calls=[]),
        ]
        monkeypatch.setattr(
            llm_gateway,
            "chat_with_tools",
            _make_fake_chat_with_tools(responses),
        )
        monkeypatch.setattr(llm_gateway, "is_available", lambda: True)

        from app.services.court_prep_agent import run_court_prep

        db = SessionLocal()
        try:
            result = run_court_prep(db=db, case_id=TEST_CASE_ID)
            assert result.status == "completed"
            tcs = (
                db.query(ToolCallLog)
                .filter_by(agent_run_id=result.agent_run_id, tool_name="read_case")
                .all()
            )
            assert len(tcs) == 2
            assert any(tc.cached for tc in tcs), "expected one cache-hit on repeat"
        finally:
            db.close()

    def test_iteration_cap_aborts(self, monkeypatch):
        # Always request the same tool — the loop should hit max_iterations
        # and abort cleanly.
        def loop_forever(**kwargs):
            return _FakeChatResult(
                content="",
                tool_calls=[
                    _tool_call(
                        "read_case", {"case_id": TEST_CASE_ID}, f"tc-{id(kwargs)}"
                    ),
                ],
            )

        monkeypatch.setattr(llm_gateway, "chat_with_tools", loop_forever)
        monkeypatch.setattr(llm_gateway, "is_available", lambda: True)

        from app.services.court_prep_agent import run_court_prep

        db = SessionLocal()
        try:
            result = run_court_prep(db=db, case_id=TEST_CASE_ID, max_iterations=3)
            assert result.status == "aborted_iterations"
            assert "iteration limit" in (result.error or "")
        finally:
            db.close()


# ── HTTP endpoint integration ────────────────────────────────────────────


class TestCourtPrepEndpoint:
    def test_post_returns_artefacts(self, monkeypatch):
        responses = _build_scripted_responses(TEST_CASE_ID)
        monkeypatch.setattr(
            llm_gateway,
            "chat_with_tools",
            _make_fake_chat_with_tools(responses),
        )
        monkeypatch.setattr(llm_gateway, "is_available", lambda: True)

        client = TestClient(app)
        resp = client.post(
            f"/agent/court-prep/{TEST_CASE_ID}",
            json={"victim_name": "Test Person"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["status"] == "completed"
        assert data["agent_run_id"]
        assert data["prompt_version"]
        assert data["artefacts"]["strafanzeige_pdf_base64"]
        # Trace is light — base64 blobs stripped
        for call in data["tool_trace"]:
            if isinstance(call.get("output"), dict):
                assert "pdf_base64" not in call["output"]
                assert "eml_base64" not in call["output"]

    def test_get_run_returns_full_audit(self, monkeypatch):
        responses = _build_scripted_responses(TEST_CASE_ID)
        monkeypatch.setattr(
            llm_gateway,
            "chat_with_tools",
            _make_fake_chat_with_tools(responses),
        )
        monkeypatch.setattr(llm_gateway, "is_available", lambda: True)

        client = TestClient(app)
        post = client.post(
            f"/agent/court-prep/{TEST_CASE_ID}", json={"victim_name": "Y"}
        )
        run_id = post.json()["agent_run_id"]

        got = client.get(f"/agent/runs/{run_id}")
        assert got.status_code == 200
        body = got.json()
        assert body["status"] == "completed"
        assert body["agent_name"] == "court_prep"
        assert len(body["tool_calls"]) >= 4

    def test_returns_503_when_llm_unavailable(self, monkeypatch):
        monkeypatch.setattr(llm_gateway, "is_available", lambda: False)
        client = TestClient(app)
        resp = client.post(f"/agent/court-prep/{TEST_CASE_ID}", json={})
        assert resp.status_code == 503
