"""
Tests for UK and French law definitions.
Validates that every law object is a valid GermanLaw instance with all
required fields populated.
"""

import pytest
from app.models.evidence import GermanLaw
from app.data.laws_uk import (
    ALL_UK_LAWS,
    UK_ONLINE_SAFETY_ACT,
    UK_COMMUNICATIONS_ACT_S127,
    UK_MALICIOUS_COMMS_S1,
    UK_HARASSMENT_S2,
    UK_HARASSMENT_S4,
    UK_FRAUD_ACT_S2,
    UK_COMPUTER_MISUSE_S1,
)
from app.data.laws_france import (
    ALL_FR_LAWS,
    FR_LOI_AVIA,
    FR_HARCELEMENT_MORAL,
    FR_MENACES_DE_MORT,
    FR_VIE_PRIVEE,
    FR_DIFFAMATION,
    FR_ESCROQUERIE,
)


# ---------------------------------------------------------------------------
# UK LAW TESTS
# ---------------------------------------------------------------------------


class TestUKLawsRequiredFields:
    """Verify every UK law has all required GermanLaw fields populated."""

    @pytest.mark.parametrize("law", ALL_UK_LAWS, ids=lambda l: l.paragraph)
    def test_uk_law_is_german_law_instance(self, law):
        assert isinstance(law, GermanLaw)

    @pytest.mark.parametrize("law", ALL_UK_LAWS, ids=lambda l: l.paragraph)
    def test_uk_law_has_nonempty_title(self, law):
        assert law.title and len(law.title.strip()) > 0

    @pytest.mark.parametrize("law", ALL_UK_LAWS, ids=lambda l: l.paragraph)
    def test_uk_law_has_nonempty_title_de(self, law):
        assert law.title_de and len(law.title_de.strip()) > 0

    @pytest.mark.parametrize("law", ALL_UK_LAWS, ids=lambda l: l.paragraph)
    def test_uk_law_has_nonempty_description(self, law):
        assert law.description and len(law.description.strip()) > 0

    @pytest.mark.parametrize("law", ALL_UK_LAWS, ids=lambda l: l.paragraph)
    def test_uk_law_has_nonempty_description_de(self, law):
        assert law.description_de and len(law.description_de.strip()) > 0

    @pytest.mark.parametrize("law", ALL_UK_LAWS, ids=lambda l: l.paragraph)
    def test_uk_law_has_nonempty_max_penalty(self, law):
        assert law.max_penalty and len(law.max_penalty.strip()) > 0

    @pytest.mark.parametrize("law", ALL_UK_LAWS, ids=lambda l: l.paragraph)
    def test_uk_law_has_nonempty_applies_because(self, law):
        assert law.applies_because and len(law.applies_because.strip()) > 0

    @pytest.mark.parametrize("law", ALL_UK_LAWS, ids=lambda l: l.paragraph)
    def test_uk_law_has_nonempty_applies_because_de(self, law):
        assert law.applies_because_de and len(law.applies_because_de.strip()) > 0

    @pytest.mark.parametrize("law", ALL_UK_LAWS, ids=lambda l: l.paragraph)
    def test_uk_law_has_nonempty_paragraph(self, law):
        assert law.paragraph and len(law.paragraph.strip()) > 0


class TestUKLawsCount:
    """Verify the expected number of UK laws are defined."""

    def test_uk_laws_count(self):
        assert len(ALL_UK_LAWS) == 7

    def test_uk_all_laws_list_contains_all_exports(self):
        expected = [
            UK_ONLINE_SAFETY_ACT,
            UK_COMMUNICATIONS_ACT_S127,
            UK_MALICIOUS_COMMS_S1,
            UK_HARASSMENT_S2,
            UK_HARASSMENT_S4,
            UK_FRAUD_ACT_S2,
            UK_COMPUTER_MISUSE_S1,
        ]
        for law in expected:
            assert law in ALL_UK_LAWS, f"{law.paragraph} missing from ALL_UK_LAWS"
        assert len(ALL_UK_LAWS) == len(expected)


