"""
AI legal analysis — the RAG layer.

Retrieves all evidence + classifications for a case, structures them as a
context block, sends to OpenAI `gpt-4o-mini` with Structured Outputs for
aggregate legal reasoning across the whole case.

- **Retrieve** · `case.evidence_items` + each item's classification
- **Augment** · evidence_summary block composed into the user prompt
- **Generate** · `client.chat.completions.parse()` with Pydantic schema

Moved from Anthropic to OpenAI on 2026-04-20 — aligns with the classifier
stack (one provider, one key, Structured Outputs everywhere). The Anthropic
SDK is no longer required for SafeVoice's AI layer.
"""

from __future__ import annotations

import json
import os
import logging
from typing import Literal

try:
    from openai import OpenAI
    _openai_installed = True
except ImportError:
    _openai_installed = False

from pydantic import BaseModel, ConfigDict, Field

from app.models.evidence import Case, EvidenceItem

logger = logging.getLogger(__name__)


LEGAL_SYSTEM_PROMPT = """You are a German digital law expert specialising in digital harassment, cybercrime, and victim protection. You provide detailed legal analysis of evidence in cases of digital violence.

Your analysis must be:
- Legally precise (cite specific paragraphs — § 185, § 241, § 238, § 126a, NetzDG § 3, etc.)
- Victim-centered (focus on what helps the victim, not abstract theory)
- Actionable (concrete next steps with timeframes)
- Bilingual (German as primary, English as secondary, both must be present)

You are NOT a lawyer. Always include a disclaimer in both languages. Your analysis is thorough enough that a real lawyer can use it as a starting point — and clear enough that a non-lawyer victim can understand what to do next."""


# ── Pydantic schemas — server-side-enforced by OpenAI Structured Outputs ────

class Charge(BaseModel):
    model_config = ConfigDict(extra="forbid")
    paragraph: str = Field(..., description="e.g. '§ 241 StGB' or 'NetzDG § 3'")
    strength: Literal["strong", "medium", "weak"]
    reason_de: str
    reason_en: str


class Action(BaseModel):
    model_config = ConfigDict(extra="forbid")
    priority: Literal["immediate", "soon", "when_ready"]
    action_de: str
    action_en: str
    deadline: Literal["24h", "7d", "none"]


class RiskAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    escalation_risk: Literal["low", "medium", "high"]
    reason_de: str
    reason_en: str


