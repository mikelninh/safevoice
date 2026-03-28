"""
Tests for international law support — Austria (at) and Switzerland (ch).
Verifies law_mapper returns correct country-specific laws for all categories.
"""

import pytest
from app.services.law_mapper import get_laws_for_country, SUPPORTED_COUNTRIES
from app.models.evidence import Category


# === Austrian law tests ===

class TestAustrianLaws:
    """Austrian laws are returned for country='at'."""

    def test_at_harassment_returns_austrian_laws(self):
        laws = get_laws_for_country("at", [Category.HARASSMENT])
        paragraphs = [l.paragraph for l in laws]
        assert any("(AT)" in p for p in paragraphs), "Austrian laws must contain (AT) marker"
        assert "§ 115 StGB (AT)" in paragraphs
        assert "§ 107c StGB (AT)" in paragraphs

    def test_at_threat_returns_107(self):
        laws = get_laws_for_country("at", [Category.THREAT])
        paragraphs = [l.paragraph for l in laws]
        assert "§ 107 StGB (AT)" in paragraphs

    def test_at_death_threat_returns_107(self):
        laws = get_laws_for_country("at", [Category.DEATH_THREAT])
        paragraphs = [l.paragraph for l in laws]
        assert "§ 107 StGB (AT)" in paragraphs

    def test_at_defamation_returns_111(self):
        laws = get_laws_for_country("at", [Category.DEFAMATION])
        paragraphs = [l.paragraph for l in laws]
        assert "§ 111 StGB (AT)" in paragraphs

    def test_at_misogyny_returns_115(self):
        laws = get_laws_for_country("at", [Category.MISOGYNY])
        paragraphs = [l.paragraph for l in laws]
        assert "§ 115 StGB (AT)" in paragraphs

    def test_at_sexual_harassment_returns_coercion_and_cyber(self):
        laws = get_laws_for_country("at", [Category.SEXUAL_HARASSMENT])
        paragraphs = [l.paragraph for l in laws]
        assert "§ 105 StGB (AT)" in paragraphs
        assert "§ 107c StGB (AT)" in paragraphs

    def test_at_laws_have_bilingual_fields(self):
        laws = get_laws_for_country("at", [Category.HARASSMENT])
        for law in laws:
            assert law.title, "title must not be empty"
            assert law.title_de, "title_de must not be empty"
            assert law.description, "description must not be empty"
            assert law.description_de, "description_de must not be empty"
            assert law.applies_because, "applies_because must not be empty"
            assert law.applies_because_de, "applies_because_de must not be empty"

    def test_at_no_netzDG(self):
        """Austria should not include German NetzDG."""
        laws = get_laws_for_country("at", [Category.HARASSMENT, Category.THREAT])
        paragraphs = [l.paragraph for l in laws]
        assert "NetzDG § 3" not in paragraphs


# === Swiss law tests ===

class TestSwissLaws:
    """Swiss laws are returned for country='ch'."""

    def test_ch_harassment_returns_swiss_laws(self):
        laws = get_laws_for_country("ch", [Category.HARASSMENT])
        paragraphs = [l.paragraph for l in laws]
        assert any("(CH)" in p for p in paragraphs), "Swiss laws must contain (CH) marker"
        assert "Art. 177 StGB (CH)" in paragraphs
        assert "Art. 179septies StGB (CH)" in paragraphs

    def test_ch_threat_returns_180(self):
        laws = get_laws_for_country("ch", [Category.THREAT])
        paragraphs = [l.paragraph for l in laws]
        assert "Art. 180 StGB (CH)" in paragraphs

    def test_ch_death_threat_returns_180_and_181(self):
        laws = get_laws_for_country("ch", [Category.DEATH_THREAT])
        paragraphs = [l.paragraph for l in laws]
        assert "Art. 180 StGB (CH)" in paragraphs
        assert "Art. 181 StGB (CH)" in paragraphs

    def test_ch_defamation_returns_173_and_174(self):
        laws = get_laws_for_country("ch", [Category.DEFAMATION])
        paragraphs = [l.paragraph for l in laws]
        assert "Art. 173 StGB (CH)" in paragraphs
        assert "Art. 174 StGB (CH)" in paragraphs

    def test_ch_misogyny_returns_177(self):
        laws = get_laws_for_country("ch", [Category.MISOGYNY])
        paragraphs = [l.paragraph for l in laws]
        assert "Art. 177 StGB (CH)" in paragraphs

    def test_ch_sexual_harassment_returns_coercion_and_telecom(self):
        laws = get_laws_for_country("ch", [Category.SEXUAL_HARASSMENT])
        paragraphs = [l.paragraph for l in laws]
        assert "Art. 181 StGB (CH)" in paragraphs
        assert "Art. 179septies StGB (CH)" in paragraphs

    def test_ch_laws_have_bilingual_fields(self):
        laws = get_laws_for_country("ch", [Category.THREAT])
        for law in laws:
            assert law.title, "title must not be empty"
            assert law.title_de, "title_de must not be empty"
            assert law.description, "description must not be empty"
            assert law.description_de, "description_de must not be empty"
            assert law.applies_because, "applies_because must not be empty"
            assert law.applies_because_de, "applies_because_de must not be empty"

    def test_ch_no_netzDG(self):
        """Switzerland should not include German NetzDG."""
        laws = get_laws_for_country("ch", [Category.HARASSMENT, Category.THREAT])
        paragraphs = [l.paragraph for l in laws]
        assert "NetzDG § 3" not in paragraphs


