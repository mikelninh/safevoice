"""
SafeVoice MCP server — exposes the victim-protection service layer as tools any
MCP client (Claude Desktop, Cursor, custom agents) can call.

This MVP wraps six DB-free service functions from the SafeVoice backend:

  classify              — LLM classifier (text → harassment categories + severity + applicable §)
  detect_patterns       — coordinated-attack / escalation / repeat-offender detection
  get_applicable_laws   — category × jurisdiction → list of statutes (DE/AT/CH/UK)
  check_strafantrag_frist  — statute-of-limitations calculator per § (warns on < 7 days left)
  determine_jurisdiction   — Bundesland code → responsible Staatsanwaltschaft + Rechtsgrundlage
  detect_anonymisierung_needed — flags whether the victim needs anonymisation when filing

Out of scope for v0.1 (db-coupled — they need a SQLAlchemy session and a case row):
  generate_strafanzeige_pdf   — court-ready Strafanzeige with hashes/timestamps
  draft_netzdg_email          — RFC 2822 NetzDG complaint per platform
  build_onlinewache_text      — Polizei online-form payload

The pattern is identical to gitlaw-mcp: thin MCP wrapper over a well-tested
service layer. The "intelligence" lives in backend/app/services/; this server
exposes it.
"""

from __future__ import annotations

import json as _json
import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

# Make the SafeVoice backend importable. Layout:
#   /safevoice/
#     ├── backend/app/services/*.py   ← we import these
#     ├── backend/app/models/*.py
#     └── safevoice_mcp/server.py     ← we are here
ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from mcp.server.fastmcp import FastMCP  # type: ignore  # noqa: E402

# Services (DB-free entry points only)
from app.models.evidence import EvidenceItem  # type: ignore  # noqa: E402
from app.services.classifier import (  # type: ignore  # noqa: E402
    ClassifierUnavailableError,
    classify as _classify_service,
)
from app.services.court_prep_tools import (  # type: ignore  # noqa: E402
    check_strafantrag_frist as _check_frist,
    detect_anonymisierung_needed as _detect_anonym,
    determine_jurisdiction as _determine_jur,
)
from app.services.law_mapper import (  # type: ignore  # noqa: E402
    get_laws_for_country,
)
from app.services.pattern_detector import detect_patterns as _detect_patterns  # type: ignore  # noqa: E402


log = logging.getLogger("safevoice_mcp")


# ── Structured logging — one line per tool call, parseable as JSON ────────


def _log_json(level: int, **fields: Any) -> None:
    fields.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S"))
    log.log(level, _json.dumps(fields, ensure_ascii=False))


def _traced(tool_name: str):
    """Wrap a tool function with request-id + latency logging + clean error envelope."""

    def decorator(fn):
        def wrapper(*args, **kwargs):
            request_id = uuid.uuid4().hex[:12]
            t0 = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                _log_json(
                    logging.INFO,
                    msg=f"tool.{tool_name}",
                    request_id=request_id,
                    tool=tool_name,
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                    status="ok",
                    error=None,
                )
                return result
            except ClassifierUnavailableError as e:
                _log_json(
                    logging.WARNING,
                    msg=f"tool.{tool_name}",
                    request_id=request_id,
                    tool=tool_name,
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                    status="unavailable",
                    error=str(e),
                )
                return {"error": "classifier_unavailable", "message": str(e)}
            except Exception as e:  # pragma: no cover — defensive
                _log_json(
                    logging.ERROR,
                    msg=f"tool.{tool_name}",
                    request_id=request_id,
                    tool=tool_name,
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                    status="error",
                    error=f"{type(e).__name__}: {e}",
                )
                return {"error": "internal_error", "message": str(e)}

        wrapper.__name__ = fn.__name__
        wrapper.__doc__ = fn.__doc__
        return wrapper

    return decorator


# ── MCP server construction ───────────────────────────────────────────────


mcp = FastMCP(
    "safevoice",
    host=os.getenv("FASTMCP_HOST", "0.0.0.0"),
    port=int(os.getenv("FASTMCP_PORT", os.getenv("PORT", "8002"))),
)


# Plain HTTP health for hosted-deploy probes (mirrors gitlaw-mcp pattern).
try:
    from starlette.responses import JSONResponse  # type: ignore

    @mcp.custom_route("/health", methods=["GET"])
    async def _health(_request):  # noqa: ANN001
        return JSONResponse({"status": "ok", "service": "safevoice-mcp"})
