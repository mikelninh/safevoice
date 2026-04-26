#!/usr/bin/env python3
"""
gpt-5-mini hyperparameter sweep — `reasoning_effort` × `verbosity`.

The earlier compare_prompts.py used OpenAI defaults (medium reasoning, medium
verbosity) for gpt-5-mini and found it tied with gpt-4o-mini on accuracy at
~7× the cost. The interesting question this sweep answers:

  Does `reasoning_effort=low` keep accuracy at 100% while cutting cost +
  latency in half? If yes, gpt-5-mini becomes cost-competitive. If no,
  gpt-4o-mini stays the production winner.

We sweep a 3×3 grid (low/medium/high reasoning × low/medium/high verbosity)
on the production few-shot CoT prompt only — that's the prompt that achieves
100% accuracy for every model in the main comparison, so it isolates the
hyperparameter effect from the prompt effect.

Total: 9 cells × 6 cases = 54 calls. With the 13s gpt-5-mini RPM throttle
that's ~12 minutes of waiting + actual call latency.

Usage:
  cd /Users/mikel/safevoice
  source backend/venv/bin/activate
  python scripts/sweep_gpt5_hyperparams.py

Output: docs/notebooks/gpt5-hyperparam-sweep.md (paste-ready for Notion).
"""

from __future__ import annotations

import os
import time
import json
import statistics
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, asdict

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

from openai import OpenAI
from pydantic import BaseModel, Field, ConfigDict


# Same schema + production prompt as compare_prompts.py — keep in sync.
class Severity(str, Enum):
    low = "low"; medium = "medium"; high = "high"; critical = "critical"

class CategoryEnum(str, Enum):
    harassment = "harassment"; threat = "threat"; death_threat = "death_threat"
    defamation = "defamation"; verleumdung = "verleumdung"; misogyny = "misogyny"
    body_shaming = "body_shaming"; sexual_harassment = "sexual_harassment"
    volksverhetzung = "volksverhetzung"; stalking = "stalking"
    intimate_images = "intimate_images"; scam = "scam"; phishing = "phishing"
    investment_fraud = "investment_fraud"; romance_scam = "romance_scam"
    impersonation = "impersonation"; false_facts = "false_facts"
    coordinated_attack = "coordinated_attack"

class LawEnum(str, Enum):
    stgb_130 = "§ 130 StGB"; stgb_185 = "§ 185 StGB"; stgb_186 = "§ 186 StGB"
    stgb_187 = "§ 187 StGB"; stgb_201a = "§ 201a StGB"; stgb_238 = "§ 238 StGB"
    stgb_241 = "§ 241 StGB"; stgb_126a = "§ 126a StGB"; stgb_263 = "§ 263 StGB"
    stgb_263a = "§ 263a StGB"; stgb_269 = "§ 269 StGB"; netzdg_3 = "NetzDG § 3"

class Classification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    severity: Severity
    categories: list[CategoryEnum] = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    requires_immediate_action: bool
    summary: str
    summary_de: str
    applicable_laws: list[LawEnum]
    potential_consequences: str
    potential_consequences_de: str


# Re-import the production prompt + test cases from compare_prompts.py.
# Use a regular import (with sys.path) so dataclass introspection works.
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare_prompts as _cmp  # noqa: E402
SYSTEM_PROMPT = _cmp.PROMPT_2_PRODUCTION
TEST_CASES = _cmp.TEST_CASES


# Sweep grid
REASONING_EFFORTS = ["low", "medium", "high"]
VERBOSITIES = ["low", "medium", "high"]
MODEL = "gpt-5-mini"

# OpenAI tier-1 RPM limit on gpt-5-mini = 5 RPM. Throttle to 13s between calls.
RATE_DELAY = 13.0
MAX_COMPLETION_TOKENS = 4096

