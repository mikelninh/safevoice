#!/usr/bin/env python3
"""
SafeVoice harassment classifier eval runner.

Runs the production classifier (classifier_llm_v2.classify_with_llm) against
every case in evals/harassment_eval_set.json and scores four dimensions per case:

  - severity_match   — exact match on expected_severity
  - categories_ok    — all expected_categories are present in the result (subset)
  - laws_present     — all expected_law_codes are present (subset)
  - forbidden_absent — none of forbidden_law_codes appear (false-positive guard)

A case "passes" only if all four are true. Aggregates per-category and overall.

Output: docs/notebooks/eval-results.md (markdown report) + .json (raw results).

Usage:
  cd /Users/mikel/safevoice
  source backend/venv/bin/activate
  python scripts/run_eval.py
"""

from __future__ import annotations

import os
import sys
import time
import json
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, asdict

# Load .env from repo root
def _load_env():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            os.environ.setdefault(k.strip(), v)

_load_env()

# Make backend importable so we use the actual production classifier
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.classifier_llm_v2 import classify_with_llm, PROMPT_VERSION


@dataclass
class CaseResult:
    id: str
    category: str
    text: str
    expected_severity: str
    got_severity: str | None
    expected_categories: list[str]
    got_categories: list[str]
    expected_laws: list[str]
    forbidden_laws: list[str]
    got_laws: list[str]
    severity_match: bool
    categories_ok: bool
    laws_present: bool
    forbidden_absent: bool
    passed: bool
    latency_ms: int
    error: str | None = None


def run_one(case: dict) -> CaseResult:
    t0 = time.time()
    try:
        result = classify_with_llm(
            case["text"],
            victim_context=case.get("victim_context"),
        )
    except Exception as e:
        return CaseResult(
            id=case["id"], category=case["category"], text=case["text"],
            expected_severity=case["expected_severity"], got_severity=None,
            expected_categories=case["expected_categories"], got_categories=[],
            expected_laws=case["expected_law_codes"], forbidden_laws=case.get("forbidden_law_codes", []),
            got_laws=[], severity_match=False, categories_ok=False, laws_present=False,
            forbidden_absent=False, passed=False, latency_ms=int((time.time() - t0) * 1000),
            error=str(e)[:200],
        )

    elapsed = int((time.time() - t0) * 1000)
    if result is None:
        return CaseResult(
            id=case["id"], category=case["category"], text=case["text"],
            expected_severity=case["expected_severity"], got_severity=None,
            expected_categories=case["expected_categories"], got_categories=[],
            expected_laws=case["expected_law_codes"], forbidden_laws=case.get("forbidden_law_codes", []),
            got_laws=[], severity_match=False, categories_ok=False, laws_present=False,
            forbidden_absent=False, passed=False, latency_ms=elapsed,
            error="classifier returned None (no API key, refusal, or parse failure)",
        )

    got_severity = result.severity.value if hasattr(result.severity, "value") else str(result.severity)
    got_categories = [c.value if hasattr(c, "value") else str(c) for c in result.categories]
    got_laws = [l.paragraph for l in result.applicable_laws]

    expected_cats = set(case["expected_categories"])
    expected_laws_set = set(case["expected_law_codes"])
    forbidden = set(case.get("forbidden_law_codes", []))

    severity_match = got_severity == case["expected_severity"]
    categories_ok = expected_cats.issubset(set(got_categories))
    laws_present = expected_laws_set.issubset(set(got_laws))
    forbidden_absent = forbidden.isdisjoint(set(got_laws))
    passed = severity_match and categories_ok and laws_present and forbidden_absent

    return CaseResult(
        id=case["id"], category=case["category"], text=case["text"],
        expected_severity=case["expected_severity"], got_severity=got_severity,
        expected_categories=case["expected_categories"], got_categories=got_categories,
        expected_laws=case["expected_law_codes"], forbidden_laws=case.get("forbidden_law_codes", []),
        got_laws=got_laws, severity_match=severity_match, categories_ok=categories_ok,
        laws_present=laws_present, forbidden_absent=forbidden_absent, passed=passed,
        latency_ms=elapsed,
    )


