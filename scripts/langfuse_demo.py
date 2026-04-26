#!/usr/bin/env python3
"""
30-second Langfuse demo — wraps the SafeVoice classifier so every call becomes
a trace in the Langfuse UI: full prompt, response, tokens, latency, cost,
plus our custom prompt_version metadata.

What you'll see in the Langfuse UI:
  - Traces tab: 6 classification calls, each fully expanded with the system
    prompt, the user message, the parsed Pydantic output, token usage and
    cost. Click any one to see the structured response.
  - Sessions tab: all 6 calls grouped under a single session for this run.
  - Each trace tagged with prompt_version=v2, expected_severity, case_id —
    so you can filter, group, and aggregate.
  - Scores: each trace gets a severity_match score (1 or 0) so you see
    aggregate accuracy in the dashboard, not just in a markdown report.

Setup (one-time, ~5 min):
  1. Sign up at https://cloud.langfuse.com  (or https://eu.cloud.langfuse.com
     for EU-hosted — recommended for SafeVoice's DSGVO posture)
  2. Create a project → Settings → API Keys → New API Key
  3. Add to /Users/mikel/safevoice/.env:
       LANGFUSE_PUBLIC_KEY=pk-lf-...
       LANGFUSE_SECRET_KEY=sk-lf-...
       LANGFUSE_HOST=https://eu.cloud.langfuse.com   # or .com for US
  4. pip install langfuse  (in the safevoice venv)
  5. python scripts/langfuse_demo.py

Run cost: 6 OpenAI calls × ~€0.0003 ≈ €0.002.
Run time: ~80 seconds (5-RPM throttle on tier-1 OpenAI project).
"""

from __future__ import annotations

import os
import sys
import time
import json
from pathlib import Path

# Load .env from repo root
def _load_env():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

_load_env()

# Helpful exit if Langfuse env isn't configured yet
required = ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "OPENAI_API_KEY"]
missing = [k for k in required if not os.environ.get(k)]
if missing:
    print(f"\n  Missing env vars: {missing}\n")
    if "LANGFUSE_PUBLIC_KEY" in missing or "LANGFUSE_SECRET_KEY" in missing:
        print("  → Sign up: https://cloud.langfuse.com  (or https://eu.cloud.langfuse.com for EU)")
        print("  → Project Settings → API Keys → New API Key")
        print("  → Add to .env:")
        print("      LANGFUSE_PUBLIC_KEY=pk-lf-...")
        print("      LANGFUSE_SECRET_KEY=sk-lf-...")
        print("      LANGFUSE_HOST=https://eu.cloud.langfuse.com")
    sys.exit(1)

# Default to EU host if user didn't set one — DSGVO-aware default for SafeVoice
os.environ.setdefault("LANGFUSE_HOST", "https://eu.cloud.langfuse.com")

# Make backend/ importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

try:
    from langfuse import Langfuse
    from langfuse.openai import openai as lf_openai
except ImportError:
    print("\n  langfuse not installed. Run: pip install langfuse\n")
    sys.exit(1)

from app.services.classifier_llm_v2 import SYSTEM_PROMPT, PROMPT_VERSION, LLMClassification

# Initialise the Langfuse client (reads LANGFUSE_* env vars)
lf = Langfuse()

# A small representative subset of the eval corpus — enough to show the UI
# without burning the whole 5-RPM budget on a demo.
CORPUS = json.loads(
    (Path(__file__).resolve().parent.parent / "evals" / "harassment_eval_set.json").read_text()
)
DEMO_IDS = [
    "A1-baseline-greeting",                # baseline non-harassment
    "C2-arschloch",                        # § 185 (v2 prompt should now hit medium)
    "D2-misogyny-obfuscated-asterisk",     # obfuscation
    "F2-death-threat-with-misogyny",       # critical, multi-law
    "G1-idiom-bringt-mich-um",             # idiom — false-positive guard
    "H1-nazi-88",                          # § 130 dog-whistle (v2 added explicit rule)
]
demo_cases = [c for c in CORPUS["cases"] if c["id"] in DEMO_IDS]

