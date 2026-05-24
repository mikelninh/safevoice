"""
Generic agent loop — OpenAI function-calling on top of the LLM gateway.

Design goals (in order of importance):
  1. Defensibility — every tool call is audited (input, output, latency, cost),
     every run has a hard iteration + cost cap, every external action is human-
     gated by the caller (the loop only builds artefacts, it does not "send").
  2. Idempotency — repeat tool calls inside a run with identical input return
     the cached output. Lets the model re-plan without re-executing side
     effects (URL archiving, PDF generation).
  3. Honesty — we do not silently swallow failures. Tool errors propagate to
     the model as an error message so it can adapt; loop errors abort the run
     with a clear status.

No LangChain. The loop is ~150 LOC of explicit code so behaviour is grokkable
when something goes wrong at 2 AM. The LLM gateway already centralises
token + cost capture; agent_run_id stitches multi-call runs into one line
on the cost dashboard.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.database import AgentRun, ToolCallLog
from app.services import llm_gateway

logger = logging.getLogger(__name__)


# ── Public types ─────────────────────────────────────────────────────────


@dataclass
class ToolDef:
    """A tool the agent may call. `schema` is the OpenAI function spec.

    Handler signature is `(input: dict) -> Any`. Return value must be
    JSON-serialisable; the loop will encode it into a tool-response message.
    """

    name: str
    description: str
    schema: dict
    handler: Callable[[dict], Any]


@dataclass
class AgentRunResult:
    agent_run_id: str
    status: str  # completed | failed | aborted_budget | aborted_iterations
    iterations: int
    total_cost_usd: float
    final_message: str | None = None
    output: dict | None = None
    error: str | None = None
    tool_trace: list[dict] = field(default_factory=list)
    # Telemetry: per-LLM-round token + cost breakdown ("where do tokens go?").
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    rounds: list[dict] = field(default_factory=list)


# ── Defaults — chosen so a runaway agent costs at most a coffee, not a meal ──

DEFAULT_MAX_ITERATIONS = 10
DEFAULT_MAX_COST_USD = 0.50
DEFAULT_MODEL = "gpt-4o-mini"


# ── Helpers ──────────────────────────────────────────────────────────────


def _hash_input(payload: Any) -> str:
    """Deterministic hash of a tool-call input for idempotency lookup."""
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _openai_tool_spec(tool: ToolDef) -> dict:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.schema,
        },
    }


def _safe_json_dumps(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        return json.dumps({"_unserializable": True, "repr": repr(obj)})


# ── Core loop ────────────────────────────────────────────────────────────


def run_agent(
    *,
    db: Session,
    agent_name: str,
    system_prompt: str,
    user_message: str,
    tools: list[ToolDef],
    case_id: str | None = None,
    user_id: str | None = None,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    max_cost_usd: float = DEFAULT_MAX_COST_USD,
    model: str = DEFAULT_MODEL,
    input_payload: dict | None = None,
) -> AgentRunResult:
    """Drive an agent loop until the model stops requesting tool calls.

    Persists an `agent_runs` row up front so polling clients can observe
    status while the loop is still running. Every tool execution is logged
    to `tool_calls` for audit and idempotency lookup.
    """

    if not llm_gateway.is_available():
        return AgentRunResult(
            agent_run_id="",
            status="failed",
            iterations=0,
            total_cost_usd=0.0,
            error="openai_unavailable",
        )

    tools_by_name = {t.name: t for t in tools}
    openai_tools = [_openai_tool_spec(t) for t in tools]

    agent_run_id = str(uuid.uuid4())
    run = AgentRun(
        id=agent_run_id,
        agent_name=agent_name,
        user_id=user_id,
        case_id=case_id,
        status="running",
        input_json=_safe_json_dumps(input_payload or {"user_message": user_message}),
        total_iterations=0,
        total_cost_usd=0.0,
    )
    db.add(run)
    db.commit()

    messages: list[dict] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    tool_trace: list[dict] = []
    total_cost = 0.0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    rounds: list[dict] = []
    iterations = 0
    final_message: str | None = None

    try:
        for i in range(max_iterations):
            iterations = i + 1

            chat_result = llm_gateway.chat_with_tools(
                messages=messages,
                tools=openai_tools,
                model=model,
                temperature=0.2,
            )

            # Persist this LLM call to llm_usage, stitched to this agent run.
            llm_gateway.record_usage(
                db,
                chat_result,
                route=f"agent.{agent_name}",
                case_id=case_id,
                user_id=user_id,
                agent_run_id=agent_run_id,
            )
            total_cost += chat_result.estimated_cost_usd

            # Per-round telemetry: tokens + cost for this LLM call, plus which
            # tools it requested. This is the "what's slow / what's expensive"
            # data the dev telemetry panel renders.
            _usage = getattr(chat_result, "usage", None)
            _round_pt = (getattr(_usage, "prompt_tokens", 0) or 0) if _usage else 0
            _round_ct = (getattr(_usage, "completion_tokens", 0) or 0) if _usage else 0
            total_prompt_tokens += _round_pt
            total_completion_tokens += _round_ct
            rounds.append(
                {
                    "iteration": iterations,
                    "prompt_tokens": _round_pt,
                    "completion_tokens": _round_ct,
                    "cost_usd": round(chat_result.estimated_cost_usd, 6),
                    "tools": [
                        tc["name"]
                        for tc in (getattr(chat_result, "tool_calls", None) or [])
                    ],
                }
            )

            if total_cost > max_cost_usd:
                run.status = "aborted_budget"
                run.error = f"budget exceeded: ${total_cost:.4f} > ${max_cost_usd:.2f}"
                break

            if chat_result.error:
                run.status = "failed"
                run.error = chat_result.error
                break

            tool_calls = getattr(chat_result, "tool_calls", None) or []
            assistant_content = chat_result.content or ""

            # Always append the assistant message so the model sees its own
            # previous reasoning + tool-call requests in the next turn.
            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": assistant_content,
            }
            if tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": tc["arguments_raw"],
                        },
                    }
                    for tc in tool_calls
                ]
            messages.append(assistant_msg)

            if not tool_calls:
                # Model is done — no more tools requested. Treat content as final.
                final_message = assistant_content
                run.status = "completed"
                break

            # Execute every requested tool sequentially. Parallel execution is
            # a later optimisation — sequential keeps debugging trivial.
            for call in tool_calls:
                tool_name = call["name"]
                args = call["arguments"]
                tool_def = tools_by_name.get(tool_name)

                started = time.perf_counter()
                if tool_def is None:
                    tool_output: Any = {
                        "error": f"unknown tool '{tool_name}'",
                        "available_tools": list(tools_by_name.keys()),
                    }
                    err = "unknown_tool"
                    cached = False
                else:
                    input_hash = _hash_input(args)
                    # Idempotency lookup — same tool, same input, same run.
                    prior = (
                        db.query(ToolCallLog)
                        .filter_by(
                            agent_run_id=agent_run_id,
                            tool_name=tool_name,
                            input_hash=input_hash,
                            error=None,
                        )
                        .first()
                    )
                    if prior is not None and prior.output_json:
                        try:
                            tool_output = json.loads(prior.output_json)
                        except Exception:
                            tool_output = prior.output_json
                        cached = True
                        err = None
                    else:
                        try:
                            tool_output = tool_def.handler(args)
                            err = None
                            cached = False
                        except Exception as e:
                            logger.exception(
                                "tool '%s' raised in agent %s", tool_name, agent_run_id
                            )
                            tool_output = {"error": str(e)}
                            err = str(e)
                            cached = False

                latency_ms = int((time.perf_counter() - started) * 1000)

                log = ToolCallLog(
                    agent_run_id=agent_run_id,
                    tool_name=tool_name,
                    input_json=_safe_json_dumps(args),
                    output_json=_safe_json_dumps(tool_output),
                    input_hash=_hash_input(args),
                    latency_ms=latency_ms,
                    cost_usd=0.0,
                    cached=cached,
                    error=err,
                )
                db.add(log)

                tool_trace.append(
                    {
                        "tool": tool_name,
                        "input": args,
                        "output": tool_output,
                        "latency_ms": latency_ms,
                        "cached": cached,
                        "error": err,
                    }
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": _safe_json_dumps(tool_output),
                    }
                )

            # Persist progress so polling clients see live updates.
            run.total_iterations = iterations
            run.total_cost_usd = total_cost
            db.commit()

        else:
            # for-loop completed without break — hit iteration cap.
            run.status = "aborted_iterations"
            run.error = f"iteration limit hit ({max_iterations})"

        # Final bookkeeping
        run.total_iterations = iterations
        run.total_cost_usd = total_cost
        run.completed_at = datetime.utcnow()
        if run.status == "completed":
            run.output_json = _safe_json_dumps(
                {"final_message": final_message, "tool_trace": tool_trace}
            )
        db.commit()

    except Exception as e:
        logger.exception("agent loop crashed (run %s)", agent_run_id)
        run.status = "failed"
        run.error = f"loop crash: {e}"
        run.completed_at = datetime.utcnow()
        db.commit()

    return AgentRunResult(
        agent_run_id=agent_run_id,
        status=run.status,
        iterations=iterations,
        total_cost_usd=total_cost,
        total_prompt_tokens=total_prompt_tokens,
        total_completion_tokens=total_completion_tokens,
        rounds=rounds,
        final_message=final_message,
        output=(
            json.loads(run.output_json)
            if run.output_json and run.status == "completed"
            else None
        ),
        error=run.error,
        tool_trace=tool_trace,
    )
