"""
LLM-based classifier using OpenAI API with Structured Output.
Primary classifier — understands context, typos, slang, obfuscation.
Falls back gracefully if API key is missing or call fails.
"""

import json
import os
import logging

try:
    from openai import OpenAI
    _openai_installed = True
except ImportError:
    _openai_installed = False

from app.models.evidence import (
    ClassificationResult, Severity, Category, GermanLaw
)
from app.data.mock_data import (
    LAW_185, LAW_186, LAW_187, LAW_241, LAW_126A, LAW_130, LAW_201A, LAW_238,
    NETZ_DG, LAW_263, LAW_263A, LAW_269
)

logger = logging.getLogger(__name__)

# All 12 laws mapped
LAW_MAP = {
    "§ 130 StGB": LAW_130,
    "§ 185 StGB": LAW_185,
    "§ 186 StGB": LAW_186,
    "§ 187 StGB": LAW_187,
    "§ 201a StGB": LAW_201A,
    "§ 238 StGB": LAW_238,
    "§ 241 StGB": LAW_241,
    "§ 126a StGB": LAW_126A,
    "§ 263 StGB": LAW_263,
    "§ 263a StGB": LAW_263A,
    "§ 269 StGB": LAW_269,
    "NetzDG § 3": NETZ_DG,
}

CATEGORY_MAP = {c.value: c for c in Category}
SEVERITY_MAP = {s.value: s for s in Severity}

SYSTEM_PROMPT = """Du bist SafeVoice — ein juristischer Klassifikator für digitale Gewalt in Deutschland.

Du analysierst Texte aus sozialen Medien (Kommentare, DMs, Posts) und klassifizierst sie nach deutschem Strafrecht.

WICHTIG:
- Verstehe Tippfehler, Slang, absichtliche Verschleierung (z.B. "f0tze", "stirbt" statt "stirb")
- Wenn unklar: im Zweifel FÜR das Opfer entscheiden (höhere Severity)
- Eine Drohung ist eine Drohung, auch wenn sie indirekt formuliert ist
- Beachte den Gesamtkontext, nicht einzelne Wörter

KATEGORIEN (nutze exakt diese Werte):
- harassment: Allgemeine Belästigung, Beleidigung
- threat: Bedrohung (nicht tödlich)
- death_threat: Todesdrohung oder Aufforderung zum Suizid
- defamation: Üble Nachrede (§186)
- verleumdung: Wissentlich falsche Behauptungen (§187)
- misogyny: Frauenfeindliche Inhalte
- body_shaming: Körperbezogene Beleidigung
- sexual_harassment: Sexuelle Belästigung
- volksverhetzung: Hassrede gegen geschützte Gruppen (§130)
- stalking: Nachstellung, unerwünschter Kontakt (§238)
- intimate_images: Nicht einvernehmliche intime Bilder/Deepfakes (§201a)
- scam: Betrug allgemein
- phishing: Phishing-Versuch
- investment_fraud: Investitionsbetrug
- romance_scam: Romance Scam
- impersonation: Identitätsdiebstahl
- false_facts: Falsche Tatsachenbehauptungen
- coordinated_attack: Koordinierter Angriff mehrerer Accounts

GESETZE (nutze exakt diese Paragraphen):
- § 130 StGB — Volksverhetzung (bis 5 Jahre)
- § 185 StGB — Beleidigung (bis 1 Jahr)
- § 186 StGB — Üble Nachrede (bis 1 Jahr)
- § 187 StGB — Verleumdung (bis 5 Jahre)
- § 201a StGB — Verletzung des höchstpersönlichen Lebensbereichs durch Bildaufnahmen (bis 2 Jahre)
- § 238 StGB — Nachstellung/Stalking (bis 3 Jahre)
- § 241 StGB — Bedrohung (bis 2 Jahre)
- § 126a StGB — Strafbare Bedrohung (bis 3 Jahre)
- § 263 StGB — Betrug (bis 5 Jahre)
- § 263a StGB — Computerbetrug (bis 5 Jahre)
- § 269 StGB — Fälschung beweiserheblicher Daten (bis 5 Jahre)
- NetzDG § 3 — Plattformpflicht zur Löschung (immer bei Social Media Inhalten)

SEVERITY:
- low: Grenzwertig, Verstoß gegen Nutzungsbedingungen möglich
- medium: Wahrscheinlicher Rechtsverstoß
- high: Klarer Rechtsverstoß, Anzeige empfohlen
- critical: Schwere Straftat, sofortige Anzeige + Beweissicherung

Antworte NUR mit validem JSON."""

RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "classification",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                "categories": {"type": "array", "items": {"type": "string"}},
                "confidence": {"type": "number"},
                "requires_immediate_action": {"type": "boolean"},
                "summary": {"type": "string"},
                "summary_de": {"type": "string"},
                "applicable_laws": {"type": "array", "items": {"type": "string"}},
                "potential_consequences": {"type": "string"},
                "potential_consequences_de": {"type": "string"}
            },
            "required": ["severity", "categories", "confidence", "requires_immediate_action",
                         "summary", "summary_de", "applicable_laws",
                         "potential_consequences", "potential_consequences_de"],
            "additionalProperties": False
        }
    }
}


def is_available() -> bool:
    return _openai_installed and bool(os.environ.get("OPENAI_API_KEY"))


def classify_with_llm(text: str) -> ClassificationResult | None:
    if not _openai_installed:
        return None
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=1024,
            response_format=RESPONSE_SCHEMA,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Klassifiziere diesen Inhalt:\n\n{text}"},
            ],
        )

        data = json.loads(response.choices[0].message.content)
        return _parse_result(data)

    except Exception as e:
        logger.warning(f"LLM classifier failed: {e}")
        return None


def _parse_result(data: dict) -> ClassificationResult:
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