# === German law tests (backward compatibility) ===

class TestGermanLawsStillWork:
    """German laws must continue to work for country='de'."""

    def test_de_harassment_returns_185(self):
        laws = get_laws_for_country("de", [Category.HARASSMENT])
        paragraphs = [l.paragraph for l in laws]
        assert "§ 185 StGB" in paragraphs

    def test_de_threat_returns_241(self):
        laws = get_laws_for_country("de", [Category.THREAT])
        paragraphs = [l.paragraph for l in laws]
        assert "§ 241 StGB" in paragraphs

    def test_de_death_threat_returns_126a_and_241(self):
        laws = get_laws_for_country("de", [Category.DEATH_THREAT])
        paragraphs = [l.paragraph for l in laws]
        assert "§ 126a StGB" in paragraphs
        assert "§ 241 StGB" in paragraphs

    def test_de_includes_netzDG(self):
        laws = get_laws_for_country("de", [Category.HARASSMENT])
        paragraphs = [l.paragraph for l in laws]
        assert "NetzDG § 3" in paragraphs

    def test_de_scam_returns_fraud_laws(self):
        laws = get_laws_for_country("de", [Category.SCAM])
        paragraphs = [l.paragraph for l in laws]
        assert "§ 263 StGB" in paragraphs
        assert "§ 263a StGB" in paragraphs


# === Cross-country comparison tests ===

class TestCrossCountryMapping:
    """Verify that the same category maps to different country-specific paragraphs."""

    def test_threat_maps_to_different_paragraphs_per_country(self):
        de_laws = get_laws_for_country("de", [Category.THREAT])
        at_laws = get_laws_for_country("at", [Category.THREAT])
        ch_laws = get_laws_for_country("ch", [Category.THREAT])

        de_p = {l.paragraph for l in de_laws}
        at_p = {l.paragraph for l in at_laws}
        ch_p = {l.paragraph for l in ch_laws}

        # Each country should return its own laws, not another country's
        assert "§ 241 StGB" in de_p
        assert "§ 107 StGB (AT)" in at_p
        assert "Art. 180 StGB (CH)" in ch_p

        # No cross-contamination
        assert not at_p.intersection(de_p - {"NetzDG § 3"})
        assert not ch_p.intersection(de_p - {"NetzDG § 3"})

    def test_multiple_categories_collect_all_laws(self):
        laws = get_laws_for_country("at", [Category.HARASSMENT, Category.THREAT, Category.DEFAMATION])
        paragraphs = [l.paragraph for l in laws]
        assert "§ 115 StGB (AT)" in paragraphs  # harassment / insult
        assert "§ 107 StGB (AT)" in paragraphs  # threat
        assert "§ 111 StGB (AT)" in paragraphs  # defamation

    def test_deduplication(self):
        """Passing the same category twice should not produce duplicate laws."""
        laws = get_laws_for_country("ch", [Category.THREAT, Category.THREAT])
        paragraphs = [l.paragraph for l in laws]
        assert paragraphs == list(dict.fromkeys(paragraphs)), "Laws should be deduplicated"

    def test_unsupported_country_raises(self):
        with pytest.raises(ValueError, match="Unsupported country"):
            get_laws_for_country("xx", [Category.HARASSMENT])

    def test_empty_categories_returns_platform_laws_only(self):
        de_laws = get_laws_for_country("de", [])
        at_laws = get_laws_for_country("at", [])
        ch_laws = get_laws_for_country("ch", [])

        # DE gets NetzDG even with no categories
        assert len(de_laws) == 1
        assert de_laws[0].paragraph == "NetzDG § 3"

        # AT and CH get nothing with no categories
        assert len(at_laws) == 0
        assert len(ch_laws) == 0

    def test_all_supported_countries_recognized(self):
        assert "de" in SUPPORTED_COUNTRIES
        assert "at" in SUPPORTED_COUNTRIES
        assert "ch" in SUPPORTED_COUNTRIES

    def test_max_penalty_is_realistic(self):
        """All laws should have non-empty max_penalty values."""
        for country in SUPPORTED_COUNTRIES:
            laws = get_laws_for_country(
                country,
                [Category.HARASSMENT, Category.THREAT, Category.DEATH_THREAT, Category.DEFAMATION],
            )
            for law in laws:
                assert law.max_penalty, f"max_penalty empty for {law.paragraph}"
                assert len(law.max_penalty) > 5, f"max_penalty too short for {law.paragraph}"
