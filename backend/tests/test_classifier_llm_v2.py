"""
Tests for classifier_llm_v2 — structured outputs via Pydantic.

These tests don't hit the real OpenAI API. They verify:
1. Schema classes (LLMClassification) validate inputs correctly
2. Domain mapping (_to_domain) produces correct ClassificationResult
3. NetzDG § 3 invariant always applies
4. Refusal handling returns None
"""

import pytest
from unittest.mock import patch, MagicMock

from app.models.evidence import Severity, Category
from app.services.classifier_llm_v2 import (
    LLMClassification, LLMSeverity, LLMCategory, LLMLaw,
    _to_domain, classify_with_llm, is_available,
)
from app.data.mock_data import NETZ_DG, LAW_241


class TestLLMClassificationSchema:
    """Pydantic schema validation."""

    def test_valid_minimal_input(self):
        cls = LLMClassification(
            severity=LLMSeverity.medium,
            categories=[LLMCategory.harassment],
            confidence=0.8,
            requires_immediate_action=False,
            summary="x",
            summary_de="x",
            applicable_laws=[LLMLaw.netzdg_3],
            potential_consequences="x",
            potential_consequences_de="x",
        )
        assert cls.severity == LLMSeverity.medium

    def test_empty_categories_rejected(self):
        """At least one category required — Pydantic enforces min_length=1."""
        with pytest.raises(Exception):
            LLMClassification(
                severity=LLMSeverity.low,
                categories=[],
                confidence=0.5,
                requires_immediate_action=False,
                summary="x", summary_de="x",
                applicable_laws=[],
                potential_consequences="x", potential_consequences_de="x",
            )

    def test_confidence_out_of_range_rejected(self):
        with pytest.raises(Exception):
            LLMClassification(
                severity=LLMSeverity.low,
                categories=[LLMCategory.harassment],
                confidence=1.5,  # > 1.0
                requires_immediate_action=False,
                summary="x", summary_de="x",
                applicable_laws=[LLMLaw.netzdg_3],
                potential_consequences="x", potential_consequences_de="x",
            )

    def test_unknown_category_rejected(self):
        """Strings outside the enum are rejected at construction."""
        with pytest.raises(Exception):
            LLMClassification.model_validate({
                "severity": "low",
                "categories": ["made_up_category"],
                "confidence": 0.5,
                "requires_immediate_action": False,
                "summary": "x", "summary_de": "x",
                "applicable_laws": ["NetzDG § 3"],
                "potential_consequences": "x", "potential_consequences_de": "x",
            })


class TestDomainMapping:
    """_to_domain converts LLM output to internal domain types."""

    def _minimal(self, **overrides):
        base = dict(
            severity=LLMSeverity.medium,
            categories=[LLMCategory.harassment],
            confidence=0.8,
            requires_immediate_action=False,
            summary="Classification", summary_de="Klassifikation",
            applicable_laws=[LLMLaw.stgb_241],
            potential_consequences="...", potential_consequences_de="...",
        )
        base.update(overrides)
        return LLMClassification(**base)

    def test_severity_maps(self):
        result = _to_domain(self._minimal(severity=LLMSeverity.high))
        assert result.severity == Severity.HIGH

    def test_categories_map(self):
        result = _to_domain(self._minimal(
            categories=[LLMCategory.death_threat, LLMCategory.harassment],
        ))
        assert Category.DEATH_THREAT in result.categories
        assert Category.HARASSMENT in result.categories

    def test_netzdg_always_appended(self):
        """NetzDG § 3 invariant: always in applicable_laws for platform content."""
        result = _to_domain(self._minimal(applicable_laws=[LLMLaw.stgb_241]))
        assert NETZ_DG in result.applicable_laws
        assert LAW_241 in result.applicable_laws

    def test_netzdg_not_duplicated_when_already_present(self):
        result = _to_domain(self._minimal(
            applicable_laws=[LLMLaw.stgb_241, LLMLaw.netzdg_3],
        ))
        netzdg_count = sum(1 for l in result.applicable_laws if l == NETZ_DG)
        assert netzdg_count == 1

    def test_confidence_preserved(self):
        result = _to_domain(self._minimal(confidence=0.42))
        assert result.confidence == 0.42


class TestClassifyWithLLM:
    """Full flow with mocked OpenAI client."""

    def test_no_api_key_returns_none(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        assert classify_with_llm("test") is None

    def test_is_available_requires_both_sdk_and_key(self, monkeypatch):
        # Assuming SDK is installed in the test env
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        assert is_available() is False
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        assert is_available() is True

    @patch("app.services.classifier_llm_v2.OpenAI")
    def test_refusal_returns_none(self, mock_openai_cls, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        completion = MagicMock()
        completion.choices = [MagicMock()]
        completion.choices[0].message.refusal = "Cannot classify."
        completion.choices[0].message.parsed = None
        mock_client.chat.completions.parse.return_value = completion

        assert classify_with_llm("some text") is None

    @patch("app.services.classifier_llm_v2.OpenAI")
    def test_successful_classification(self, mock_openai_cls, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        parsed = LLMClassification(
            severity=LLMSeverity.high,
            categories=[LLMCategory.threat],
            confidence=0.9,
            requires_immediate_action=True,
            summary="Threat", summary_de="Bedrohung",
            applicable_laws=[LLMLaw.stgb_241],
            potential_consequences="x", potential_consequences_de="x",
        )
        completion = MagicMock()
        completion.choices = [MagicMock()]
        completion.choices[0].message.refusal = None
        completion.choices[0].message.parsed = parsed
        mock_client.chat.completions.parse.return_value = completion

        result = classify_with_llm("Du wirst sterben")
        assert result is not None
        assert result.severity == Severity.HIGH
        assert Category.THREAT in result.categories
        assert NETZ_DG in result.applicable_laws

    @patch("app.services.classifier_llm_v2.OpenAI")
    def test_api_exception_returns_none(self, mock_openai_cls, monkeypatch):
        """Broad exception handling: a failed API call falls through to tier 2/3."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.parse.side_effect = Exception("Network error")

        assert classify_with_llm("test") is None