session_id = f"demo-{time.strftime('%Y%m%d-%H%M%S')}"
print(f"\nLangfuse demo · session_id = {session_id}")
print(f"Host: {os.environ['LANGFUSE_HOST']}")
print(f"Prompt version: {PROMPT_VERSION}")
print(f"Cases: {len(demo_cases)}\n")


def classify_traced(case: dict) -> dict:
    """Run one classification with full Langfuse tracing.

    The lf_openai wrapper auto-traces every call: prompt, response, tokens,
    latency, cost — all in one trace. We add custom metadata so the UI knows
    the prompt version, the case ID, and what we expected, which makes filter
    + group + score trivial later.
    """
    text = case["text"]
    victim_context = case.get("victim_context")

    user_msg = f"Klassifiziere diesen Inhalt:\n\n{text}"
    if victim_context:
        user_msg = f"Victim context: {victim_context}\n\n{user_msg}"

    t0 = time.time()
    completion = lf_openai.chat.completions.parse(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        response_format=LLMClassification,
        # All of this lands in the Langfuse trace as metadata — searchable + filterable
        name=f"classify · {case['id']}",
        session_id=session_id,
        metadata={
            "case_id": case["id"],
            "case_category": case["category"],
            "expected_severity": case["expected_severity"],
            "prompt_version": PROMPT_VERSION,
            "victim_context_present": victim_context is not None,
        },
        tags=[f"prompt-{PROMPT_VERSION}", "demo", case["category"].split(" · ")[0]],
    )
    elapsed = int((time.time() - t0) * 1000)

    msg = completion.choices[0].message
    if msg.refusal or msg.parsed is None:
        return {"case_id": case["id"], "severity": None, "passed": False,
                "elapsed_ms": elapsed, "error": "refusal_or_no_parse"}

    parsed = msg.parsed
    got_sev = parsed.severity.value
    passed = got_sev == case["expected_severity"]

    # Attach a Score to the trace — this is what makes Langfuse's eval
    # dashboards work. You'll see aggregate accuracy in the UI without writing
    # any markdown report.
    try:
        # The Langfuse-wrapped OpenAI call sets the active trace context;
        # langfuse_context.score_current_trace() attaches to the current span.
        from langfuse.decorators import langfuse_context
        langfuse_context.score_current_trace(
            name="severity_match",
            value=1.0 if passed else 0.0,
            comment=f"got={got_sev}, expected={case['expected_severity']}",
        )
    except Exception as e:
        # Older SDK style — fall back to direct score creation
        try:
            lf.score(
                trace_id=lf.get_current_trace_id(),
                name="severity_match",
                value=1.0 if passed else 0.0,
            )
        except Exception:
            pass  # don't let scoring break the demo

    return {
        "case_id": case["id"],
        "severity": got_sev,
        "expected": case["expected_severity"],
        "passed": passed,
        "elapsed_ms": elapsed,
    }


# Throttle for the OpenAI 5-RPM tier limit
RATE_DELAY = 13.0
last_call = 0.0
n_passed = 0

for i, case in enumerate(demo_cases, 1):
    elapsed_since = time.time() - last_call
    if elapsed_since < RATE_DELAY and i > 1:
        wait = RATE_DELAY - elapsed_since
        print(f"  [{i}/{len(demo_cases)}] sleeping {wait:.1f}s for OpenAI RPM…", end="\r")
        time.sleep(wait)
    last_call = time.time()

    result = classify_traced(case)
    mark = "✓" if result.get("passed") else "✗"
    if result.get("passed"):
        n_passed += 1
    print(f"  [{i}/{len(demo_cases)}] {mark} {result['case_id']:35s} → "
          f"got {result.get('severity') or 'ERR':9s} "
          f"(exp {result.get('expected', '?'):9s}) "
          f"{result['elapsed_ms']}ms")

# Make sure all traces are flushed to Langfuse before exit
lf.flush()

print(f"\n✓ Done. {n_passed}/{len(demo_cases)} passed.\n")
print(f"Open the Langfuse UI: {os.environ['LANGFUSE_HOST']}")
print(f"  → Traces tab — filter by session_id={session_id}")
print(f"  → Each trace shows full prompt + response + tokens + cost + latency")
print(f"  → Scores tab — aggregate severity_match across all traces in this run")
print(f"  → Filter by tag 'prompt-{PROMPT_VERSION}' to compare against future v3 runs\n")
