"""Central LLM gateway — every OpenAI call goes through here so we capture
token usage and estimated USD cost in one place. Mirrors the pattern in
GitLaw so a cross-project cost dashboard can read from both DBs.

Stays minimal on purpose:
- No retry / no streaming / no provider abstraction.
- `chat()` for free-form completions, `parse()` for Structured Outputs.
- Persistence is opt-in via `record_usage()` — gateway never writes on its
  own so callers control the request-scoped DB session.
"""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from typing import Any

try:
    from openai import OpenAI

    _openai_installed = True
except ImportError:
    _openai_installed = False

logger = logging.getLogger(__name__)


# OpenAI pricing 2026-05-18 — USD per 1M tokens. Bump alongside any
# OpenAI price-page change. Sibling GitLaw table is the source of truth;
# keep these two in sync.
_PRICE_TABLE: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
}


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class ChatResult:
    content: str | None
    model: str
    usage: Usage
    estimated_cost_usd: float
    request_id: str
    # Raw SDK objects so callers needing `.parsed` / `.refusal` aren't forced
    # to re-issue the call. None for non-parse calls.
    raw_message: Any = None
    refusal: str | None = None
    parsed: Any = None
    error: str | None = field(default=None)
    # Populated by `chat_with_tools()` when the model returned tool calls.
    # Each entry: {"id": str, "name": str, "arguments": dict, "arguments_raw": str}
    tool_calls: list[dict] = field(default_factory=list)


def is_available() -> bool:
    return _openai_installed and bool(os.environ.get("OPENAI_API_KEY"))


def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    price = _PRICE_TABLE.get(model)
    if price is None:
        return 0.0
    in_per_m, out_per_m = price
    return (prompt_tokens / 1_000_000) * in_per_m + (
        completion_tokens / 1_000_000
    ) * out_per_m


def _new_request_id() -> str:
    return uuid.uuid4().hex[:12]


def _client() -> "OpenAI | None":
    if not _openai_installed:
        return None
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return None
    return OpenAI(api_key=key)


def _extract_usage(completion: Any) -> Usage:
    u = getattr(completion, "usage", None)
    if u is None:
        return Usage()
    return Usage(
        prompt_tokens=getattr(u, "prompt_tokens", 0) or 0,
        completion_tokens=getattr(u, "completion_tokens", 0) or 0,
        total_tokens=getattr(u, "total_tokens", 0) or 0,
    )


