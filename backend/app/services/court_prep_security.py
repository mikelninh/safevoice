"""Deterministic security boundary for the SafeVoice Court-Prep agent.

The model may choose *which* declared preparation tool to call, but it may not
change the case being operated on or invent network targets. This module wraps
the existing ToolDef handlers so authority is derived from the authenticated
request context, not from model-generated arguments.

Security invariants:
- tools with a ``case_id`` parameter may only use the active case id;
- ``re_archive_urls`` may only archive source URLs already attached to the
  active case in the database;
- the stored evidence platform wins over any model-provided platform label;
- any scope violation fails closed before the underlying handler executes.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable

from sqlalchemy.orm import Session

from app.database import Case as DBCase


def _case_scope_error(*, active_case_id: str, requested_case_id: Any) -> dict[str, Any]:
    return {
        "ok": False,
        "error": "case_scope_violation",
        "active_case_id": active_case_id,
        "requested_case_id": requested_case_id,
    }


def _wrap_case_id_handler(handler, *, case_id: str):
    def scoped(args: dict) -> Any:
        requested = args.get("case_id")
        if requested != case_id:
            return _case_scope_error(
                active_case_id=case_id,
                requested_case_id=requested,
            )
        return handler(args)

    return scoped


def _wrap_archive_handler(handler, *, db: Session, case_id: str):
    def scoped(args: dict) -> Any:
        case = db.query(DBCase).filter_by(id=case_id).first()
        if case is None:
            return {
                "attempted": 0,
                "succeeded": 0,
                "results": [],
                "error": "case_scope_not_found",
                "active_case_id": case_id,
            }

        allowed: dict[str, str] = {
            ev.source_url: (ev.platform or "unknown")
            for ev in case.evidence_items
            if ev.source_url
        }
        requested_items = args.get("urls") or []
        blocked_urls = [
            (item.get("url") or "")
            for item in requested_items
            if (item.get("url") or "") not in allowed
        ]
        if blocked_urls:
            return {
                "attempted": 0,
                "succeeded": 0,
                "results": [],
                "error": "archive_url_outside_case_scope",
                "active_case_id": case_id,
                "blocked_urls": blocked_urls,
            }

        # Do not trust a model-provided platform label. Reconstruct the exact
        # archive request from database-backed evidence metadata.
        sanitized = [
            {
                "url": item.get("url") or "",
                "platform": allowed[item.get("url") or ""],
            }
            for item in requested_items
        ]
        return handler({"urls": sanitized})

    return scoped


def bind_court_prep_tools(
    *,
    db: Session,
    case_id: str,
    tools: Iterable[Any],
) -> list[Any]:
    """Return ToolDefs whose authority is bound to one active case.

    ``ToolDef`` is a dataclass, so ``dataclasses.replace`` preserves the
    published name/description/schema while swapping only the executable
    handler. Pure calculation tools remain unchanged.
    """

    bound = []
    for tool in tools:
        handler = tool.handler
        properties = (tool.schema or {}).get("properties") or {}

        if tool.name == "re_archive_urls":
            handler = _wrap_archive_handler(handler, db=db, case_id=case_id)
        elif "case_id" in properties:
            handler = _wrap_case_id_handler(handler, case_id=case_id)

        bound.append(replace(tool, handler=handler))

    return bound
