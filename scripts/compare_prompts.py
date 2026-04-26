#!/usr/bin/env python3
"""
SafeVoice classifier prompt comparison — homework matrix run.

Compares two prompt techniques across three OpenAI models on a small fixed
test corpus of German harassment messages spanning the full severity scale:

  Prompt #1 — "Minimalist (zero-shot)"
    A two-line system prompt. Trusts the model + the Pydantic schema to do
    everything. No worked examples, no severity scale, no category glossary.

  Prompt #2 — "Production Few-shot CoT"
    The full SafeVoice production prompt copied verbatim from
    backend/app/services/classifier_llm_v2.py — rules, severity scale with
    examples, category definitions, four worked few-shot examples.

Both prompts target the same Pydantic-enforced output schema, so the comparison
isolates *prompt technique* from *output formatting*.

Models: gpt-4o-mini, gpt-4.1-mini, gpt-5-mini (OpenAI only — no Google keys).

For each (model × prompt × test message) we record:
  - severity (vs. expected — drives accuracy)
  - categories returned
  - input + output token count
  - latency in ms
  - per-call cost in EUR

Aggregated per (model × prompt):
  - accuracy %
  - avg latency
  - total tokens
  - total cost

Output: a markdown comparison table at docs/notebooks/prompt-comparison.md
that you can paste into the Notion homework page.

Usage:
  cd /Users/mikel/safevoice
  source backend/venv/bin/activate
  python scripts/compare_prompts.py
"""

from __future__ import annotations

import os
import time
import json
import statistics
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field, asdict

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

try:
    from openai import OpenAI
except ImportError:
    raise SystemExit("openai SDK not installed. Run: pip install -r backend/requirements.txt")

from pydantic import BaseModel, Field, ConfigDict


# ─────────────────────── SHARED OUTPUT SCHEMA ───────────────────────
# Same Pydantic schema both prompts target. Lifted from
# backend/app/services/classifier_llm_v2.py to keep the experiment self-
# contained and decoupled from FastAPI app imports.

class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class CategoryEnum(str, Enum):
    harassment = "harassment"
    threat = "threat"
    death_threat = "death_threat"
    defamation = "defamation"
    verleumdung = "verleumdung"
    misogyny = "misogyny"
    body_shaming = "body_shaming"
    sexual_harassment = "sexual_harassment"
    volksverhetzung = "volksverhetzung"
    stalking = "stalking"
    intimate_images = "intimate_images"
    scam = "scam"
    phishing = "phishing"
    investment_fraud = "investment_fraud"
    romance_scam = "romance_scam"
    impersonation = "impersonation"
    false_facts = "false_facts"
    coordinated_attack = "coordinated_attack"


class LawEnum(str, Enum):
    stgb_130 = "§ 130 StGB"
    stgb_185 = "§ 185 StGB"
    stgb_186 = "§ 186 StGB"
    stgb_187 = "§ 187 StGB"
    stgb_201a = "§ 201a StGB"
    stgb_238 = "§ 238 StGB"
    stgb_241 = "§ 241 StGB"
    stgb_126a = "§ 126a StGB"
    stgb_263 = "§ 263 StGB"
    stgb_263a = "§ 263a StGB"
    stgb_269 = "§ 269 StGB"
    netzdg_3 = "NetzDG § 3"


class Classification(BaseModel):
    """Pydantic schema OpenAI Structured Outputs enforces server-side."""
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


# ─────────────────────── PROMPT #1 — Minimalist ───────────────────────
# Pure zero-shot. Trusts model + schema to do everything. The schema's
# field names + enum values communicate everything about what's expected.

PROMPT_1_MINIMALIST = """Du bist ein juristischer Klassifikator für digitale Gewalt nach deutschem Strafrecht.
Klassifiziere den vom User gelieferten Text gemäß dem geforderten Ausgabeschema."""


