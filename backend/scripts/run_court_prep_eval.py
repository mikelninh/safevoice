"""
Eval runner for the Court-Prep Agent.

Seeds a temp case per eval case (from `evals/agent_court_prep.json`), runs the
real agent against it (real LLM, real tools), and checks the assertions.

Usage:
  OPENAI_API_KEY=sk-... python3 backend/scripts/run_court_prep_eval.py
  OPENAI_API_KEY=sk-... python3 backend/scripts/run_court_prep_eval.py --limit 1

Honest about cost: each case is ~$0.05-0.30 real OpenAI spend. Default runs
all 3 cases (~$0.50). Pass --limit to constrain.

Exit code: 0 if every case passes, 1 if any fails. Suitable for CI gating
on agent prompt changes.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.database import (  # noqa: E402
    Case as DBCase,
    Category as DBCategory,
    Classification as DBClassification,
    EvidenceItem as DBEvidence,
    Law as DBLaw,
    SessionLocal,
    init_db,
    seed_categories_and_laws,
)
from app.services.court_prep_agent import run_court_prep  # noqa: E402
from app.services.evidence import hash_content  # noqa: E402


EVAL_FILE = ROOT / "evals" / "agent_court_prep.json"


def _platform_to_url(platform: str, idx: int) -> str:
    base = {
        "instagram": "https://instagram.com/p/eval",
        "facebook": "https://facebook.com/eval/posts/",
        "tiktok": "https://www.tiktok.com/@eval/video/",
        "x": "https://x.com/eval/status/",
        "twitter": "https://twitter.com/eval/status/",
        "youtube": "https://youtube.com/watch?v=eval",
    }.get(platform.lower(), "https://example.com/post/")
    return f"{base}{idx}"


def seed_case(db, case_id: str, seed: dict) -> None:
    """Insert one synthetic case matching the eval seed spec."""

    now = datetime.now(timezone.utc) - timedelta(days=seed.get("evidence_days_ago", 5))

    case = DBCase(
        id=case_id,
        title=f"Eval case {case_id}",
        status="open",
        overall_severity=seed["severity"],
        created_at=now,
        updated_at=now,
    )
    db.add(case)
    db.flush()

    cats = db.query(DBCategory).filter(DBCategory.id.in_(seed["categories"])).all()
    laws = []
    for law_key in seed.get("laws", []):
        code, section = law_key.split(":", 1)
        l_row = db.query(DBLaw).filter_by(code=code, section=section).first()
        if l_row:
            laws.append(l_row)

    for i, platform in enumerate(seed["platforms"]):
        url = _platform_to_url(platform, i)
        text = f"[Eval evidence for {case_id} on {platform}]"
        ev = DBEvidence(
            id=f"{case_id}-ev-{i}",
            case_id=case_id,
            content_type="text",
            raw_content=text,
            content_hash=hash_content(text),
            platform=platform,
            source_url=url,
            timestamp_utc=now,
        )
        db.add(ev)
        db.flush()

        cls = DBClassification(
            id=f"{case_id}-cls-{i}",
            evidence_item_id=ev.id,
            severity=seed["severity"],
            confidence=0.9,
            classifier_tier=1,
            summary_de=f"Eval-Klassifikation für {platform}.",
        )
        db.add(cls)
        db.flush()
        for c in cats:
            cls.categories.append(c)
        for l in laws:
            cls.laws.append(l)

    db.commit()


def check_assertions(result, expectations: dict, artefacts: dict) -> list[str]:
    """Return a list of failure messages — empty list means pass."""
    errs: list[str] = []

    tools_called = {c["tool"] for c in result.tool_trace}
    for required in expectations.get("tools_called_at_least", []):
        if required not in tools_called:
            errs.append(f"tool '{required}' was never called")

    expected_levels = expectations.get("frist_warning_level_in")
    if expected_levels and artefacts.get("frist"):
        actual = artefacts["frist"].get("warning_level")
        if actual not in expected_levels:
            errs.append(
                f"frist_warning_level: expected one of {expected_levels}, got '{actual}'"
            )

    if "anonymisierung_needed" in expectations and artefacts.get("anonymisierung"):
        exp = expectations["anonymisierung_needed"]
        got = artefacts["anonymisierung"].get("needed")
        if exp != got:
            errs.append(f"anonymisierung_needed: expected {exp}, got {got}")

    contains = expectations.get("jurisdiction_name_contains")
    if contains and artefacts.get("jurisdiction"):
        name = artefacts["jurisdiction"]["staatsanwaltschaft"]["name"]
        if contains not in name:
            errs.append(
                f"jurisdiction: expected name to contain '{contains}', got '{name}'"
            )

    if expectations.get("pdf_present") and not artefacts.get("strafanzeige_pdf_base64"):
        errs.append("expected Strafanzeige PDF artefact, got none")

    min_emls = expectations.get("netzdg_eml_count_at_least")
    if min_emls is not None:
        got = len(artefacts.get("netzdg_emls") or [])
        if got < min_emls:
            errs.append(f"netzdg_eml_count: expected ≥{min_emls}, got {got}")

    min_arch = expectations.get("archived_urls_count_at_least")
    if min_arch is not None:
        got = len(artefacts.get("archived_urls") or [])
        if got < min_arch:
            errs.append(f"archived_urls_count: expected ≥{min_arch}, got {got}")

    if (
        expectations.get("max_iterations")
        and result.iterations > expectations["max_iterations"]
    ):
        errs.append(
            f"iterations: expected ≤{expectations['max_iterations']}, got {result.iterations}"
        )
    if (
        expectations.get("max_cost_usd")
        and result.total_cost_usd > expectations["max_cost_usd"]
    ):
        errs.append(
            f"cost: expected ≤${expectations['max_cost_usd']:.2f}, got ${result.total_cost_usd:.4f}"
        )

    return errs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY required for live eval run.", file=sys.stderr)
        return 2

    init_db()
    seed_categories_and_laws()

    spec = json.loads(EVAL_FILE.read_text(encoding="utf-8"))
    cases = spec["cases"]
    if args.limit:
        cases = cases[: args.limit]

    from app.services.court_prep_agent import summarise_artefacts

    pass_count = 0
    fail_count = 0
    total_cost = 0.0

    for c in cases:
        case_id = c["id"]
        print(f"\n=== {case_id}: {c['name']} ===")
        db = SessionLocal()
        try:
            # Idempotent re-seed: delete if exists
            existing = db.query(DBCase).filter_by(id=case_id).first()
            if existing:
                for ev in list(existing.evidence_items):
                    if ev.classification:
                        db.delete(ev.classification)
                    db.delete(ev)
                db.delete(existing)
                db.commit()
            seed_case(db, case_id, c["input"]["case_seed"])

            result = run_court_prep(
                db=db,
                case_id=case_id,
                victim_name=c["input"].get("victim_name"),
                bundesland_code=c["input"].get("bundesland_code"),
            )
            artefacts = summarise_artefacts(result.tool_trace)
            total_cost += result.total_cost_usd

            errs = check_assertions(result, c["expectations"], artefacts)
            if not errs:
                print(
                    f"  PASS  · {result.iterations} iter · ${result.total_cost_usd:.4f}"
                )
                pass_count += 1
            else:
                print(
                    f"  FAIL  · {result.iterations} iter · ${result.total_cost_usd:.4f}"
                )
                for e in errs:
                    print(f"        - {e}")
                fail_count += 1
        finally:
            db.close()

    print(f"\nTotal: {pass_count}/{len(cases)} pass · ${total_cost:.4f} spent")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