# ---------------------------------------------------------------------------
# FRENCH LAW TESTS
# ---------------------------------------------------------------------------


class TestFRLawsRequiredFields:
    """Verify every French law has all required GermanLaw fields populated."""

    @pytest.mark.parametrize("law", ALL_FR_LAWS, ids=lambda l: l.paragraph)
    def test_fr_law_is_german_law_instance(self, law):
        assert isinstance(law, GermanLaw)

    @pytest.mark.parametrize("law", ALL_FR_LAWS, ids=lambda l: l.paragraph)
    def test_fr_law_has_nonempty_title(self, law):
        assert law.title and len(law.title.strip()) > 0

    @pytest.mark.parametrize("law", ALL_FR_LAWS, ids=lambda l: l.paragraph)
    def test_fr_law_has_nonempty_title_de(self, law):
        assert law.title_de and len(law.title_de.strip()) > 0

    @pytest.mark.parametrize("law", ALL_FR_LAWS, ids=lambda l: l.paragraph)
    def test_fr_law_has_nonempty_description(self, law):
        assert law.description and len(law.description.strip()) > 0

    @pytest.mark.parametrize("law", ALL_FR_LAWS, ids=lambda l: l.paragraph)
    def test_fr_law_has_nonempty_description_de(self, law):
        assert law.description_de and len(law.description_de.strip()) > 0

    @pytest.mark.parametrize("law", ALL_FR_LAWS, ids=lambda l: l.paragraph)
    def test_fr_law_has_nonempty_max_penalty(self, law):
        assert law.max_penalty and len(law.max_penalty.strip()) > 0

    @pytest.mark.parametrize("law", ALL_FR_LAWS, ids=lambda l: l.paragraph)
    def test_fr_law_has_nonempty_applies_because(self, law):
        assert law.applies_because and len(law.applies_because.strip()) > 0

    @pytest.mark.parametrize("law", ALL_FR_LAWS, ids=lambda l: l.paragraph)
    def test_fr_law_has_nonempty_applies_because_de(self, law):
        assert law.applies_because_de and len(law.applies_because_de.strip()) > 0

    @pytest.mark.parametrize("law", ALL_FR_LAWS, ids=lambda l: l.paragraph)
    def test_fr_law_has_nonempty_paragraph(self, law):
        assert law.paragraph and len(law.paragraph.strip()) > 0


class TestFRLawsCount:
    """Verify the expected number of French laws are defined."""

    def test_fr_laws_count(self):
        assert len(ALL_FR_LAWS) == 6

    def test_fr_all_laws_list_contains_all_exports(self):
        expected = [
            FR_LOI_AVIA,
            FR_HARCELEMENT_MORAL,
            FR_MENACES_DE_MORT,
            FR_VIE_PRIVEE,
            FR_DIFFAMATION,
            FR_ESCROQUERIE,
        ]
        for law in expected:
            assert law in ALL_FR_LAWS, f"{law.paragraph} missing from ALL_FR_LAWS"
        assert len(ALL_FR_LAWS) == len(expected)


# ---------------------------------------------------------------------------
# CROSS-JURISDICTION TESTS
# ---------------------------------------------------------------------------


class TestCrossJurisdiction:
    """Tests across both UK and French law sets."""

    def test_all_laws_have_unique_paragraphs(self):
        all_paragraphs = [law.paragraph for law in ALL_UK_LAWS + ALL_FR_LAWS]
        assert len(all_paragraphs) == len(set(all_paragraphs)), (
            "Duplicate paragraph identifiers found across UK and FR laws"
        )

    def test_no_law_has_placeholder_text(self):
        for law in ALL_UK_LAWS + ALL_FR_LAWS:
            for field in ["title", "title_de", "description", "description_de",
                          "max_penalty", "applies_because", "applies_because_de"]:
                value = getattr(law, field)
                assert "TODO" not in value, f"{law.paragraph}.{field} contains TODO"
                assert "PLACEHOLDER" not in value, f"{law.paragraph}.{field} contains PLACEHOLDER"