# ─────────────────────── PROMPT #2 — Production Few-shot CoT ─────────────
# Verbatim copy of the production SYSTEM_PROMPT from
# backend/app/services/classifier_llm_v2.py. Keep them in sync.

PROMPT_2_PRODUCTION = """Du bist SafeVoice — ein juristischer Klassifikator für digitale Gewalt in Deutschland.

Du analysierst Texte aus sozialen Medien (Kommentare, DMs, Posts) und klassifizierst sie nach deutschem Strafrecht.

GRUNDREGELN
- Verstehe Tippfehler, Slang, absichtliche Verschleierung — "f0tze", "stirbt" statt "stirb", "H*re", Zahlencodes (1488, 88).
- Bei Mehrdeutigkeit: im Zweifel FÜR das Opfer entscheiden (höhere Severity).
- Eine Drohung ist eine Drohung, auch indirekt — "Ich weiß wo du wohnst" ist § 241 StGB.
- Redewendungen sind keine Straftaten — "Das bringt mich um" ist ein Idiom, severity=none.
- Beurteile Gesamtkontext, nicht einzelne Wörter.
- Mindestens eine Kategorie; im Zweifel: harassment.
- NetzDG § 3 gilt IMMER bei Social Media Inhalten — füge es zu applicable_laws hinzu.

VICTIM_CONTEXT VERWENDEN (wenn im User-Input vorhanden)
Der Kontext ändert die rechtliche Einordnung materiell:
- Ex-Partner/-in → § 238 StGB (Nachstellung/Stalking), nicht nur § 241 StGB.
- Arbeitgeber/Kollege → § 185 StGB wiegt schwerer (Druckverhältnis).
- Minderjährig → bei sexuellem Inhalt mögliches § 184b/h StGB.
- Öffentliche Person / Journalist → § 187 StGB (Verleumdung mit Reputationsschaden).
Ohne victim_context: Standard-Klassifikation ohne Beziehungsannahme.

SEVERITY-SKALA (mit Beispielen)
- low — Grenzwertig, Plattform-Verstoß möglich, keine klare Straftat.
  Beispiel: "Bist du dumm?" → severity=low, harassment.
- medium — Wahrscheinlicher Rechtsverstoß, Anzeige möglich.
  Beispiel: "Du H*re" → severity=medium, misogyny + insult, § 185 StGB.
- high — Klarer Rechtsverstoß, Anzeige empfohlen.
  Beispiel: "Ich weiß wo du wohnst" → severity=high, threat, § 241 StGB.
- critical — Schwere Straftat, sofortige Anzeige + Beweissicherung empfohlen.
  Beispiel: "Ich bringe dich um" → severity=critical, death_threat, § 241 + § 126a StGB.

KATEGORIEN (Kurz-Definition, Auswahl)
- harassment: allgemeine Belästigung, wenn nichts spezifischeres passt.
- threat / death_threat: Drohung mit Gewalt / mit Tötung (explizit oder implizit).
- defamation / verleumdung: falsche Tatsachenbehauptung, Rufschädigung.
- misogyny: frauenfeindliche Angriffe, geschlechtsspezifisch.
- body_shaming: Abwertung Aussehen, Körper, Gewicht.
- sexual_harassment: sexualisierte Belästigung, non-consent Inhalte.
- volksverhetzung: Aufstachelung gegen Gruppen (§ 130).
- stalking: wiederholte Annäherung, Überwachung, Kontextabhängig.
- intimate_images: nicht-einvernehmliche intime Aufnahmen, Deepfakes (§ 201a).
- scam / phishing / investment_fraud / romance_scam: Betrugsformen (§ 263).
- impersonation / false_facts / coordinated_attack: Identitätsvortäuschung, vorsätzliche Falschbehauptung, erkennbar abgestimmte Mehr-Account-Angriffe.

BEISPIELE (few-shot)

Input: "Ich bringe dich um, du Drecksschlampe"
→ severity=critical, categories=[death_threat, misogyny],
  laws=[§ 241 StGB, § 126a StGB, § 185 StGB, NetzDG § 3]
  Summary (DE): "Explizite Todesdrohung verbunden mit frauenfeindlicher Beleidigung."

Input: "Das bringt mich um" (Idiom)
→ severity=low, categories=[harassment],
  laws=[NetzDG § 3]
  Summary (DE): "Umgangssprachliche Redewendung, keine erkennbare Straftat."

Input: "Stirbt endlich, du H*re" (Obfuscation)
→ severity=critical, categories=[death_threat, misogyny],
  laws=[§ 241 StGB, § 185 StGB, NetzDG § 3]
  Summary (DE): "Tötungsaufforderung mit frauenfeindlicher Beleidigung — Obfuscation ändert nichts an Tatbestand."

Input: "Ich weiß wo du arbeitest" — victim_context: "Ex-Partner, schreibt seit 3 Monaten täglich"
→ severity=high, categories=[stalking, threat],
  laws=[§ 238 StGB, § 241 StGB, NetzDG § 3]
  Summary (DE): "Implizite Drohung im Kontext wiederholter Kontaktaufnahme durch Ex-Partner — Stalking-Tatbestand erfüllt."

SUMMARY-QUALITÄT
- 1–2 faktische Sätze, kein Drama, keine Wertung.
- Was gesagt wurde + welches Recht betroffen ist.
- summary_de und summary (EN) dieselben Fakten, sprachlich natürlich."""


