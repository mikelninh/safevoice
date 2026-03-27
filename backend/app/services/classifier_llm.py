"""
LLM-based classifier using Claude API.
Primary classifier — most accurate, understands context and nuance.
Falls back gracefully if API key is missing or call fails.
"""

import json
import os
import logging
from anthropic import Anthropic
from app.models.evidence import (
    ClassificationResult, Severity, Category, GermanLaw
)
from app.data.mock_data import (
    LAW_185, LAW_186, LAW_241, LAW_126A, NETZ_DG,
    LAW_263, LAW_263A, LAW_269
)

logger = logging.getLogger(__name__)

# Map paragraph strings to law objects for lookup
LAW_MAP = {
    "§ 185 StGB": LAW_185,
    "§ 186 StGB": LAW_186,
    "§ 241 StGB": LAW_241,
    "§ 126a StGB": LAW_126A,
    "NetzDG § 3": NETZ_DG,
    "§ 263 StGB": LAW_263,
    "§ 263a StGB": LAW_263A,
    "§ 269 StGB": LAW_269,
}

CATEGORY_MAP = {c.value: c for c in Category}
SEVERITY_MAP = {s.value: s for s in Severity}

SYSTEM_PROMPT = """You are SafeVoice's legal classification engine. You analyse digital content (social media posts, DMs, comments) for harassment, threats, scams, and other offenses under German criminal law.

Your job:
1. Classify the content into one or more categories
2. Assess severity (low / medium / high / critical)
3. Map to applicable German criminal law paragraphs
4. Provide a concise summary in BOTH English and German
5. Assess whether immediate action is needed (police report, evidence preservation)

Categories (use value strings exactly):
- harassment, threat, death_threat, defamation, misogyny, body_shaming
- coordinated_attack, false_facts, sexual_harassment
- scam, phishing, investment_fraud, romance_scam, impersonation

Applicable German laws (use paragraph strings exactly):
- § 185 StGB (Beleidigung / Insult)
- § 186 StGB (Üble Nachrede / Defamation)
- § 241 StGB (Bedrohung / Threat)
- § 126a StGB (Strafbare Bedrohung / Criminal threat)
- § 263 StGB (Betrug / Fraud)
- § 263a StGB (Computerbetrug / Computer fraud)
- § 269 StGB (Fälschung beweiserheblicher Daten / Data falsification)
- NetzDG § 3 (Network Enforcement Act — always include for social media content)

Respond with ONLY valid JSON in this exact schema:
{
  "severity": "low|medium|high|critical",
  "categories": ["category1", "category2"],
  "confidence": 0.0-1.0,
  "requires_immediate_action": true/false,
  "summary": "English summary",
  "summary_de": "German summary",
  "applicable_laws": ["§ 185 StGB", "NetzDG § 3"],
  "potential_consequences": "English consequences",
  "potential_consequences_de": "German consequences"
}

Be precise. Be victim-centered. When in doubt about severity, err on the side of protecting the victim.
Never minimise threats. A threat is a threat even when phrased indirectly."""


def is_available() -> bool:
    """Check if Claude API is configured."""
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def classify_with_llm(text: str) -> ClassificationResult | None:
    """
    Classify text using Claude API.
    Returns None if API is unavailable or call fails.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.info("ANTHROPIC_API_KEY not set, skipping LLM classifier")
        return None

    try:
        client = Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Classify this content:\n\n{text}"
                }
            ]
        )

        raw = message.content[0].text.strip()
        # Handle markdown code blocks
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            raw = raw.rsplit("```", 1)[0]

        data = json.loads(raw)
        return _parse_result(data)

    except Exception as e:
        logger.warning(f"LLM classifier failed: {e}")
        return None


def _parse_result(data: dict) -> ClassificationResult:
    """Parse JSON response into ClassificationResult."""
    severity = SEVERITY_MAP.get(data["severity"], Severity.MEDIUM)

    categories = []
    for cat_str in data.get("categories", []):
        cat = CATEGORY_MAP.get(cat_str)
        if cat:
            categories.append(cat)
    if not categories:
        categories = [Category.HARASSMENT]

    applicable_laws = []
    for law_str in data.get("applicable_laws", []):
        law = LAW_MAP.get(law_str)
        if law:
            applicable_laws.append(law)
    # Always include NetzDG for social media
    if NETZ_DG not in applicable_laws:
        applicable_laws.append(NETZ_DG)

    confidence = min(max(float(data.get("confidence", 0.85)), 0.0), 1.0)

    return ClassificationResult(
        severity=severity,
        categories=categories,
        confidence=confidence,
        requires_immediate_action=data.get("requires_immediate_action", False),
        summary=data.get("summary", "Content analysed."),
        summary_de=data.get("summary_de", "Inhalt analysiert."),
        applicable_laws=applicable_laws,
        potential_consequences=data.get("potential_consequences", ""),
        potential_consequences_de=data.get("potential_consequences_de", "")
    )