except Exception:  # pragma: no cover
    pass


# ── Tool 1: classify ─────────────────────────────────────────────────────


@mcp.tool()
@_traced("classify")
def classify(
    text: str,
    victim_context: str | None = None,
    jurisdiction: str = "DE",
    user_lang: str = "de",
) -> dict[str, Any]:
    """
    Classify a piece of evidence (a message, post, comment) into harassment
    categories, severity, and applicable statutes.

    Args:
      text: the content to classify (one message / one screenshot transcription / one post body).
      victim_context: optional free-text context like "ex-partner after breakup" or
                      "anonymous account following several weeks". Steers severity + § mapping.
      jurisdiction: ISO country code — "DE" (default), "AT", "CH", "UK". Determines which legal
                    framework to map categories to.
      user_lang: output language — "de" (default) or "en". Affects narrative summary only;
                 categories and § are always identifiers.

    Returns:
      A ClassificationResult dict with:
        categories[]            — e.g. ["bedrohung", "beleidigung"]
        severity                — "low" | "medium" | "high" | "critical"
        applicable_laws[]       — statute codes like ["stgb:241", "stgb:185"]
        summary, summary_de     — short prose explanations
        confidence              — 0.0–1.0
        explanation             — why the model picked these categories (auditable)

    Requires OPENAI_API_KEY. If unavailable, returns {"error": "classifier_unavailable", ...}
    instead of falling back to a weaker classifier — a weak classification on harassment
    evidence is more harmful than an honest "try again".
    """
    result = _classify_service(
        text,
        victim_context=victim_context,
        jurisdiction=jurisdiction,
        user_lang=user_lang,
    )
    # ClassificationResult is a Pydantic model — convert to plain dict for MCP transport.
    return result.model_dump(mode="json")


# ── Tool 2: detect_patterns ──────────────────────────────────────────────