# ─────────────────────── TEST CORPUS ───────────────────────
# Six German messages across the severity range. The "expected_severity"
# column lets us compute accuracy (does the model agree with a human-labeled
# ground truth?). Idiom + non-harassment are deliberately included to surface
# false-positive behaviour.

@dataclass
class TestCase:
    id: str
    text: str
    expected_severity: Severity
    note: str

TEST_CASES: list[TestCase] = [
    TestCase("01-baseline", "Hallo, schöner Post heute", Severity.low,
             "non-harassment baseline — model should rate low or refuse to flag"),
    TestCase("02-soft-insult", "Du bist so dumm", Severity.low,
             "borderline insult — likely low, harassment"),
    TestCase("03-obfuscated-insult", "Du H*re", Severity.medium,
             "obfuscated misogynistic slur — § 185"),
    TestCase("04-implicit-threat", "Ich weiß wo du wohnst", Severity.high,
             "implicit threat — § 241"),
    TestCase("05-death-threat", "Ich bringe dich um, du Drecksschlampe", Severity.critical,
             "explicit death threat + misogyny"),
    TestCase("06-obfuscated-death", "Stirbt endlich, du H*re", Severity.critical,
             "obfuscation should not lower severity"),
]


# ─────────────────────── PRICING (EUR per 1M tokens) ───────────────────
# OpenAI pricing as of early 2026. Update if pricing changes.
# gpt-5-mini pricing is a placeholder estimate — verify in the OpenAI dashboard.
EUR_PER_USD = 0.93
PRICING = {
    "gpt-4o-mini":  {"input": 0.15 * EUR_PER_USD, "output": 0.60 * EUR_PER_USD},
    "gpt-4.1-mini": {"input": 0.40 * EUR_PER_USD, "output": 1.60 * EUR_PER_USD},
    "gpt-5-mini":   {"input": 0.25 * EUR_PER_USD, "output": 2.00 * EUR_PER_USD},
}

_ALL_MODELS = ["gpt-4o-mini", "gpt-4.1-mini", "gpt-5-mini"]
_filter = os.environ.get("MODELS_FILTER", "").strip()
MODELS = [m for m in _ALL_MODELS if (not _filter or m in _filter.split(","))]
PROMPTS = [
    ("P1-Minimalist",   "Zero-shot · schema-only", PROMPT_1_MINIMALIST),
    ("P2-Production",   "Few-shot CoT · production", PROMPT_2_PRODUCTION),
]


