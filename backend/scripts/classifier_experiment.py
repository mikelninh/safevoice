"""
Classifier experiment — compare gpt-4o-mini · gpt-4o · gpt-5 side-by-side.

Run from backend/ with venv active:
    OPENAI_API_KEY=sk-... python3 scripts/classifier_experiment.py

Outputs:
    scripts/out/comparison_<timestamp>.csv        # raw per-run rows
    scripts/out/comparison_<timestamp>.md         # markdown table for Notion
    scripts/out/prompt_payload_<timestamp>.json   # the exact prompt + inputs used

Notes
- gpt-4o-mini and gpt-4o use `temperature=0` for determinism.
- gpt-5 does NOT accept `temperature` — it uses `reasoning_effort`
  (minimal | low | medium | high) and `verbosity` (low | medium | high).
  We run gpt-5 at (reasoning_effort="medium", verbosity="low") as the
  default, and add a second run at high/high so the table shows both.
- Every cell records: severity, categories, confidence, latency_ms,
  input_tokens, output_tokens, cost_cents (best-effort estimate).
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Make the app package importable when run from backend/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from openai import OpenAI  # noqa: E402
except ImportError:
    print("openai sdk not installed. pip install openai")
    sys.exit(1)

from app.services.classifier_llm_v2 import SYSTEM_PROMPT, LLMClassification  # noqa: E402


# ── Test cases ──────────────────────────────────────────────────────────

TEST_CASES = [
    {
        "id": "explicit_threat",
        "text": "Ich bringe dich um",
        "victim_context": None,
        "expected": "critical · death_threat · §§ 241, 126a StGB",
    },
    {
        "id": "idiom_false_positive",
        "text": "Das bringt mich um",
        "victim_context": None,
        "expected": "low or none · idiom, not a criminal offence",
    },
    {
        "id": "obfuscation",
        "text": "Stirbt endlich, du H*re",
        "victim_context": None,
        "expected": "critical · death_threat + misogyny · §§ 241, 185 StGB",
    },
    {
        "id": "contextual_stalking",
        "text": "Ich weiß wo du arbeitest",
        "victim_context": "Ex-Partner, schreibt seit 3 Monaten täglich",
        "expected": "high · stalking + threat · §§ 238, 241 StGB (context upgrades to § 238)",
    },
    {
        "id": "borderline",
        "text": "Du bist echt nervig heute",
        "victim_context": None,
        "expected": "low · harassment · NetzDG § 3 (borderline / Terms-of-Service only)",
    },
]


# ── Model configurations ────────────────────────────────────────────────

MODEL_CONFIGS = [
    # (id, model, kwargs)
    ("gpt-4o-mini · temp=0",                  "gpt-4o-mini", {"temperature": 0, "max_tokens": 1024}),
    ("gpt-4o · temp=0",                       "gpt-4o",      {"temperature": 0, "max_tokens": 1024}),
    ("gpt-5 · reasoning=medium · verbosity=low",  "gpt-5",   {"reasoning_effort": "medium", "verbosity": "low", "max_completion_tokens": 2048}),
    ("gpt-5 · reasoning=high · verbosity=medium", "gpt-5",   {"reasoning_effort": "high",   "verbosity": "medium", "max_completion_tokens": 2048}),
]


# ── Best-effort pricing (USD per 1M tokens, April 2026 public rates) ────

PRICING = {
    "gpt-4o-mini": {"in": 0.150, "out": 0.600},
    "gpt-4o":      {"in": 2.500, "out": 10.000},
    "gpt-5":       {"in": 1.250, "out": 10.000},  # placeholder — update when OpenAI publishes
}


# ── Runner ─────────────────────────────────────────────────────────────

def build_user_message(text: str, victim_context: str | None) -> str:
    parts = ["Klassifiziere diesen Inhalt nach dem Strafrecht der Jurisdiktion: DE."]
    if victim_context:
        parts.append(f"Kontext des Opfers: {victim_context}")
    parts.append(f"Inhalt:\n{text}")
    return "\n\n".join(parts)


def run_one(client: OpenAI, model: str, kwargs: dict, test: dict) -> dict:
    user_msg = build_user_message(test["text"], test.get("victim_context"))
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_msg},
    ]

    t0 = time.perf_counter()
    try:
        completion = client.chat.completions.parse(
            model=model,
            messages=messages,
            response_format=LLMClassification,
            **kwargs,
        )
        latency_ms = int((time.perf_counter() - t0) * 1000)

        msg = completion.choices[0].message
        if msg.refusal:
            return {"status": "refused", "refusal": msg.refusal, "latency_ms": latency_ms}

        parsed = msg.parsed
        usage = completion.usage
        price = PRICING.get(model, {"in": 0, "out": 0})
        cost_cents = (
            (usage.prompt_tokens / 1_000_000) * price["in"] * 100
            + (usage.completion_tokens / 1_000_000) * price["out"] * 100
        )
        return {
            "status": "ok",
            "severity": parsed.severity.value if parsed else None,
            "categories": [c.value for c in parsed.categories] if parsed else [],
            "confidence": parsed.confidence if parsed else None,
            "laws": [l.value for l in parsed.applicable_laws] if parsed else [],
            "summary_de": parsed.summary_de if parsed else None,
            "latency_ms": latency_ms,
            "input_tokens": usage.prompt_tokens,
            "output_tokens": usage.completion_tokens,
            "cost_cents": round(cost_cents, 4),
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "latency_ms": int((time.perf_counter() - t0) * 1000)}


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = Path(__file__).resolve().parent / "out"
    out_dir.mkdir(exist_ok=True)
    csv_path = out_dir / f"comparison_{stamp}.csv"
    md_path  = out_dir / f"comparison_{stamp}.md"
    pay_path = out_dir / f"prompt_payload_{stamp}.json"

    # Snapshot the exact prompt + inputs used so the tutor can audit.
    pay_path.write_text(json.dumps({
        "timestamp": stamp,
        "system_prompt_sha_lines": len(SYSTEM_PROMPT.splitlines()),
        "system_prompt": SYSTEM_PROMPT,
        "test_cases": TEST_CASES,
        "model_configs": [{"id": c[0], "model": c[1], "kwargs": c[2]} for c in MODEL_CONFIGS],
    }, indent=2, ensure_ascii=False))

    print(f"Running {len(TEST_CASES)} test cases × {len(MODEL_CONFIGS)} model configs = {len(TEST_CASES) * len(MODEL_CONFIGS)} total calls...\n")

    rows: list[dict] = []
    for test in TEST_CASES:
        print(f"─── {test['id']}: {test['text']!r} ───")
        for cfg_id, model, kwargs in MODEL_CONFIGS:
            result = run_one(client, model, kwargs, test)
            row = {
                "test_id": test["id"],
                "input": test["text"],
                "victim_context": test.get("victim_context") or "",
                "expected": test["expected"],
                "config": cfg_id,
                "model": model,
                **result,
            }
            if isinstance(row.get("categories"), list):
                row["categories"] = "|".join(row["categories"])
            if isinstance(row.get("laws"), list):
                row["laws"] = "|".join(row["laws"])
            rows.append(row)
            status = result.get("status", "?")
            summary = ""
            if status == "ok":
                summary = f"sev={result['severity']} cats=[{row['categories']}] lat={result['latency_ms']}ms €={result['cost_cents']/100:.5f}"
            elif status == "error":
                summary = f"ERROR: {result.get('error', '')[:120]}"
            elif status == "refused":
                summary = f"REFUSED: {result.get('refusal', '')[:120]}"
            print(f"  {cfg_id:<50}  {summary}")
        print()

    # ── CSV ──
    all_keys = sorted({k for r in rows for k in r.keys()})
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys)
        writer.writeheader()
        writer.writerows(rows)

    # ── Markdown ──
    md = ["# Classifier Comparison — 3 OpenAI Models\n",
          f"*Generated: {stamp}*\n",
          f"*System prompt: {len(SYSTEM_PROMPT.splitlines())} lines · few-shot with victim_context*\n",
          "## Results\n",
          "| Test | Config | Severity | Categories | Laws | Confidence | Latency | Cost (€) |",
          "|------|--------|----------|------------|------|-----------|---------|----------|"]
    for r in rows:
        if r.get("status") != "ok":
            md.append(f"| `{r['test_id']}` | {r['config']} | **{r.get('status','')}** | — | — | — | {r.get('latency_ms','?')}ms | — |")
            continue
        cost_eur = (r.get("cost_cents") or 0) / 100
        md.append(
            f"| `{r['test_id']}` | {r['config']} | **{r['severity']}** | "
            f"{r['categories']} | {r['laws']} | {r['confidence']:.2f} | "
            f"{r['latency_ms']}ms | €{cost_eur:.5f} |"
        )
    md.append("\n## Test inputs\n")
    for t in TEST_CASES:
        md.append(f"- **`{t['id']}`** — {t['text']!r}" + (f" · context: *{t['victim_context']}*" if t.get("victim_context") else ""))
        md.append(f"  - Expected: {t['expected']}")
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"✓ CSV    → {csv_path}")
    print(f"✓ Markdown → {md_path}")
    print(f"✓ Payload  → {pay_path}")


if __name__ == "__main__":
    main()
