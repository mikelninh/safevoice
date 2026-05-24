"""
Agent endpoints — Court-Prep agent (MVP), more agents follow.

Two endpoints per agent:
  POST /agent/court-prep/{case_id}  — run synchronously, return artefacts
  GET  /agent/runs/{agent_run_id}   — fetch run + tool trace from the audit log

Synchronous run is fine for SafeVoice: a full Court-Prep run is 4-7 LLM hops
plus a handful of tool calls, ~10-30s end-to-end. Background-job indirection
adds DX cost without removing UX cost — the user is staring at a spinner
either way. If we move to fan-out workloads later, this is the place to add
a `BackgroundTasks` invocation + polling.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import AgentRun, ToolCallLog, get_db
from app.services.court_prep_agent import (
    PROMPT_VERSION as COURT_PREP_PROMPT_VERSION,
    run_court_prep,
    summarise_artefacts,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


class CourtPrepRequest(BaseModel):
    """Optional victim block — anything omitted leaves placeholders in the PDF.

    `relationship` distinguishes the three real-world cases:
      - 'self' (default): the victim files their own complaint
      - 'guardian': a legal guardian for a minor (Eltern für Kind),
        relevant for § 77 III StGB Strafantragsrecht der Erziehungsberechtigten
      - 'caretaker': a person filing on behalf of a relative (e.g. pflegende
        Angehörige), needs a Vollmacht — surfaced in the PDF as a note.
    """

    victim_name: str | None = None
    victim_email: str | None = None
    victim_address: str | None = None
    victim_phone: str | None = None
    bundesland_code: str | None = None
    relationship: str | None = "self"
    represented_name: str | None = None  # only used when relationship != 'self'
    lang: str | None = "de"  # 'de' | 'en' — language of the user-facing summary


@router.post("/court-prep/{case_id}")
def court_prep(
    case_id: str,
    req: CourtPrepRequest | None = None,
    db: Session = Depends(get_db),
):
    """Run the Court-Prep agent against `case_id` and return the artefacts.

    Returns 422 on iteration / budget abort with the partial trace so the UI
    can show what the agent reached before giving up. 503 on LLM unavail.
    """
    req = req or CourtPrepRequest()

    result = run_court_prep(
        db=db,
        case_id=case_id,
        victim_name=req.victim_name,
        victim_email=req.victim_email,
        victim_address=req.victim_address,
        victim_phone=req.victim_phone,
        bundesland_code=req.bundesland_code,
        relationship=req.relationship or "self",
        represented_name=req.represented_name,
        lang=req.lang or "de",
    )

    if result.status == "failed" and result.error == "openai_unavailable":
        raise HTTPException(
            status_code=503,
            detail="LLM unavailable — OPENAI_API_KEY missing or provider down.",
        )

    artefacts = summarise_artefacts(result.tool_trace)

    # Hash-chain CSV intentionally NOT generated as a user-facing download:
    # it's a technical verification artefact a victim doesn't need cluttering
    # their package. The SHA-256 chain still backs every piece of evidence and
    # is available officer-side via the .eml export when a case is actually
    # filed — it just doesn't belong in the one-click victim flow.

    # Strip the base64 payloads out of the trace so the trace stays UI-light.
    # Artefacts retain everything; the trace is for the live tool-call view.
    light_trace = []
    for call in result.tool_trace:
        out = call.get("output") or {}
        light_out = {
            k: v
            for k, v in (out.items() if isinstance(out, dict) else [])
            if k not in {"pdf_base64", "eml_base64"}
        }
        light_trace.append({**call, "output": light_out})

    payload = {
        "agent_run_id": result.agent_run_id,
        "status": result.status,
        "iterations": result.iterations,
        "total_cost_usd": round(result.total_cost_usd, 6),
        "total_prompt_tokens": result.total_prompt_tokens,
        "total_completion_tokens": result.total_completion_tokens,
        "rounds": result.rounds,
        "prompt_version": COURT_PREP_PROMPT_VERSION,
        "final_message": result.final_message,
        "error": result.error,
        "tool_trace": light_trace,
        "artefacts": artefacts,
    }

    if result.status in {"aborted_budget", "aborted_iterations", "failed"}:
        # 422 = "we did some work, here's what we have, but the run did not
        # complete normally". Lets the UI render partial output.
        raise HTTPException(status_code=422, detail=payload)

    return payload


@router.get("/runs/{agent_run_id}")
def get_run(agent_run_id: str, db: Session = Depends(get_db)):
    """Fetch a persisted agent run with its full tool-call audit trail.

    Useful for: debugging an old run, re-rendering the trace in the UI, or
    extracting tool outputs after the original response was discarded.
    """
    run = db.query(AgentRun).filter_by(id=agent_run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail="agent run not found")

    tool_calls = (
        db.query(ToolCallLog)
        .filter_by(agent_run_id=agent_run_id)
        .order_by(ToolCallLog.called_at.asc())
        .all()
    )

    return {
        "id": run.id,
        "agent_name": run.agent_name,
        "case_id": run.case_id,
        "user_id": run.user_id,
        "status": run.status,
        "total_iterations": run.total_iterations,
        "total_cost_usd": round(run.total_cost_usd or 0.0, 6),
        "error": run.error,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": (run.completed_at.isoformat() if run.completed_at else None),
        "input": _safe_load(run.input_json),
        "output": _safe_load(run.output_json),
        "tool_calls": [
            {
                "tool_name": tc.tool_name,
                "input": _safe_load(tc.input_json),
                "output": _safe_load(tc.output_json),
                "latency_ms": tc.latency_ms,
                "cached": tc.cached,
                "error": tc.error,
                "called_at": tc.called_at.isoformat() if tc.called_at else None,
            }
            for tc in tool_calls
        ],
    }


def _safe_load(s: str | None):
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return s
