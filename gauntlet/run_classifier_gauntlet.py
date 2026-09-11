#!/usr/bin/env python3
"""SafeVoice classifier Gauntlet.

Default mode is hermetic and verifies the safety contract + frozen 35-case corpus.
`--live` runs the production LLM classifier against the frozen cases when an API
key is intentionally provided. No fallback classifier is ever substituted.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "evals" / "harassment_eval_set.json"
CLASSIFIER = ROOT / "backend" / "app" / "services" / "classifier.py"
ALLOWED_SEVERITY = {"low", "medium", "high", "critical"}


def structural_gate() -> dict:
    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    cases = data["cases"]
    ids = [c["id"] for c in cases]
    assert len(cases) >= 35, "frozen safety corpus unexpectedly shrank"
    assert len(ids) == len(set(ids)), "duplicate case ids"
    for case in cases:
        assert case["expected_severity"] in ALLOWED_SEVERITY
        required = set(case["expected_law_codes"])
        forbidden = set(case["forbidden_law_codes"])
        assert not required & forbidden, f"contradictory law labels: {case['id']}"

    source = CLASSIFIER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    classify_fn = next(
        n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "classify"
    )
    classify_src = ast.get_source_segment(source, classify_fn) or ""

    # Fail-closed is a product safety property: production classify() must not
    # silently call the deprecated regex fallback when the LLM is unavailable.
    assert "ClassifierUnavailableError" in classify_src, "missing fail-closed classifier error"
    assert "classify_regex(" not in classify_src, "production classifier silently falls back to regex"
    assert "llm_available" in classify_src, "production path no longer checks LLM availability"

    return {
        "mode": "structural",
        "cases": len(cases),
        "hard_gates": {
            "frozen_corpus_integrity": "PASS",
            "no_required_forbidden_overlap": "PASS",
            "llm_fail_closed": "PASS",
            "no_regex_fallback": "PASS",
        },
        "decision": "PASS",
    }


def _value(x):
    return str(getattr(x, "value", x))


def live_eval(limit: int | None = None) -> dict:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required for --live; CI never invents one")

    sys.path.insert(0, str(ROOT / "backend"))
    from app.services.classifier import classify  # noqa: PLC0415

    cases = json.loads(CORPUS.read_text(encoding="utf-8"))["cases"]
    if limit:
        cases = cases[:limit]

    severity_ok = category_hits = category_total = law_hits = law_total = 0
    forbidden_violations = []
    rows = []
    for case in cases:
        result = classify(case["text"])
        severity = _value(result.severity).lower()
        categories = {_value(c).lower() for c in result.categories}
        laws = {str(l.paragraph) for l in result.applicable_laws}

        s_ok = severity == case["expected_severity"]
        severity_ok += int(s_ok)

        expected_categories = {str(c).lower() for c in case["expected_categories"]}
        category_hits += len(expected_categories & categories)
        category_total += len(expected_categories)

        expected_laws = set(case["expected_law_codes"])
        law_hits += len(expected_laws & laws)
        law_total += len(expected_laws)

        bad = sorted(set(case["forbidden_law_codes"]) & laws)
        if bad:
            forbidden_violations.append({"id": case["id"], "laws": bad})

        rows.append({"id": case["id"], "severity_ok": s_ok, "forbidden": bad})

    n = len(cases)
    metrics = {
        "n": n,
        "severity_accuracy": round(severity_ok / n, 3) if n else 0,
        "category_recall": round(category_hits / category_total, 3) if category_total else 0,
        "required_law_recall": round(law_hits / law_total, 3) if law_total else 0,
        "forbidden_law_violations": len(forbidden_violations),
    }
    decision = "REVERT" if forbidden_violations else "BASELINE_MEASURED"
    return {"mode": "live-production-llm", "metrics": metrics, "decision": decision, "violations": forbidden_violations, "rows": rows}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    result = live_eval(args.limit) if args.live else structural_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