def chat(
    messages: list[dict],
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    max_tokens: int | None = None,
    response_format: dict | None = None,
) -> ChatResult:
    """Raw chat completion. Use `parse()` when the caller has a Pydantic schema."""
    request_id = _new_request_id()
    client = _client()
    if client is None:
        return ChatResult(
            content=None,
            model=model,
            usage=Usage(),
            estimated_cost_usd=0.0,
            request_id=request_id,
            error="openai_unavailable",
        )

    try:
        kwargs: dict[str, Any] = {
            "model": model,
            "temperature": temperature,
            "messages": messages,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if response_format is not None:
            kwargs["response_format"] = response_format

        completion = client.chat.completions.create(**kwargs)
        msg = completion.choices[0].message
        usage = _extract_usage(completion)
        cost = _estimate_cost(model, usage.prompt_tokens, usage.completion_tokens)
        return ChatResult(
            content=msg.content,
            model=model,
            usage=usage,
            estimated_cost_usd=cost,
            request_id=request_id,
            raw_message=msg,
        )
    except Exception as e:
        logger.warning("llm_gateway.chat failed [%s]: %s", request_id, e)
        return ChatResult(
            content=None,
            model=model,
            usage=Usage(),
            estimated_cost_usd=0.0,
            request_id=request_id,
            error=str(e),
        )


def parse(
    messages: list[dict],
    *,
    response_format: Any,
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    max_tokens: int | None = None,
) -> ChatResult:
    """OpenAI Structured Outputs — `response_format` is a Pydantic class."""
    request_id = _new_request_id()
    client = _client()
    if client is None:
        return ChatResult(
            content=None,
            model=model,
            usage=Usage(),
            estimated_cost_usd=0.0,
            request_id=request_id,
            error="openai_unavailable",
        )

    try:
        kwargs: dict[str, Any] = {
            "model": model,
            "temperature": temperature,
            "messages": messages,
            "response_format": response_format,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        completion = client.chat.completions.parse(**kwargs)
        msg = completion.choices[0].message
        usage = _extract_usage(completion)
        cost = _estimate_cost(model, usage.prompt_tokens, usage.completion_tokens)
        return ChatResult(
            content=msg.content,
            model=model,
            usage=usage,
            estimated_cost_usd=cost,
            request_id=request_id,
            raw_message=msg,
            refusal=getattr(msg, "refusal", None),
            parsed=getattr(msg, "parsed", None),
        )
    except Exception as e:
        logger.warning("llm_gateway.parse failed [%s]: %s", request_id, e)
        return ChatResult(
            content=None,
            model=model,
            usage=Usage(),
            estimated_cost_usd=0.0,
            request_id=request_id,
            error=str(e),
        )


def chat_with_tools(
    messages: list[dict],
    *,
    tools: list[dict],
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    tool_choice: str | dict = "auto",
) -> ChatResult:
    """Chat completion with OpenAI function-calling.

    Returns a `ChatResult` whose `tool_calls` field is populated when the
    model requested one or more tools. `arguments` is parsed JSON;
    `arguments_raw` is the original string (needed when echoing the
    assistant message back to the API).
    """
    request_id = _new_request_id()
    client = _client()
    if client is None:
        return ChatResult(
            content=None,
            model=model,
            usage=Usage(),
            estimated_cost_usd=0.0,
            request_id=request_id,
            error="openai_unavailable",
        )

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            tools=tools,
            tool_choice=tool_choice,
        )
        msg = completion.choices[0].message
        usage = _extract_usage(completion)
        cost = _estimate_cost(model, usage.prompt_tokens, usage.completion_tokens)

        raw_tool_calls = getattr(msg, "tool_calls", None) or []
        parsed_tool_calls: list[dict] = []
        import json as _json

        for tc in raw_tool_calls:
            args_raw = getattr(tc.function, "arguments", "") or "{}"
            try:
                args = _json.loads(args_raw)
            except Exception:
                args = {"_unparseable": True, "raw": args_raw}
            parsed_tool_calls.append(
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": args,
                    "arguments_raw": args_raw,
                }
            )

        return ChatResult(
            content=msg.content,
            model=model,
            usage=usage,
            estimated_cost_usd=cost,
            request_id=request_id,
            raw_message=msg,
            tool_calls=parsed_tool_calls,
        )
    except Exception as e:
        logger.warning("llm_gateway.chat_with_tools failed [%s]: %s", request_id, e)
        return ChatResult(
            content=None,
            model=model,
            usage=Usage(),
            estimated_cost_usd=0.0,
            request_id=request_id,
            error=str(e),
        )


def record_usage(
    db,
    result: ChatResult,
    *,
    route: str,
    case_id: str | None = None,
    user_id: str | None = None,
    agent_run_id: str | None = None,
) -> None:
    """Append one row to `llm_usage`. Best-effort — never raises, since a
    telemetry failure must not break the actual request path."""
    try:
        from app.database import LLMUsage

        row = LLMUsage(
            case_id=case_id,
            user_id=user_id,
            route=route,
            model=result.model,
            prompt_tokens=result.usage.prompt_tokens,
            completion_tokens=result.usage.completion_tokens,
            total_tokens=result.usage.total_tokens,
            estimated_cost_usd=result.estimated_cost_usd,
            request_id=result.request_id,
            agent_run_id=agent_run_id,
        )
        db.add(row)
        db.commit()
    except Exception as e:
        logger.warning("llm_gateway.record_usage failed [%s]: %s", result.request_id, e)
        try:
            db.rollback()
        except Exception:
            pass