@mcp.tool()
@_traced("detect_patterns")
def detect_patterns(evidence_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Detect coordinated-attack, escalation, and repeat-offender patterns across multiple
    pieces of evidence — the patterns no single classification can see.

    Args:
      evidence_items: a list of evidence dicts. Each must include all of:
        - id              (string)
        - url             (string — source URL of the post / message)
        - captured_at     (ISO 8601 timestamp)
        - author_username (string — handle / username / "unknown")
        - content_text    (string — the actual text being assessed)
        - content_hash    (string — SHA-256 or similar; for evidence integrity)
        Optional: platform, author_display_name, content_type, archived_url,
        screenshot_path, classification.

    Returns:
      A list of PatternFlag dicts, each with:
        type            — "coordinated_attack" | "escalation" | "repeat_offender"
        severity        — "low" | "medium" | "high" | "critical"
        evidence_count  — how many items contributed to the pattern
        description     — human-readable explanation (English)
        description_de  — German equivalent

      Empty list means no patterns detected — that's a valid answer, not an error.

    Pure-Python heuristics: no LLM call, sub-millisecond per item. Pair with classify()
    to get per-item severity first, then detect_patterns() across the case.
    """
    items = [EvidenceItem.model_validate(d) for d in evidence_items]
    flags = _detect_patterns(items)
    return [f.model_dump(mode="json") for f in flags]


# ── Tool 3: get_applicable_laws ──────────────────────────────────────────


@mcp.tool()
@_traced("get_applicable_laws")
def get_applicable_laws(
    categories: list[str],
    country: str = "DE",
    severity: str = "medium",
) -> list[dict[str, Any]]:
    """
    Map harassment categories to the specific statutes that apply in a given jurisdiction.

    Args:
      categories: e.g. ["bedrohung", "beleidigung", "stalking"]
      country: ISO code — "DE" (default), "AT", "CH", "UK"
      severity: "low" | "medium" | "high" | "critical" — gates which statutes apply
                (e.g. § 241 StGB Bedrohung kicks in only at "medium"+).

    Returns:
      A list of statute dicts:
        code           — short identifier ("stgb:241")
        full_reference — "§ 241 StGB" (human-readable)
        title          — "Bedrohung"
        description    — what it covers, plain language
        max_penalty    — max sanction
        url            — official gesetze-im-internet.de link (when known)

    This is the bridge between "what happened" (categories) and "what you can do about it"
    (statutes). Bilingual + multi-jurisdiction by design.
    """
    laws = get_laws_for_country(country, categories, severity)
    return [law.model_dump(mode="json") for law in laws]


# ── Tool 4: check_strafantrag_frist ──────────────────────────────────────


@mcp.tool()
@_traced("check_strafantrag_frist")
def check_strafantrag_frist(
    earliest_evidence_iso: str,
    applicable_laws: list[str],
) -> dict[str, Any]:
    """
    Compute deadlines for Strafantrag filings per § (statute of limitations clock).

    For Antragsdelikte (offences requiring the victim's formal request to prosecute),
    German law sets a 3-month window from the date of first Kenntnisnahme (knowledge).
    Miss it and the offence is no longer prosecutable on Strafantrag grounds.

    Args:
      earliest_evidence_iso: ISO 8601 timestamp of the earliest evidence in the case
                             — treated as the date of first knowledge.
      applicable_laws: list of statute codes like ["stgb:185", "stgb:241"] (from
                       get_applicable_laws or classify).

    Returns:
      {
        "anchor_utc": "2026-05-01T00:00:00+00:00",
        "applicable_antragsdelikte": [
          {
            "law": "stgb:185",
            "frist_months": 3,
            "deadline_utc": "2026-07-30T00:00:00+00:00",
            "days_left": 62,
            "expired": false,
            "urgent": false
          },
          ...
        ],
        "warning_level": "ok" | "urgent" | "expired",
        "summary": "Alle relevanten Antragsfristen liegen in der Zukunft."
      }

    `urgent: true` when < 7 days remain; `expired: true` past the deadline. The intended UX:
    an agent surfaces the urgency proactively — "you have 4 days left to file on § 185, act now."

    Laws without a known Antragsfrist are silently skipped (no error). The
    `applicable_antragsdelikte` list contains only laws the calculator recognises.
    """
    return _check_frist(
        {
            "earliest_evidence_iso": earliest_evidence_iso,
            "applicable_laws": applicable_laws,
        }
    )


# ── Tool 5: determine_jurisdiction ───────────────────────────────────────


@mcp.tool()
@_traced("determine_jurisdiction")
def determine_jurisdiction(bundesland_code: str) -> dict[str, Any]:
    """
    Map a Bundesland code to the responsible Staatsanwaltschaft (Public Prosecutor's
    Office) for filing a Strafanzeige.

    Args:
      bundesland_code: ISO-3166-2 region code — "BE" (Berlin), "BY" (Bayern), "NW"
                       (Nordrhein-Westfalen), etc.

    Returns:
      {
        "bundesland_code": "BE",
        "staatsanwaltschaft": { "name": ..., "address": ..., "email": ..., "phone": ... },
        "rechtsgrundlage": "§ 7 StPO (Gerichtsstand des Wohnsitzes)"
      }

    Or, if the code is unknown:
      { "error": "unknown bundesland_code 'XX'", "available": [...] }

    Pure lookup — no network call, no LLM. The Staatsanwaltschaft contact table is
    maintained in the SafeVoice backend.
    """
    return _determine_jur({"bundesland_code": bundesland_code})


# ── Tool 6: detect_anonymisierung_needed ─────────────────────────────────


@mcp.tool()
@_traced("detect_anonymisierung_needed")
def detect_anonymisierung_needed(
    categories: list[str],
    severity: str = "medium",
) -> dict[str, Any]:
    """
    Flag whether the victim's identity should be anonymised in the filing (§ 68a StPO
    Opferschutz, Zeugenschutzprogramm-Erwägungen).

    Certain category × severity combinations — e.g. stalking with critical severity,
    sexual harassment, threats from organised groups — strongly indicate the victim
    should not be named publicly in the Strafanzeige header. This tool surfaces that
    recommendation so the drafting agent can apply the right template.

    Args:
      categories: list of harassment categories from classify().
      severity:   overall case severity.

    Returns:
      {
        "needed": true | false,
        "rechtsgrundlage": "§ 68a StPO" | null,
        "begruendung": "<plain-German explanation of why / why not>",
        "triggering_categories": ["stalking", ...]   # the categories that fed the decision
      }
    """
    return _detect_anonym({"categories": categories, "severity": severity})


# ── Entry point ──────────────────────────────────────────────────────────


def main() -> None:
    """Transport: stdio by default (Claude Desktop, Cursor), MCP_TRANSPORT=sse for hosted."""
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(message)s",
        stream=sys.stderr,
    )
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport in ("sse", "streamable-http"):
        mcp.run(transport=transport)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