def write_markdown(results: list[CaseResult], corpus_meta: dict, out_path: Path):
    by_category: dict[str, list[CaseResult]] = defaultdict(list)
    for r in results:
        by_category[r.category].append(r)

    n = len(results)
    n_passed = sum(1 for r in results if r.passed)
    n_severity = sum(1 for r in results if r.severity_match)
    n_categories = sum(1 for r in results if r.categories_ok)
    n_laws_present = sum(1 for r in results if r.laws_present)
    n_forbidden_absent = sum(1 for r in results if r.forbidden_absent)
    avg_lat = int(sum(r.latency_ms for r in results) / n) if n else 0

    lines: list[str] = []
    lines.append(f"# SafeVoice classifier eval — `{corpus_meta.get('version', 'v1')}`")
    lines.append("")
    lines.append(f"_Run: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())} · Prompt version: `{PROMPT_VERSION}` · {n} cases · {len(by_category)} categories_")
    lines.append("")
    lines.append(corpus_meta.get("description", ""))
    lines.append("")

    # Headline
    lines.append("## Headline")
    lines.append("")
    lines.append(f"- **Pass rate (all 4 dimensions): {n_passed}/{n} ({n_passed/n*100:.0f}%)**")
    lines.append(f"- Severity exact-match: {n_severity}/{n} ({n_severity/n*100:.0f}%)")
    lines.append(f"- Expected categories present: {n_categories}/{n} ({n_categories/n*100:.0f}%)")
    lines.append(f"- Expected laws present: {n_laws_present}/{n} ({n_laws_present/n*100:.0f}%)")
    lines.append(f"- Forbidden laws absent (false-positive guard): {n_forbidden_absent}/{n} ({n_forbidden_absent/n*100:.0f}%)")
    lines.append(f"- Avg latency: {avg_lat} ms")
    lines.append("")

    # Per-category accuracy
    lines.append("## Per-category pass rate")
    lines.append("")
    lines.append("| Category | Cases | Passed | Severity | Categories | Laws-present | Forbidden-absent |")
    lines.append("|---|---|---|---|---|---|---|")
    for cat in sorted(by_category.keys()):
        items = by_category[cat]
        n_cat = len(items)
        cat_passed = sum(1 for r in items if r.passed)
        cat_sev = sum(1 for r in items if r.severity_match)
        cat_cat = sum(1 for r in items if r.categories_ok)
        cat_law = sum(1 for r in items if r.laws_present)
        cat_forb = sum(1 for r in items if r.forbidden_absent)
        lines.append(f"| {cat} | {n_cat} | **{cat_passed}/{n_cat}** | {cat_sev}/{n_cat} | {cat_cat}/{n_cat} | {cat_law}/{n_cat} | {cat_forb}/{n_cat} |")
    lines.append("")

    # Failing cases (the actionable list)
    failing = [r for r in results if not r.passed]
    lines.append(f"## Failing cases ({len(failing)})")
    lines.append("")
    if not failing:
        lines.append("**All cases pass.** Either the prompt is excellent or the eval set is too easy — grow the set.")
    else:
        lines.append("Cases marked with the dimension they failed on. Use this list to drive prompt iteration.")
        lines.append("")
        lines.append("| Case | Text | Expected | Got | Failed dimensions |")
        lines.append("|---|---|---|---|---|")
        for r in failing:
            txt = r.text if len(r.text) <= 60 else r.text[:60] + "…"
            failed_dims = []
            if not r.severity_match: failed_dims.append(f"severity ({r.got_severity})")
            if not r.categories_ok: failed_dims.append("categories")
            if not r.laws_present: failed_dims.append("missing-law")
            if not r.forbidden_absent: failed_dims.append("forbidden-law-present")
            lines.append(f"| `{r.id}` | _{txt}_ | **{r.expected_severity}** | {r.got_severity or 'ERR'} | {', '.join(failed_dims)} |")
    lines.append("")

    # Per-case detail
    lines.append("## Per-case detail")
    lines.append("")
    lines.append("| Case | Severity | Categories | Laws | Latency |")
    lines.append("|---|---|---|---|---|")
    for r in results:
        sev_mark = "✓" if r.severity_match else "✗"
        cat_mark = "✓" if r.categories_ok else "✗"
        law_mark = "✓" if r.laws_present and r.forbidden_absent else "✗"
        lines.append(f"| `{r.id}` | {sev_mark} {r.got_severity or 'ERR'} (exp {r.expected_severity}) | {cat_mark} got {len(r.got_categories)} | {law_mark} got {', '.join(r.got_laws[:3])}{'…' if len(r.got_laws) > 3 else ''} | {r.latency_ms} ms |")
    lines.append("")

    # Conclusion
    pct = n_passed / n * 100
    lines.append("## Conclusion")
    lines.append("")
    if pct >= 90:
        verdict = f"**{pct:.0f}% pass rate is production-ready** for this corpus."
    elif pct >= 75:
        verdict = f"**{pct:.0f}% pass rate is shippable but improvable.** Failing cases are the actionable list."
    else:
        verdict = f"**{pct:.0f}% pass rate is not yet defensible.** Iterate the prompt against the failing cases before claiming the model works."
    lines.append(verdict)
    lines.append("")
    lines.append("Re-run after prompt changes:")
    lines.append("```bash")
    lines.append("cd /Users/mikel/safevoice && source backend/venv/bin/activate && python scripts/run_eval.py")
    lines.append("```")
    lines.append("")
    lines.append(f"_Generated by `scripts/run_eval.py` · classifier prompt version `{PROMPT_VERSION}`._")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))
    print(f"\n✓ Wrote {out_path}")


def main():
    corpus_path = Path(__file__).resolve().parent.parent / "evals" / "harassment_eval_set.json"
    corpus = json.loads(corpus_path.read_text())
    cases = corpus["cases"]
    print(f"Eval corpus v{corpus.get('version')} · {len(cases)} cases · prompt v{PROMPT_VERSION}\n")

    results: list[CaseResult] = []
    for i, case in enumerate(cases, 1):
        r = run_one(case)
        mark = "✓" if r.passed else "✗"
        print(f"  [{i:2d}/{len(cases)}] {mark} {r.id:32s} → got {r.got_severity or 'ERR':9s} (exp {r.expected_severity:9s}) {r.latency_ms:5d}ms"
              + (f"  {r.error[:60]}" if r.error else ""))
        results.append(r)

    out = Path(__file__).resolve().parent.parent / "docs" / "notebooks" / "eval-results.md"
    write_markdown(results, corpus, out)
    raw = out.with_suffix(".json")
    raw.write_text(json.dumps([asdict(r) for r in results], default=str, indent=2))
    print(f"✓ Wrote {raw}")


if __name__ == "__main__":
    main()
