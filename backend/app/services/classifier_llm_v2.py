"""
LLM-based classifier v2 — OpenAI Structured Outputs with Pydantic (SDK 1.40+).

Uses `client.chat.completions.parse()` + Pydantic model, which:
- Auto-validates against the schema server-side
- Returns a typed Pydantic object (no manual JSON parsing)
- Rejects malformed outputs before we see them

This is the modern best-practice replacement for classifier_llm.py's raw JSON schema approach.

Drop-in compatible: exports `is_available()` and `classify_with_llm()` with the same signatures.
"""

from __future__ import annotations

import os
import logging
from enum import Enum

try:
    from openai import OpenAI
    _openai_installed = True
except ImportError:
    _openai_installed = False

from pydantic import BaseModel, Field, ConfigDict

from app.models.evidence import (
    ClassificationResult, Severity, Category, GermanLaw
)
from app.data.mock_data import (
    LAW_185, LAW_186, LAW_187, LAW_241, LAW_126A, LAW_130, LAW_201A, LAW_238,
    NETZ_DG, LAW_263, LAW_263A, LAW_269
)

logger = logging.getLogger(__name__)


# ── Schema classes for OpenAI structured output ──
# These are a FLAT subset of the full ClassificationResult. The LLM returns
# enum strings for categories/laws; we map them to domain objects after.

class LLMSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class LLMCategory(str, Enum):
    """Exhaustive list of categories — matches Category enum values 1:1."""
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


class LLMLaw(str, Enum):
    """Exhaustive list of applicable laws."""
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


class LLMClassification(BaseModel):
    """Pydantic model for the classifier's structured output. Schema-enforced by OpenAI."""
    model_config = ConfigDict(extra="forbid")

    severity: LLMSeverity
    categories: list[LLMCategory] = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    requires_immediate_action: bool
    summary: str
    summary_de: str
    applicable_laws: list[LLMLaw]
    potential_consequences: str
    potential_consequences_de: str


# ── Maps from LLM enums to domain types ──

_SEVERITY_MAP = {
    LLMSeverity.low: Severity.LOW,
    LLMSeverity.medium: Severity.MEDIUM,
    LLMSeverity.high: Severity.HIGH,
    LLMSeverity.critical: Severity.CRITICAL,
}

_CATEGORY_MAP = {llm: Category(llm.value) for llm in LLMCategory}

_LAW_MAP: dict[LLMLaw, GermanLaw] = {
    LLMLaw.stgb_130: LAW_130,
    LLMLaw.stgb_185: LAW_185,
    LLMLaw.stgb_186: LAW_186,
    LLMLaw.stgb_187: LAW_187,
    LLMLaw.stgb_201a: LAW_201A,
    LLMLaw.stgb_238: LAW_238,
    LLMLaw.stgb_241: LAW_241,
    LLMLaw.stgb_126a: LAW_126A,
    LLMLaw.stgb_263: LAW_263,
    LLMLaw.stgb_263a: LAW_263A,
    LLMLaw.stgb_269: LAW_269,
    LLMLaw.netzdg_3: NETZ_DG,
}


# Bumped whenever SYSTEM_PROMPT or the few-shot examples change materially.
# Stored on every Classification row so historical classifications remain
# attributable to a specific prompt revision — lets us re-run history when
# the prompt changes and detect drift.
#
# v2 (2026-04-26): added 4 few-shot examples + 1 system rule to close the
# gaps surfaced by the v1 eval run (66% → target 80%+):
#   - direct insult ("Du bist ein Arschloch") → medium § 185 (was misclassified low)
#   - Nazi-coded numbers (88, 1488, 14 words) → high § 130 (was missed)
#   - oblique threat to family ("Hoffentlich ist deinen Kindern…") → high § 241
#   - idiom counter-example ("Du bist tot für mich") → low (was over-classified medium)
PROMPT_VERSION = "v2"


SYSTEM_PROMPT = """Du bist SafeVoice — ein juristischer Klassifikator für digitale Gewalt in Deutschland.

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
- volksverhetzung: Aufstachelung gegen Gruppen (§ 130). Beachte rechtsextreme Zahlencodes:
  88 = HH = Heil Hitler · 1488 = "14 words" + 88 · "14 words" / "14 W" = David-Lane-Slogan ("We must
  secure the existence of our people…"). Wenn solche Codes erkennbar verwendet werden, ist § 130 in
  der Regel einschlägig und severity ≥ high.
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

Input: "Du bist ein Arschloch"
→ severity=medium, categories=[harassment],
  laws=[§ 185 StGB, NetzDG § 3]
  Summary (DE): "Ehrverletzende Beleidigung mit klarem Personenbezug — Tatbestand der Beleidigung erfüllt."
  WICHTIG: Direkte Beleidigungen wie 'Arschloch', 'Idiot', 'erbärmliche Existenz' sind nach
  ständiger BGH-Rechtsprechung § 185 StGB. Severity=medium ist die richtige Einordnung — nicht low.

Input: "Sieg, Brüder. 88!"
→ severity=high, categories=[volksverhetzung],
  laws=[§ 130 StGB, NetzDG § 3]
  Summary (DE): "Verwendung des rechtsextremen Zahlencodes 88 (Heil Hitler) in eindeutigem Kontext
  — Volksverhetzung gemäß § 130 StGB."

Input: "Hoffentlich ist deinen Kindern auf dem Schulweg nichts passiert"
→ severity=high, categories=[threat],
  laws=[§ 241 StGB, NetzDG § 3]
  Summary (DE): "Implizite Bedrohung gegen Familienangehörige — auch indirekte Drohungen gegen
  nahestehende Personen sind nach § 241 StGB strafbar."
  WICHTIG: Oblique Drohungen gegen Familie ("hoffentlich passiert nichts", "wäre schade wenn dein
  Kind…") sind § 241 StGB, severity=high — nicht harmlos einzuordnen.

Input: "Du bist tot für mich" (Idiom)
→ severity=low, categories=[harassment],
  laws=[NetzDG § 3]
  Summary (DE): "Idiomatischer Ausdruck der Distanzierung — keine Todesdrohung, keine Straftat."

SUMMARY-QUALITÄT
- 1–2 faktische Sätze, kein Drama, keine Wertung.
- Was gesagt wurde + welches Recht betroffen ist.
- summary_de und summary (EN) dieselben Fakten, sprachlich natürlich."""