class EvidenceGap(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gap_de: str
    gap_en: str
    how_to_fill_de: str
    how_to_fill_en: str


class CaseAnalysis(BaseModel):
    """Full case-level legal assessment — the structured output of analyze_case_legally."""
    model_config = ConfigDict(extra="forbid")

    legal_assessment_de: str
    legal_assessment_en: str
    strongest_charges: list[Charge]
    recommended_actions: list[Action]
    risk_assessment: RiskAssessment
    evidence_gaps: list[EvidenceGap]
    cross_references: str
    disclaimer_de: str
    disclaimer_en: str


class SingleEvidenceAnalysis(BaseModel):
    """Lightweight legal lens on a single evidence item."""
    model_config = ConfigDict(extra="forbid")

    analysis_de: str
    analysis_en: str
    applicable_laws: list[str]
    severity_justification: str
    immediate_action_needed: bool
    action_de: str
    action_en: str


# ── Public API ─────────────────────────────────────────────────────────────

def is_available() -> bool:
    """Whether the Legal AI layer can run (SDK installed + key present)."""
    return _openai_installed and bool(os.environ.get("OPENAI_API_KEY"))


def analyze_case_legally(case: Case) -> dict | None:
    """Deep legal analysis of an entire case.

    Returns a dict shaped like `CaseAnalysis`, or a rule-based fallback when
    the OpenAI layer isn't available. Never returns None — callers rely on
    the structured shape either way.
    """
    if not is_available():
        return _fallback_analysis(case)

    try:
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

        # RETRIEVE + AUGMENT — pull evidence + classifications, structure as context
        evidence_summary = []
        for ev in case.evidence_items:
            entry = {
                "author": ev.author_username,
                "platform": ev.platform,
                "content": ev.content_text[:500],
                "captured_at": str(ev.captured_at),
            }
            if ev.classification:
                entry["severity"] = ev.classification.severity.value
                entry["categories"] = [c.value for c in ev.classification.categories]
                entry["laws"] = [l.paragraph for l in ev.classification.applicable_laws]
            evidence_summary.append(entry)

        user_prompt = f"""Analyze this digital harassment case.

Case ID: {case.id}
Title: {case.title}
Overall severity: {case.overall_severity.value}
Victim context: {case.victim_context or 'Not provided'}

Evidence ({len(case.evidence_items)} items):
{json.dumps(evidence_summary, indent=2, ensure_ascii=False)}

Produce a structured legal assessment. Use German as the primary language for
the `_de` fields and English as the secondary for `_en` fields. Include at
least one item in `recommended_actions`. Always include both disclaimers."""

        # GENERATE — schema-enforced by OpenAI
        completion = client.chat.completions.parse(
            model="gpt-4o-mini",
            temperature=0.2,
            max_tokens=2048,
            messages=[
                {"role": "system", "content": LEGAL_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format=CaseAnalysis,
        )

        msg = completion.choices[0].message
        if msg.refusal:
            logger.warning("OpenAI refused legal analysis: %s", msg.refusal)
            return _fallback_analysis(case)

        parsed = msg.parsed
        if parsed is None:
            logger.warning("OpenAI returned no parsed result despite no refusal")
            return _fallback_analysis(case)

        return parsed.model_dump()

    except Exception as e:
        logger.warning("Legal AI failed: %s", e)
        return _fallback_analysis(case)


def analyze_single_evidence(evidence: EvidenceItem) -> dict | None:
    """Quick legal analysis of a single evidence item. Returns None on failure."""
    if not is_available():
        return None

    try:
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        user_prompt = f"""Briefly analyze this single piece of evidence under German criminal law.

Author: @{evidence.author_username}
Platform: {evidence.platform}
Content: "{evidence.content_text}"

Produce a structured legal-lens analysis."""

        completion = client.chat.completions.parse(
            model="gpt-4o-mini",
            temperature=0.2,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": LEGAL_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format=SingleEvidenceAnalysis,
        )

        msg = completion.choices[0].message
        if msg.refusal or msg.parsed is None:
            return None
        return msg.parsed.model_dump()

    except Exception as e:
        logger.warning("Single-evidence legal AI failed: %s", e)
        return None


# ── Fallback — rule-based analysis when OpenAI is unavailable ──────────────

def _fallback_analysis(case: Case) -> dict:
    """Honest rule-based analysis for when the Legal AI layer is unavailable.

    Still conforms to the `CaseAnalysis` shape so API consumers can rely on
    the structure. Names OPENAI_API_KEY explicitly so the operator knows what
    to provide if they want the full AI analysis.
    """
    from app.models.evidence import Severity, Category

    actions = []
    if case.overall_severity in (Severity.CRITICAL, Severity.HIGH):
        actions.append({
            "priority": "immediate",
            "action_de": "Strafanzeige bei der Polizei erstatten (Onlinewache oder Dienststelle)",
            "action_en": "File a police report (Onlinewache or police station)",
            "deadline": "24h",
        })
        actions.append({
            "priority": "immediate",
            "action_de": "NetzDG-Meldung bei der Plattform einreichen",
            "action_en": "File NetzDG report with the platform",
            "deadline": "24h",
        })

    actions.append({
        "priority": "soon",
        "action_de": "Beratung bei HateAid (hateaid.org) oder Weisser Ring suchen",
        "action_en": "Seek counseling at HateAid (hateaid.org) or Weisser Ring",
        "deadline": "none",
    })

    all_laws = set()
    has_threat = False
    for ev in case.evidence_items:
        if ev.classification:
            for law in ev.classification.applicable_laws:
                all_laws.add(law.paragraph)
            if Category.THREAT in ev.classification.categories or Category.DEATH_THREAT in ev.classification.categories:
                has_threat = True

    escalation = "high" if has_threat else ("medium" if case.overall_severity == Severity.HIGH else "low")

    return {
        "legal_assessment_de": (
            f"Dieser Fall enthält {len(case.evidence_items)} Beweismittel mit Schweregrad "
            f"{case.overall_severity.value}. Anwendbare Gesetze: {', '.join(sorted(all_laws)) or '—'}. "
            "Eine detaillierte KI-Analyse ist verfügbar, wenn OPENAI_API_KEY gesetzt ist."
        ),
        "legal_assessment_en": (
            f"This case contains {len(case.evidence_items)} evidence items at {case.overall_severity.value} "
            f"severity. Applicable laws: {', '.join(sorted(all_laws)) or '—'}. "
            "Detailed AI analysis available when OPENAI_API_KEY is set."
        ),
        "strongest_charges": [
            {"paragraph": p, "strength": "medium", "reason_de": "Basierend auf Regelanalyse", "reason_en": "Based on rule analysis"}
            for p in sorted(all_laws) if p != "NetzDG § 3"
        ],
        "recommended_actions": actions,
        "risk_assessment": {
            "escalation_risk": escalation,
            "reason_de": "Basierend auf erkannten Bedrohungs- und Eskalationsmustern" if has_threat else "Basierend auf Schweregrad",
            "reason_en": "Based on detected threat and escalation patterns" if has_threat else "Based on severity level",
        },
        "evidence_gaps": [],
        "cross_references": "",
        "disclaimer_de": "Dies ist keine Rechtsberatung. Für individuelle Beratung wenden Sie sich an HateAid (hateaid.org) oder einen Anwalt.",
        "disclaimer_en": "This is not legal advice. For individual advice, contact HateAid (hateaid.org) or a qualified attorney.",
    }
