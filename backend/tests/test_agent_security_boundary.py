"""Security regressions for the model -> Court-Prep tool boundary.

These tests model a compromised agent output. The important metric is whether
the underlying case/network handler runs, not whether the prompt looked safe.
"""

from __future__ import annotations

from app.database import Case as DBCase, SessionLocal
from app.services import court_prep_agent
from app.services import evidence as evidence_service
from app.services.agent_loop import ToolDef
from app.services.court_prep_security import bind_court_prep_tools
from app.services.court_prep_tools import build_tools


TEST_CASE_ID = "case-001"


def _bound_tools(db):
    return {
        tool.name: tool
        for tool in bind_court_prep_tools(
            db=db,
            case_id=TEST_CASE_ID,
            tools=build_tools(db),
        )
    }


def test_cross_case_attack_never_reaches_underlying_handler():
    """Executor-level proof: a model-selected foreign case causes zero handler calls."""

    handler_calls = 0

    def underlying_handler(args):
        nonlocal handler_calls
        handler_calls += 1
        return {"ok": True, "case_id": args["case_id"]}

    tool = ToolDef(
        name="read_case",
        description="test tool",
        schema={
            "type": "object",
            "properties": {"case_id": {"type": "string"}},
            "required": ["case_id"],
        },
        handler=underlying_handler,
    )
    bound = bind_court_prep_tools(
        db=None,
        case_id=TEST_CASE_ID,
        tools=[tool],
    )[0]

    result = bound.handler({"case_id": "case-attacker-selected"})

    assert result["error"] == "case_scope_violation"
    assert handler_calls == 0


def test_all_case_id_tools_fail_closed_on_model_case_switch():
    """A compromised model cannot pivot from the active case to another case."""

    db = SessionLocal()
    try:
        tools = _bound_tools(db)
        scoped_names = {
            name
            for name, tool in tools.items()
            if "case_id" in ((tool.schema or {}).get("properties") or {})
        }
        assert {
            "read_case",
            "draft_netzdg_email",
            "generate_strafanzeige_pdf",
            "build_onlinewache_text",
        }.issubset(scoped_names)

        for name in scoped_names:
            result = tools[name].handler({"case_id": "case-attacker-selected"})
            assert result["error"] == "case_scope_violation", (name, result)
            assert result["active_case_id"] == TEST_CASE_ID
            assert result["requested_case_id"] == "case-attacker-selected"
    finally:
        db.close()


def test_archive_tool_blocks_model_invented_url_before_network_call(monkeypatch):
    """A malicious document cannot make the agent archive an arbitrary URL."""

    network_calls: list[str] = []

    def fake_archive(url: str):
        network_calls.append(url)
        return f"https://web.archive.org/web/test/{url}"

    monkeypatch.setattr(evidence_service, "archive_url_sync", fake_archive)

    db = SessionLocal()
    try:
        archive_tool = _bound_tools(db)["re_archive_urls"]
        result = archive_tool.handler(
            {
                "urls": [
                    {
                        "url": "https://attacker.invalid/model-chosen-target",
                        "platform": "instagram",
                    }
                ]
            }
        )

        assert result["error"] == "archive_url_outside_case_scope"
        assert result["attempted"] == 0
        assert result["succeeded"] == 0
        assert network_calls == []
    finally:
        db.close()


def test_archive_tool_allows_only_database_backed_case_evidence(monkeypatch):
    """Legitimate case evidence still works, with platform metadata from the DB."""

    network_calls: list[str] = []

    def fake_archive(url: str):
        network_calls.append(url)
        return f"https://web.archive.org/web/test/{url}"

    monkeypatch.setattr(evidence_service, "archive_url_sync", fake_archive)

    db = SessionLocal()
    try:
        case = db.query(DBCase).filter_by(id=TEST_CASE_ID).first()
        assert case is not None
        evidence = next((ev for ev in case.evidence_items if ev.source_url), None)
        assert evidence is not None, "seeded security test requires one source URL"

        archive_tool = _bound_tools(db)["re_archive_urls"]
        result = archive_tool.handler(
            {
                "urls": [
                    {
                        "url": evidence.source_url,
                        # Deliberately spoofed. The wrapper must replace this
                        # with the database-backed evidence platform.
                        "platform": "attacker-controlled-label",
                    }
                ]
            }
        )

        assert result["attempted"] == 1
        assert result["succeeded"] == 1
        assert network_calls == [evidence.source_url]
        assert result["results"][0]["platform"] == (evidence.platform or "unknown")
    finally:
        db.close()


def test_run_court_prep_wires_the_case_security_boundary(monkeypatch):
    """The production Court-Prep entrypoint must use the scoped tool surface."""

    captured = {}

    def fake_bind(*, db, case_id, tools):
        captured["bound_case_id"] = case_id
        captured["input_tool_count"] = len(tools)
        return ["case-scoped-tools"]

    def fake_run_agent(**kwargs):
        captured["run_tools"] = kwargs["tools"]
        captured["run_case_id"] = kwargs["case_id"]
        return "sentinel-result"

    monkeypatch.setattr(court_prep_agent, "bind_court_prep_tools", fake_bind)
    monkeypatch.setattr(court_prep_agent.agent_loop, "run_agent", fake_run_agent)

    db = SessionLocal()
    try:
        result = court_prep_agent.run_court_prep(db=db, case_id=TEST_CASE_ID)
        assert result == "sentinel-result"
        assert captured["bound_case_id"] == TEST_CASE_ID
        assert captured["run_case_id"] == TEST_CASE_ID
        assert captured["input_tool_count"] >= 1
        assert captured["run_tools"] == ["case-scoped-tools"]
    finally:
        db.close()
