"""
AI legal analysis — Claude API for nuanced legal reasoning.
Goes beyond classification to provide:
- Legal strategy recommendations
- Precedent-aware analysis
- Cross-reference between evidence items
- Risk assessment for victim
"""

import json
import os
import logging
from anthropic import Anthropic
from app.models.evidence import Case, EvidenceItem, ClassificationResult

logger = logging.getLogger(__name__)

LEGAL_SYSTEM_PROMPT = """You are a German digital law expert specialising in digital harassment, cybercrime, and victim protection. You provide detailed legal analysis of evidence in cases of digital violence.

Your analysis must be:
- Legally precise (cite specific paragraphs)
- Victim-centered (focus on what helps the victim)
- Actionable (concrete next steps)
- Bilingual (German primary, English secondary)

You are NOT a lawyer and must include a disclaimer. But your analysis should be thorough enough that a real lawyer can use it as a starting point.

Respond with valid JSON only."""


def is_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def analyze_case_legally(case: Case) -> dict | None:
    """
    Deep legal analysis of an entire case using Claude API.
    Returns structured legal assessment or None if API unavailable.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_analysis(case)

    try:
        client = Anthropic(api_key=api_key)

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

        prompt = f"""Analyze this digital harassment case:

Case ID: {case.id}
Title: {case.title}
Overall severity: {case.overall_severity.value}
Victim context: {case.victim_context or 'Not provided'}

Evidence ({len(case.evidence_items)} items):
{json.dumps(evidence_summary, indent=2, ensure_ascii=False)}

Provide your analysis as JSON:
{{
  "legal_assessment_de": "German-language overall legal assessment (2-3 paragraphs)",
  "legal_assessment_en": "English-language overall legal assessment (2-3 paragraphs)",
  "strongest_charges": [
    {{"paragraph": "§ 241 StGB", "strength": "strong/medium/weak", "reason_de": "...", "reason_en": "..."}}
  ],
  "recommended_actions": [
    {{"priority": "immediate/soon/when_ready", "action_de": "...", "action_en": "...", "deadline": "24h/7d/none"}}
  ],
  "risk_assessment": {{
    "escalation_risk": "low/medium/high",
    "reason_de": "...",
    "reason_en": "..."
  }},
  "evidence_gaps": [
    {{"gap_de": "...", "gap_en": "...", "how_to_fill_de": "...", "how_to_fill_en": "..."}}
  ],
  "cross_references": "Any connections between evidence items (patterns, escalation, coordination)",
  "disclaimer_de": "Dies ist keine Rechtsberatung. Konsultieren Sie einen Anwalt.",
  "disclaimer_en": "This is not legal advice. Consult a qualified attorney."
}}"""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=LEGAL_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

        return json.loads(raw)

    except Exception as e:
        logger.warning(f"AI legal analysis failed: {e}")
        return _fallback_analysis(case)


def analyze_single_evidence(evidence: EvidenceItem) -> dict | None:
    """Quick legal analysis of a single evidence item."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        client = Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=LEGAL_SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"""Briefly analyze this single piece of evidence:

Author: @{evidence.author_username}
Platform: {evidence.platform}
Content: "{evidence.content_text}"

Respond as JSON:
{{
  "analysis_de": "1-2 sentence German analysis",
  "analysis_en": "1-2 sentence English analysis",
  "applicable_laws": ["§ xxx StGB"],
  "severity_justification": "Why this severity level",
  "immediate_action_needed": true/false,
  "action_de": "What the victim should do",
  "action_en": "What the victim should do"
}}"""
            }],
        )

        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(raw)

    except Exception as e:
        logger.warning(f"AI evidence analysis failed: {e}")
        return None


def _fallback_analysis(case: Case) -> dict:
    """Rule-based fallback when Claude API is unavailable."""
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

    # Collect all laws
    all_laws = set()
    has_threat = False
    has_scam = False
    for ev in case.evidence_items:
        if ev.classification:
            for law in ev.classification.applicable_laws:
                all_laws.add(law.paragraph)
            if Category.THREAT in ev.classification.categories or Category.DEATH_THREAT in ev.classification.categories:
                has_threat = True
            if Category.SCAM in ev.classification.categories:
                has_scam = True

    escalation = "high" if has_threat else ("medium" if case.overall_severity == Severity.HIGH else "low")

    return {
        "legal_assessment_de": f"Dieser Fall enthält {len(case.evidence_items)} Beweismittel mit Schweregrad {case.overall_severity.value}. "
            f"Anwendbare Gesetze: {', '.join(sorted(all_laws))}. "
            f"Eine detaillierte KI-Analyse ist verfügbar, wenn ANTHROPIC_API_KEY gesetzt ist.",
        "legal_assessment_en": f"This case contains {len(case.evidence_items)} evidence items at {case.overall_severity.value} severity. "
            f"Applicable laws: {', '.join(sorted(all_laws))}. "
            f"Detailed AI analysis available when ANTHROPIC_API_KEY is set.",
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
