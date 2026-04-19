"""
Classification service — single-tier LLM classifier.

Previous versions had a 3-tier fallback (LLM → transformer → regex).
We removed tiers 2 and 3 because:
  - Transformer (xlm-roberta) under-classifies German legal specifics
  - Regex can't handle obfuscation beyond its dictionary
  - A weak fallback classification is worse than an honest error:
    it gives victims (and courts) a false sense of certainty.

If the LLM is unavailable, we raise ClassifierUnavailableError.
The API layer catches this and returns 503 with a clear message.
"""

from __future__ import annotations

import logging

from app.models.evidence import ClassificationResult
from app.services.classifier_llm_v2 import classify_with_llm, is_available as llm_available

logger = logging.getLogger(__name__)


class ClassifierUnavailableError(RuntimeError):
    """Raised when the LLM classifier cannot be reached.

    The orchestrator used to fall back to tier 2 (transformer) or tier 3 (regex)
    in this case. We now surface the error honestly: a stale or weak classification
    is more harmful than a clear "try again later" message.
    """


def classify(
    text: str,
    *,
    victim_context: str | None = None,
    jurisdiction: str = "DE",
    user_lang: str = "de",
) -> ClassificationResult:
    """
    Classify text using the LLM classifier.

    Optional keyword args are threaded through to `classify_with_llm`, which
    injects them into the user-role prompt via `build_user_message`. Omitting
    them preserves the legacy prompt exactly.

    Args:
        text: the content to classify.
        victim_context: optional free-text victim-provided context
            (e.g. "ex-partner after breakup") — steers severity/§ mapping.
        jurisdiction: ISO country code of applicable law. Defaults to "DE".
        user_lang: preferred output language. Defaults to "de".

    Raises:
        ClassifierUnavailableError: if no API key is set, or the LLM call fails.

    The single-tier design means every classification is high-quality and auditable.
    `classifier_tier` is always 1 — kept in the schema for future multi-model support.
    """
    if not llm_available():
        raise ClassifierUnavailableError(
            "LLM classifier unavailable — OPENAI_API_KEY not configured."
        )

    result = classify_with_llm(
        text,
        victim_context=victim_context,
        jurisdiction=jurisdiction,
        user_lang=user_lang,
    )
    if result is None:
        raise ClassifierUnavailableError(
            "LLM classification failed. Please try again in a moment."
        )

    logger.info("Classified with LLM (tier 1)")
    return result


def is_configured() -> bool:
    """Whether the classifier is ready to run. Used by health checks."""
    return llm_available()


# ── Backward-compat re-export (DEPRECATED) ────────────────────────────
# Existing tests import `classify_regex` from this module. Keep the re-export
# so they continue to pass, but do NOT use it in new production code.
from app.services.classifier_regex import classify_regex  # noqa: E402,F401