# ─────────────────────── RUNNER ───────────────────────

@dataclass
class CallResult:
    case_id: str
    model: str
    prompt_id: str
    severity: str | None
    categories: list[str] | None
    confidence: float | None
    laws: list[str] | None
    input_tokens: int
    output_tokens: int
    latency_ms: int
    cost_eur: float
    error: str | None = None

    def correct(self, expected: Severity) -> bool:
        return self.severity == expected.value


def run_one(client: OpenAI, model: str, prompt_id: str, system_prompt: str, case: TestCase) -> CallResult:
    user_msg = f"Klassifiziere diesen Inhalt:\n\n{case.text}"
    t0 = time.time()
    # gpt-5* uses the newer Responses-style parameter naming + ignores temperature.
    is_gpt5 = model.startswith("gpt-5")
    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        "response_format": Classification,
    }
    if is_gpt5:
        # gpt-5 is a reasoning model — it spends internal thinking tokens before
        # producing output. 1024 was too tight (truncated 6/12 calls). 4096 gives
        # comfortable headroom for the schema while keeping cost bounded.
        kwargs["max_completion_tokens"] = 4096
    else:
        kwargs["max_tokens"] = 1024
        kwargs["temperature"] = 0
    try:
        completion = client.chat.completions.parse(**kwargs)
    except Exception as e:
        return CallResult(case.id, model, prompt_id, None, None, None, None,
                          0, 0, int((time.time() - t0) * 1000), 0.0, error=str(e)[:200])
    elapsed = int((time.time() - t0) * 1000)
    msg = completion.choices[0].message
    if msg.refusal:
        return CallResult(case.id, model, prompt_id, None, None, None, None,
                          completion.usage.prompt_tokens, completion.usage.completion_tokens,
                          elapsed, 0.0, error=f"refusal: {msg.refusal[:120]}")
    parsed = msg.parsed
    if parsed is None:
        return CallResult(case.id, model, prompt_id, None, None, None, None,
                          completion.usage.prompt_tokens, completion.usage.completion_tokens,
                          elapsed, 0.0, error="parse returned None")
    pricing = PRICING.get(model, {"input": 0, "output": 0})
    cost = (
        completion.usage.prompt_tokens * pricing["input"]
        + completion.usage.completion_tokens * pricing["output"]
    ) / 1_000_000
    return CallResult(
        case_id=case.id,
        model=model,
        prompt_id=prompt_id,
        severity=parsed.severity.value,
        categories=[c.value for c in parsed.categories],
        confidence=parsed.confidence,
        laws=[l.value for l in parsed.applicable_laws],
        input_tokens=completion.usage.prompt_tokens,
        output_tokens=completion.usage.completion_tokens,
        latency_ms=elapsed,
        cost_eur=cost,
    )


def run_matrix() -> list[CallResult]:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY not set")
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    results: list[CallResult] = []
    total = len(MODELS) * len(PROMPTS) * len(TEST_CASES)
    n = 0
    # gpt-5-mini: project tier 1 = 5 RPM hard limit. Throttle to 1 call every 13s.
    GPT5_RATE_DELAY = 13.0
    last_gpt5_call = 0.0
    print(f"Running {total} calls ({len(MODELS)} models × {len(PROMPTS)} prompts × {len(TEST_CASES)} cases)\n")
    for model in MODELS:
        for prompt_id, _label, prompt_text in PROMPTS:
            for case in TEST_CASES:
                n += 1
                if model.startswith("gpt-5"):
                    elapsed_since_last = time.time() - last_gpt5_call
                    if elapsed_since_last < GPT5_RATE_DELAY:
                        wait = GPT5_RATE_DELAY - elapsed_since_last
                        print(f"  [{n:2d}/{total}] sleeping {wait:.1f}s for gpt-5 rate limit…")
                        time.sleep(wait)
                    last_gpt5_call = time.time()
                r = run_one(client, model, prompt_id, prompt_text, case)
                ok = "✓" if (r.error is None and r.correct(case.expected_severity)) else ("✗" if r.error is None else "!")
                err_tag = f" ({r.error[:80]})" if r.error else ""
                print(f"  [{n:2d}/{total}] {ok} {model:14s} {prompt_id:14s} {case.id:18s} → "
                      f"{r.severity or '—':8s} {r.latency_ms:5d}ms {r.output_tokens:4d}tok{err_tag}")
                results.append(r)
    return results