# Pricing (EUR per 1M tokens) — same constants as compare_prompts.py
EUR_PER_USD = 0.93
PRICING = {"input": 0.25 * EUR_PER_USD, "output": 2.00 * EUR_PER_USD}


@dataclass
class Cell:
    case_id: str
    reasoning_effort: str
    verbosity: str
    severity: str | None
    in_tokens: int
    out_tokens: int
    latency_ms: int
    cost_eur: float
    error: str | None = None

    def correct(self, expected: str) -> bool:
        return self.severity == expected


def run_one(client: OpenAI, case, reasoning: str, verbosity: str) -> Cell:
    user_msg = f"Klassifiziere diesen Inhalt:\n\n{case.text}"
    t0 = time.time()
    try:
        completion = client.chat.completions.parse(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            response_format=Classification,
            max_completion_tokens=MAX_COMPLETION_TOKENS,
            reasoning_effort=reasoning,
            verbosity=verbosity,
        )
    except Exception as e:
        return Cell(case.id, reasoning, verbosity, None, 0, 0,
                    int((time.time() - t0) * 1000), 0.0, error=str(e)[:200])
    elapsed = int((time.time() - t0) * 1000)
    msg = completion.choices[0].message
    if msg.refusal:
        return Cell(case.id, reasoning, verbosity, None,
                    completion.usage.prompt_tokens, completion.usage.completion_tokens,
                    elapsed, 0.0, error=f"refusal: {msg.refusal[:120]}")
    parsed = msg.parsed
    if parsed is None:
        return Cell(case.id, reasoning, verbosity, None,
                    completion.usage.prompt_tokens, completion.usage.completion_tokens,
                    elapsed, 0.0, error="parse returned None (likely token truncation)")
    cost = (
        completion.usage.prompt_tokens * PRICING["input"]
        + completion.usage.completion_tokens * PRICING["output"]
    ) / 1_000_000
    return Cell(case.id, reasoning, verbosity, parsed.severity.value,
                completion.usage.prompt_tokens, completion.usage.completion_tokens,
                elapsed, cost)


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY not set")
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    results: list[Cell] = []
    grid = [(r, v) for r in REASONING_EFFORTS for v in VERBOSITIES]
    total = len(grid) * len(TEST_CASES)
    n = 0
    last_call = 0.0
    print(f"gpt-5-mini sweep · 3 reasoning × 3 verbosity × {len(TEST_CASES)} cases = {total} calls\n")
    for reasoning, verbosity in grid:
        for case in TEST_CASES:
            n += 1
            elapsed_since = time.time() - last_call
            if elapsed_since < RATE_DELAY:
                wait = RATE_DELAY - elapsed_since
                print(f"  [{n:2d}/{total}] sleeping {wait:.1f}s for gpt-5 RPM…")
                time.sleep(wait)
            last_call = time.time()
            r = run_one(client, case, reasoning, verbosity)
            ok = "✓" if (r.error is None and r.correct(case.expected_severity.value)) else (
                 "✗" if r.error is None else "!")
            err = f" ({r.error[:60]})" if r.error else ""
            print(f"  [{n:2d}/{total}] {ok} R={reasoning:6s} V={verbosity:6s} {case.id:18s} → "
                  f"{r.severity or '—':9s} {r.latency_ms:5d}ms {r.out_tokens:5d}tok{err}")
            results.append(r)
    return results