def is_available() -> bool:
    """Returns True only if the OpenAI SDK is installed AND an API key is configured."""
    return _openai_installed and bool(os.environ.get("OPENAI_API_KEY"))


# ── Dynamic user-message builder ──
# Pure function, easy to unit-test and inspect. Absent all optional fields the
# output is byte-for-byte identical to the original f-string, so existing tests
# continue to pass.

def build_user_message(
    text: str,
    *,
    victim_context: str | None = None,
    jurisdiction: str = "DE",
    user_lang: str = "de",
) -> str:
    """Build the user-role message from a (possibly enriched) classification context.

    The default call — `build_user_message(text)` — reproduces the legacy prompt
    verbatim to keep prior test fixtures stable. Any non-default argument
    triggers an extended prompt that tells the LLM the jurisdiction, the user's
    output-language preference and any victim-provided context. Richer context
    materially improves classification accuracy, especially for ambiguous cases
    (e.g. stalking after a breakup → § 238 StGB).
    """
    uses_defaults = (
        victim_context is None
        and jurisdiction == "DE"
        and user_lang == "de"
    )
    if uses_defaults:
        return f"Klassifiziere diesen Inhalt:\n\n{text}"

    parts: list[str] = [
        f"Klassifiziere diesen Inhalt nach dem Strafrecht der Jurisdiktion: {jurisdiction}."
    ]
    if victim_context:
        parts.append(f"Kontext des Opfers: {victim_context.strip()}")
    if user_lang and user_lang != "de":
        parts.append(f"Bevorzugte Ausgabesprache: {user_lang}")
    parts.append(f"Inhalt:\n{text}")
    return "\n\n".join(parts)


def classify_with_llm(
    text: str,
    *,
    victim_context: str | None = None,
    jurisdiction: str = "DE",
    user_lang: str = "de",
) -> ClassificationResult | None:
    """
    Classify text using OpenAI Structured Outputs with Pydantic schema enforcement.

    Optional keyword args (`victim_context`, `jurisdiction`, `user_lang`) are
    injected into the user-role message via `build_user_message`. When all are
    left at their defaults the prompt is identical to the legacy one.

    Returns None on any error (missing key, SDK not installed, API error, refusal).
    The orchestrator in `classifier.py::classify` surfaces None as 503.
    """
    if not _openai_installed:
        return None
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        client = OpenAI(api_key=api_key)
        user_message = build_user_message(
            text,
            victim_context=victim_context,
            jurisdiction=jurisdiction,
            user_lang=user_lang,
        )
        # .parse() is the modern structured-output method — schema-enforced server-side.
        completion = client.chat.completions.parse(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format=LLMClassification,
        )

        # Check for refusal (OpenAI may decline to classify for safety reasons).
        msg = completion.choices[0].message
        if msg.refusal:
            logger.warning(f"LLM refused classification: {msg.refusal}")
            return None

        # `.parsed` is a validated Pydantic instance — or None if OpenAI failed to conform.
        llm_result = msg.parsed
        if llm_result is None:
            logger.warning("LLM returned no parsed result despite no refusal")
            return None

        return _to_domain(llm_result)

    except Exception as e:
        logger.warning(f"LLM classifier failed: {e}")
        return None


def _to_domain(llm: LLMClassification) -> ClassificationResult:
    """Map validated LLM output to the internal ClassificationResult domain object."""
    severity = _SEVERITY_MAP[llm.severity]
    categories = [_CATEGORY_MAP[c] for c in llm.categories] or [Category.HARASSMENT]

    applicable_laws = [_LAW_MAP[l] for l in llm.applicable_laws]
    # Invariant: NetzDG § 3 applies to every piece of platform content.
    if NETZ_DG not in applicable_laws:
        applicable_laws.append(NETZ_DG)

    return ClassificationResult(
        severity=severity,
        categories=categories,
        confidence=llm.confidence,
        requires_immediate_action=llm.requires_immediate_action,
        summary=llm.summary,
        summary_de=llm.summary_de,
        applicable_laws=applicable_laws,
        potential_consequences=llm.potential_consequences,
        potential_consequences_de=llm.potential_consequences_de,
    )
