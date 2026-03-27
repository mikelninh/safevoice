"""
Transformer-based classifier using HuggingFace models.
Fallback when Claude API is unavailable. Works fully offline.
Uses multilingual toxicity/hate speech models.
"""

import logging
from app.models.evidence import (
    ClassificationResult, Severity, Category, GermanLaw
)
from app.data.mock_data import LAW_185, LAW_186, LAW_241, NETZ_DG

logger = logging.getLogger(__name__)

_pipeline = None
_available = None


def is_available() -> bool:
    """Check if transformer dependencies are installed."""
    global _available
    if _available is not None:
        return _available
    try:
        import transformers  # noqa: F401
        import torch  # noqa: F401
        _available = True
    except ImportError:
        _available = False
        logger.info("transformers/torch not installed, transformer classifier unavailable")
    return _available


def _get_pipeline():
    """Lazy-load the classification pipeline (first call downloads the model)."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    from transformers import pipeline

    # Use a multilingual toxicity model — good for DE + EN
    _pipeline = pipeline(
        "text-classification",
        model="martin-ha/toxic-comment-model",
        top_k=None,
        truncation=True,
        max_length=512,
    )
    return _pipeline


def classify_with_transformer(text: str) -> ClassificationResult | None:
    """
    Classify text using transformer model.
    Returns None if unavailable or fails.
    """
    if not is_available():
        return None

    try:
        pipe = _get_pipeline()
        results = pipe(text[:512])

        # results is a list of label/score dicts
        scores = {r["label"]: r["score"] for r in results[0]}
        toxic_score = scores.get("toxic", 0.0)
        non_toxic_score = scores.get("non-toxic", 1.0)

        return _interpret_scores(text, toxic_score, non_toxic_score)

    except Exception as e:
        logger.warning(f"Transformer classifier failed: {e}")
        return None


def _interpret_scores(
    text: str, toxic_score: float, non_toxic_score: float
) -> ClassificationResult:
    """
    Map toxicity scores to SafeVoice categories.
    The transformer gives us a toxicity signal; we combine with
    simple heuristics for category assignment.
    """
    text_lower = text.lower()

    # Determine severity from toxicity score
    if toxic_score >= 0.9:
        severity = Severity.CRITICAL
    elif toxic_score >= 0.7:
        severity = Severity.HIGH
    elif toxic_score >= 0.4:
        severity = Severity.MEDIUM
    else:
        severity = Severity.LOW

    # Category detection (enhanced by transformer confidence)
    categories: list[Category] = []
    applicable_laws: list[GermanLaw] = []

    # Threat keywords (transformer confirms the content is harmful)
    threat_words = [
        "kill", "murder", "die", "umbringen", "töten", "ermorden",
        "kys", "go die", "watch yourself", "pass auf",
    ]
    if toxic_score > 0.5 and any(w in text_lower for w in threat_words):
        categories.append(Category.THREAT)
        applicable_laws.append(LAW_241)
        if any(w in text_lower for w in ["kill", "murder", "umbringen", "töten", "ermorden"]):
            categories.append(Category.DEATH_THREAT)
            severity = Severity.CRITICAL

    # Misogyny
    misogyny_words = [
        "women should", "frauen gehören", "schlampe", "hure",
        "bitch", "whore", "slut", "cunt", "weiber",
        "frauen wie du", "stay in the kitchen",
    ]
    if toxic_score > 0.4 and any(w in text_lower for w in misogyny_words):
        categories.append(Category.MISOGYNY)

    # Scam signals
    scam_words = [
        "guaranteed return", "garantierte rendite", "send bitcoin",
        "wallet address", "verification fee", "verifizierungsgebühr",
        "monthly return", "monatliche rendite", "invest now",
    ]
    if any(w in text_lower for w in scam_words):
        categories.append(Category.SCAM)
        from app.data.mock_data import LAW_263
        applicable_laws.append(LAW_263)
        severity = Severity.CRITICAL

    # General harassment (if toxic but no specific category)
    if toxic_score > 0.4 and not categories:
        categories.append(Category.HARASSMENT)

    if not categories:
        categories.append(Category.HARASSMENT)

    if LAW_185 not in applicable_laws:
        applicable_laws.append(LAW_185)
    applicable_laws.append(NETZ_DG)

    # Remove duplicates
    seen = set()
    applicable_laws = [l for l in applicable_laws if not (l.paragraph in seen or seen.add(l.paragraph))]

    requires_immediate = severity in (Severity.CRITICAL, Severity.HIGH) and (
        Category.THREAT in categories or Category.DEATH_THREAT in categories or Category.SCAM in categories
    )

    confidence = round(toxic_score * 0.85 + 0.1, 2)  # Scale to reasonable range
    confidence = min(confidence, 0.95)  # Cap — transformer alone shouldn't claim 99%

    summary_en = f"Content classified as toxic (score: {toxic_score:.0%}). Categories: {', '.join(c.value for c in categories)}."
    summary_de = f"Inhalt als toxisch eingestuft (Score: {toxic_score:.0%}). Kategorien: {', '.join(c.value for c in categories)}."

    return ClassificationResult(
        severity=severity,
        categories=list(set(categories)),
        confidence=confidence,
        requires_immediate_action=requires_immediate,
        summary=summary_en,
        summary_de=summary_de,
        applicable_laws=applicable_laws,
        potential_consequences=_consequences_en(severity, applicable_laws),
        potential_consequences_de=_consequences_de(severity, applicable_laws),
    )


def _consequences_en(severity: Severity, laws: list[GermanLaw]) -> str:
    refs = ", ".join(l.paragraph for l in laws if l.paragraph != "NetzDG § 3")
    if severity == Severity.CRITICAL:
        return f"URGENT: Likely criminal offense under {refs}. File a police report immediately."
    if severity == Severity.HIGH:
        return f"Likely violates {refs}. NetzDG report strongly recommended."
    return f"May violate {refs}. Document and preserve evidence."


def _consequences_de(severity: Severity, laws: list[GermanLaw]) -> str:
    refs = ", ".join(l.paragraph for l in laws if l.paragraph != "NetzDG § 3")
    if severity == Severity.CRITICAL:
        return f"DRINGEND: Wahrscheinliche Straftat nach {refs}. Sofortige Strafanzeige erstatten."
    if severity == Severity.HIGH:
        return f"Verstößt wahrscheinlich gegen {refs}. NetzDG-Meldung dringend empfohlen."
    return f"Kann gegen {refs} verstoßen. Beweise dokumentieren und sichern."