def write_markdown(results: list[Cell], out_path: Path):
    # Aggregate per (reasoning, verbosity) cell
    cells: dict[tuple[str, str], dict] = {}
    for r in results:
        key = (r.reasoning_effort, r.verbosity)
        s = cells.setdefault(key, {
            "n": 0, "correct": 0, "errors": 0,
            "in_tokens": 0, "out_tokens": 0, "latencies": [], "cost": 0.0,
        })
        s["n"] += 1
        if r.error:
            s["errors"] += 1
            continue
        s["in_tokens"] += r.in_tokens
        s["out_tokens"] += r.out_tokens
        s["latencies"].append(r.latency_ms)
        s["cost"] += r.cost_eur
        case = next(c for c in TEST_CASES if c.id == r.case_id)
        if r.severity == case.expected_severity.value:
            s["correct"] += 1

    lines: list[str] = []
    lines.append("# SafeVoice — `gpt-5-mini` reasoning_effort × verbosity sweep")
    lines.append("")
    lines.append("Hyperparameter sweep on `gpt-5-mini` only, using the production few-shot CoT system prompt (the one that achieves 100% accuracy for every model in the main comparison). Isolates the *hyperparameter effect* from the *prompt effect*.")
    lines.append("")
    lines.append(f"- Grid: **{len(REASONING_EFFORTS)} reasoning_effort levels** × **{len(VERBOSITIES)} verbosity levels** × **{len(TEST_CASES)} test cases** = {len(REASONING_EFFORTS) * len(VERBOSITIES) * len(TEST_CASES)} calls")
    lines.append(f"- Model: **{MODEL}**, `max_completion_tokens={MAX_COMPLETION_TOKENS}`")
    lines.append(f"- Pricing (EUR / 1M tokens): in=€{PRICING['input']:.3f} · out=€{PRICING['output']:.3f} · EUR/USD={EUR_PER_USD}")
    lines.append("")

    # Accuracy heatmap
    lines.append("## Accuracy heatmap (correct / 6)")
    lines.append("")
    lines.append("| reasoning ↓ verbosity → | " + " | ".join(VERBOSITIES) + " |")
    lines.append("|---|" + "---|" * len(VERBOSITIES))
    for reasoning in REASONING_EFFORTS:
        row = f"| **{reasoning}** |"
        for verbosity in VERBOSITIES:
            s = cells.get((reasoning, verbosity), {})
            n_ok = s.get("n", 0) - s.get("errors", 0)
            correct = s.get("correct", 0)
            cell_str = f" {correct}/{n_ok} ({correct/n_ok*100:.0f}%) " if n_ok else " — "
            if s.get("errors", 0):
                cell_str += f"⚠{s['errors']} "
            row += cell_str + "|"
        lines.append(row)
    lines.append("")

    # Cost heatmap
    lines.append("## Cost heatmap (EUR for 6-case run)")
    lines.append("")
    lines.append("| reasoning ↓ verbosity → | " + " | ".join(VERBOSITIES) + " |")
    lines.append("|---|" + "---|" * len(VERBOSITIES))
    for reasoning in REASONING_EFFORTS:
        row = f"| **{reasoning}** |"
        for verbosity in VERBOSITIES:
            s = cells.get((reasoning, verbosity), {})
            row += f" €{s.get('cost', 0):.5f} |"
        lines.append(row)
    lines.append("")

    # Latency heatmap
    lines.append("## Avg latency heatmap (ms)")
    lines.append("")
    lines.append("| reasoning ↓ verbosity → | " + " | ".join(VERBOSITIES) + " |")
    lines.append("|---|" + "---|" * len(VERBOSITIES))
    for reasoning in REASONING_EFFORTS:
        row = f"| **{reasoning}** |"
        for verbosity in VERBOSITIES:
            s = cells.get((reasoning, verbosity), {})
            avg_lat = int(statistics.mean(s["latencies"])) if s.get("latencies") else 0
            row += f" {avg_lat} ms |"
        lines.append(row)
    lines.append("")

    # Output token heatmap
    lines.append("## Output tokens (total, 6-case run)")
    lines.append("")
    lines.append("| reasoning ↓ verbosity → | " + " | ".join(VERBOSITIES) + " |")
    lines.append("|---|" + "---|" * len(VERBOSITIES))
    for reasoning in REASONING_EFFORTS:
        row = f"| **{reasoning}** |"
        for verbosity in VERBOSITIES:
            s = cells.get((reasoning, verbosity), {})
            row += f" {s.get('out_tokens', 0):,} |"
        lines.append(row)
    lines.append("")

    # Per-call details
    lines.append("## Per-call details")
    lines.append("")
    lines.append("| Case | R | V | Severity | Latency | In/Out tokens | Cost |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in results:
        if r.error:
            lines.append(f"| `{r.case_id}` | {r.reasoning_effort} | {r.verbosity} | ⚠ {r.error[:30]} | {r.latency_ms} ms | {r.in_tokens}/{r.out_tokens} | — |")
        else:
            lines.append(f"| `{r.case_id}` | {r.reasoning_effort} | {r.verbosity} | {r.severity} | {r.latency_ms} ms | {r.in_tokens}/{r.out_tokens} | €{r.cost_eur:.6f} |")
    lines.append("")

    # Conclusion
    ranked = []
    for (r_eff, v), s in cells.items():
        n_ok = s["n"] - s["errors"]
        acc = s["correct"] / n_ok if n_ok else 0
        avg_lat = statistics.mean(s["latencies"]) if s["latencies"] else float("inf")
        ranked.append({"reasoning": r_eff, "verbosity": v, "accuracy": acc,
                       "cost": s["cost"], "avg_lat": avg_lat})
    ranked.sort(key=lambda r: (-r["accuracy"], r["cost"], r["avg_lat"]))
    best = ranked[0] if ranked else None

    lines.append("## Conclusion")
    lines.append("")
    if best:
        lines.append(f"On this 6-case German harassment corpus, the cheapest `gpt-5-mini` configuration that maintains the production prompt's 100% accuracy is **reasoning_effort={best['reasoning']}, verbosity={best['verbosity']}** — €{best['cost']:.5f} for 6 calls, avg latency {int(best['avg_lat'])} ms.")
    lines.append("")
    lines.append("**What this tells us about gpt-5-mini for SafeVoice:**")
    lines.append("")
    # Compare best gpt-5-mini cell to gpt-4o-mini baseline (€0.00171, 13.3s, 100%)
    if best:
        cost_ratio = best["cost"] / 0.00171
        lines.append(f"- Best gpt-5-mini configuration costs **{cost_ratio:.1f}× more** than `gpt-4o-mini + Production` (€{best['cost']:.5f} vs €0.00171 baseline).")
        lat_delta = int(best["avg_lat"]) - 13275
        lines.append(f"- Latency vs baseline: {'+' if lat_delta >= 0 else ''}{lat_delta} ms (`gpt-4o-mini` baseline = 13,275 ms).")
    lines.append("- **Reasoning_effort interpretation:** if `low` ties accuracy with `medium`/`high`, the reasoning premium adds nothing for this short-text classification. If `high` strictly improves accuracy, there's a ceiling that benefits from extra thinking.")
    lines.append("- **Verbosity interpretation:** lower verbosity should reduce output tokens linearly. If accuracy is invariant to verbosity, always run with `verbosity=low` to cut output cost.")
    lines.append("- **Production recommendation:** if no gpt-5-mini cell beats `gpt-4o-mini + Production` on the cost/accuracy frontier, `gpt-4o-mini` remains the production choice. Re-run this sweep on a larger (30-50 case) corpus before changing production model — 6 cases is too small a base to make irreversible decisions.")
    lines.append("")
    lines.append(f"_Generated by `scripts/sweep_gpt5_hyperparams.py` · {len(results)} calls._")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))
    print(f"\n✓ Wrote {out_path}")


if __name__ == "__main__":
    results = main()
    out = Path(__file__).resolve().parent.parent / "docs" / "notebooks" / "gpt5-hyperparam-sweep.md"
    write_markdown(results, out)
    raw = out.with_suffix(".json")
    raw.write_text(json.dumps([asdict(r) for r in results], default=str, indent=2))
    print(f"✓ Wrote {raw}")