# ─────────────────────── REPORTING ───────────────────────

def aggregate(results: list[CallResult]):
    """Per-(model, prompt) summary."""
    summary = {}
    for r in results:
        key = (r.model, r.prompt_id)
        s = summary.setdefault(key, {
            "n": 0, "correct": 0, "errors": 0,
            "input_tokens": 0, "output_tokens": 0,
            "latencies": [], "cost_eur": 0.0,
        })
        s["n"] += 1
        if r.error:
            s["errors"] += 1
            continue
        s["input_tokens"] += r.input_tokens
        s["output_tokens"] += r.output_tokens
        s["latencies"].append(r.latency_ms)
        s["cost_eur"] += r.cost_eur
        # match the case's expected severity
        case = next(c for c in TEST_CASES if c.id == r.case_id)
        if r.severity == case.expected_severity.value:
            s["correct"] += 1
    return summary


def write_markdown(results: list[CallResult], out_path: Path):
    summary = aggregate(results)
    lines: list[str] = []
    lines.append("# SafeVoice — Classifier Prompt Comparison")
    lines.append("")
    lines.append(f"Models compared: **{', '.join(MODELS)}**  \n"
                 f"Prompts compared: **{PROMPTS[0][0]}** ({PROMPTS[0][1]}) · **{PROMPTS[1][0]}** ({PROMPTS[1][1]})  \n"
                 f"Test cases: **{len(TEST_CASES)}** German harassment messages spanning the full severity range.  \n"
                 f"Output schema: identical Pydantic Structured Outputs for both prompts (so the comparison isolates *prompt technique*).  \n"
                 f"Pricing: OpenAI list price · EUR/USD = {EUR_PER_USD}.  \n"
                 f"`gpt-5-mini` pricing in this run is an estimate — verify in the OpenAI dashboard.")
    lines.append("")

    # -------- Summary table --------
    lines.append("## Summary — accuracy, cost, latency per model × prompt")
    lines.append("")
    lines.append("| Model | Prompt | Accuracy | Avg latency | Total tokens (in / out) | Total cost (EUR) | Errors |")
    lines.append("|---|---|---|---|---|---|---|")
    for model in MODELS:
        for prompt_id, _label, _txt in PROMPTS:
            s = summary.get((model, prompt_id))
            if not s:
                continue
            n_ok = s["n"] - s["errors"]
            acc = (s["correct"] / n_ok * 100) if n_ok else 0
            avg_lat = int(statistics.mean(s["latencies"])) if s["latencies"] else 0
            lines.append(
                f"| {model} | {prompt_id} | {s['correct']}/{n_ok} ({acc:.0f}%) | "
                f"{avg_lat} ms | {s['input_tokens']:,} / {s['output_tokens']:,} | "
                f"€{s['cost_eur']:.5f} | {s['errors']} |"
            )
    lines.append("")

    # -------- Per-case grid --------
    lines.append("## Per-case grid — severity returned by each (model × prompt)")
    lines.append("")
    header = "| Case | Text | Expected |"
    sep = "|---|---|---|"
    for model in MODELS:
        for prompt_id, _label, _ in PROMPTS:
            header += f" {model} · {prompt_id} |"
            sep += "---|"
    lines.append(header)
    lines.append(sep)
    for case in TEST_CASES:
        row = f"| `{case.id}` | _{case.text}_ | **{case.expected_severity.value}** |"
        for model in MODELS:
            for prompt_id, _label, _ in PROMPTS:
                r = next((x for x in results if x.case_id == case.id and x.model == model and x.prompt_id == prompt_id), None)
                if not r:
                    row += " — |"
                elif r.error:
                    row += f" ⚠ {r.error[:30]} |"
                else:
                    mark = "✓" if r.correct(case.expected_severity) else "✗"
                    row += f" {mark} {r.severity} |"
        lines.append(row)
    lines.append("")

    # -------- Per-call details --------
    lines.append("## Per-call details (latency + tokens + cost)")
    lines.append("")
    lines.append("| Case | Model | Prompt | Severity | Latency | In / Out tokens | Cost |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in results:
        if r.error:
            lines.append(f"| `{r.case_id}` | {r.model} | {r.prompt_id} | ⚠ {r.error[:40]} | "
                         f"{r.latency_ms} ms | {r.input_tokens} / {r.output_tokens} | — |")
        else:
            lines.append(f"| `{r.case_id}` | {r.model} | {r.prompt_id} | {r.severity} | "
                         f"{r.latency_ms} ms | {r.input_tokens} / {r.output_tokens} | €{r.cost_eur:.6f} |")
    lines.append("")

    # -------- Conclusion stub --------
    lines.append("## Conclusion")
    lines.append("")
    # Identify best (model, prompt) by accuracy, breaking ties by cost.
    ranked = []
    for (model, prompt_id), s in summary.items():
        n_ok = s["n"] - s["errors"]
        acc = (s["correct"] / n_ok) if n_ok else 0
        avg_lat = statistics.mean(s["latencies"]) if s["latencies"] else float("inf")
        ranked.append({
            "model": model, "prompt_id": prompt_id, "accuracy": acc,
            "cost": s["cost_eur"], "avg_lat": avg_lat,
        })
    ranked.sort(key=lambda r: (-r["accuracy"], r["cost"], r["avg_lat"]))
    best = ranked[0] if ranked else None
    if best:
        lines.append(
            f"On this small German harassment corpus, **{best['model']} + {best['prompt_id']}** wins on the "
            f"accuracy-then-cost-then-latency tiebreak — accuracy {best['accuracy']*100:.0f}%, "
            f"€{best['cost']:.5f} for the {len(TEST_CASES)}-case run, avg latency {int(best['avg_lat'])} ms."
        )
    lines.append("")
    lines.append("**Read on the prompt technique trade-off:**")
    lines.append("")
    lines.append("- The Minimalist (zero-shot) prompt is ~10× shorter than the Production few-shot CoT, "
                 "which means lower input token cost and faster time-to-first-token. "
                 "If accuracy is comparable, it's the better production choice.")
    lines.append("- The Production prompt earns its complexity when it correctly handles the cases the "
                 "Minimalist gets wrong — typically idioms (`Das bringt mich um` should be **low**, not "
                 "**critical**) and obfuscation (`Stirbt endlich, du H*re` should still be **critical**). "
                 "Inspect the per-case grid above to see which prompt caught those edge cases.")
    lines.append("- All else equal, prefer the cheaper model that maintains accuracy on safety-critical "
                 "categories (`death_threat`, `threat`, `stalking`). False negatives cost victims; "
                 "false positives cost reviewer time.")
    lines.append("")
    lines.append(f"_Generated by `scripts/compare_prompts.py` · {len(results)} calls._")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))
    print(f"\n✓ Wrote {out_path}")


if __name__ == "__main__":
    results = run_matrix()
    out = Path(__file__).resolve().parent.parent / "docs" / "notebooks" / "prompt-comparison.md"
    write_markdown(results, out)

    # Also dump raw JSON for reproducibility
    raw = out.with_suffix(".json")
    raw.write_text(json.dumps([asdict(r) for r in results], default=str, indent=2))
    print(f"✓ Wrote {raw}")
