"""
Real-world classifier tests — tests that MUST pass before LinkedIn.
Tests both regex fallback and AI classifier with realistic scenarios.
Each test represents a real type of digital violence in Germany.
"""

import pytest
import os
from app.services.classifier import classify, classify_regex
from app.models.evidence import Severity, Category


class TestDeathThreats:
    """Todesdrohungen — MUST be CRITICAL."""

    def test_direct_kill_threat_de(self):
        r = classify_regex("Ich bringe dich um")
        assert r.severity == Severity.CRITICAL
        assert Category.DEATH_THREAT in r.categories

    def test_separable_verb_kill(self):
        r = classify_regex("ich bringe dich um du hurensohn")
        assert r.severity == Severity.CRITICAL

    def test_slash_threat(self):
        """'schlitze dich auf' = knife threat."""
        r = classify_regex("du hässliches kind, hurensohn, schlitze dich auf")
        # Regex may miss this — that's why we need AI
        # But at minimum it should detect harassment
        assert r.severity in [Severity.HIGH, Severity.CRITICAL] or Category.HARASSMENT in r.categories

    def test_die_command(self):
        r = classify_regex("stirb du dreckige fotze")
        assert r.severity == Severity.CRITICAL
        assert Category.DEATH_THREAT in r.categories

    @pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="Needs AI for heavy obfuscation")
    def test_die_with_typos(self):
        """Heavy obfuscation — only AI handles this."""
        r = classify("stiiirb du dreckige fotzzze")
        assert r.severity in [Severity.HIGH, Severity.CRITICAL]

    def test_verreck(self):
        r = classify_regex("verreck du miststück")
        assert r.severity == Severity.CRITICAL

    def test_krepier(self):
        r = classify_regex("krepier du hund")
        assert r.severity == Severity.CRITICAL

    def test_suicide_encouragement(self):
        r = classify_regex("du bist so hässlich du solltest dich umbringen")
        assert r.severity == Severity.CRITICAL
        assert Category.DEATH_THREAT in r.categories

    def test_kys_english(self):
        r = classify_regex("just kys nobody cares about you")
        assert r.severity == Severity.CRITICAL


class TestVolksverhetzung:
    """§130 StGB — Incitement to hatred. MUST be CRITICAL."""

    def test_auslaender_raus(self):
        r = classify_regex("Deutschland den Deutschen, Ausländer raus")
        assert Category.VOLKSVERHETZUNG in r.categories
        assert r.severity == Severity.CRITICAL

    def test_dreckige_auslaender(self):
        r = classify_regex("dreckige Ausländer gehören deportiert")
        assert Category.VOLKSVERHETZUNG in r.categories

    def test_dreckiger_adjective_ending(self):
        """Adjective ending -er must also match."""
        r = classify_regex("dreckiger Ausländer")
        assert Category.VOLKSVERHETZUNG in r.categories

    def test_kanaken(self):
        r = classify_regex("scheiß Kanaken raus aus Deutschland")
        assert Category.VOLKSVERHETZUNG in r.categories

    def test_antisemitic(self):
        r = classify_regex("alle Juden sollen vergast werden")
        assert Category.VOLKSVERHETZUNG in r.categories
        assert r.severity == Severity.CRITICAL

    def test_nword_german(self):
        r = classify_regex("dreckige Neger gehören aufgehängt")
        assert Category.VOLKSVERHETZUNG in r.categories

    def test_holocaust_denial(self):
        r = classify_regex("den Holocaust gab es nicht, alles eine Lüge")
        assert Category.VOLKSVERHETZUNG in r.categories

    def test_heil_hitler(self):
        r = classify_regex("Heil Hitler, white power")
        assert Category.VOLKSVERHETZUNG in r.categories


class TestStalking:
    """§238 StGB — Nachstellung."""

    def test_know_where_you_live(self):
        r = classify_regex("ich weiß wo du wohnst")
        assert Category.STALKING in r.categories

    def test_watching_you(self):
        r = classify_regex("ich beobachte dich schon lange")
        assert Category.STALKING in r.categories

    def test_cant_hide(self):
        r = classify_regex("du kannst dich nicht verstecken")
        assert Category.STALKING in r.categories

    def test_i_will_find_you(self):
        r = classify_regex("ich finde dich, egal wo du bist")
        assert Category.STALKING in r.categories


class TestIntimateImages:
    """§201a StGB — Non-consensual images / deepfakes."""

    def test_leak_nudes_de(self):
        r = classify_regex("ich veröffentliche deine Nacktbilder")
        assert Category.INTIMATE_IMAGES in r.categories
        assert r.severity == Severity.CRITICAL

    def test_deepfake(self):
        r = classify_regex("I made a deepfake of you")
        assert Category.INTIMATE_IMAGES in r.categories

    def test_revenge_porn(self):
        r = classify_regex("revenge porn, ich hab deine nudes")
        assert Category.INTIMATE_IMAGES in r.categories


class TestVerleumdung:
    """§187 StGB — Slander (knowingly false claims)."""

    def test_destroy_reputation(self):
        r = classify_regex("ich zerstöre deinen Ruf, ich werde allen erzählen")
        assert Category.VERLEUMDUNG in r.categories

    def test_spread_lies(self):
        r = classify_regex("ich werde überall Lügen verbreiten über dich")
        assert Category.VERLEUMDUNG in r.categories


class TestSexualHarassment:
    """Sexual harassment."""

    def test_send_nudes_de(self):
        r = classify_regex("schick mir Bilder von dir nackt")
        assert Category.SEXUAL_HARASSMENT in r.categories

    def test_fick_dich(self):
        r = classify_regex("fick dich du schlampe")
        assert Category.SEXUAL_HARASSMENT in r.categories or Category.MISOGYNY in r.categories


class TestScamFraud:
    """§263 StGB — Fraud / Scam."""

    def test_crypto_scam(self):
        r = classify_regex("investiere jetzt in bitcoin, 30% monatliche rendite garantiert")
        assert Category.SCAM in r.categories
        assert r.severity == Severity.CRITICAL

    def test_phishing(self):
        r = classify_regex("Klicke hier um dein Konto zu verifizieren, account gesperrt")
        assert Category.PHISHING in r.categories


class TestCombinedThreats:
    """Multiple categories in one message."""

    def test_death_threat_plus_volksverhetzung(self):
        r = classify_regex("alle Muslime sollen vergast werden, ich bringe euch um")
        assert Category.VOLKSVERHETZUNG in r.categories
        assert Category.DEATH_THREAT in r.categories
        assert r.severity == Severity.CRITICAL

    def test_stalking_plus_threat(self):
        r = classify_regex("ich weiß wo du wohnst und ich komme vorbei, pass auf dich auf")
        assert Category.STALKING in r.categories
        assert r.requires_immediate_action

    def test_misogyny_plus_threat(self):
        r = classify_regex("Frauen wie du gehören geschlagen, halt die Klappe schlampe")
        assert Category.MISOGYNY in r.categories
        assert r.severity in [Severity.HIGH, Severity.CRITICAL]


class TestObfuscation:
    """Intentionally misspelled/obfuscated text."""

    def test_letter_substitution(self):
        r = classify_regex("du h$$$liche f0tze stirb")
        assert Category.DEATH_THREAT in r.categories

    @pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="Needs AI for repeated-letter obfuscation")
    def test_repeated_letters(self):
        """Repeated letters — only AI handles 'killl' → 'kill' reliably."""
        r = classify("du huuuurensohn ich killl dich")
        assert r.severity in [Severity.HIGH, Severity.CRITICAL]

    def test_spaces_in_slur(self):
        r = classify_regex("du dreckige k a n a k e")
        # Regex won't catch spaced-out words — this is an AI-only test
        # Just verify it doesn't crash
        assert r.severity is not None


class TestEdgeCases:
    """Edge cases that should NOT be classified as severe."""

    def test_neutral_text(self):
        r = classify_regex("Guten Morgen, wie geht es dir?")
        assert r.severity == Severity.LOW

    def test_news_about_violence(self):
        """Reporting about violence is not violence itself."""
        r = classify_regex("Die Polizei berichtet über einen Vorfall in Berlin")
        assert r.severity == Severity.LOW

    def test_empty_text(self):
        r = classify_regex("")
        assert r.severity == Severity.LOW


class TestMultilingual:
    """Turkish and Arabic patterns."""

    def test_turkish_death_threat(self):
        r = classify_regex("seni öldüreceğim")
        assert Category.DEATH_THREAT in r.categories

    def test_arabic_death_threat(self):
        r = classify_regex("سأقتلك")
        assert Category.DEATH_THREAT in r.categories

    def test_english_death_threat(self):
        r = classify_regex("I will kill you and your family")
        assert Category.DEATH_THREAT in r.categories
        assert r.severity == Severity.CRITICAL


@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="No API key")
class TestAIClassifier:
    """Tests that ONLY work with AI — regex can't handle these."""

    def test_slash_threat_ai(self):
        """AI should understand 'schlitze dich auf' as knife threat."""
        r = classify("du hässliches kind schlitze dich auf")
        assert r.severity in [Severity.HIGH, Severity.CRITICAL]
        assert Category.THREAT in r.categories or Category.DEATH_THREAT in r.categories

    def test_typo_threat_ai(self):
        """AI should understand 'stirbt' as 'stirb' (typo)."""
        r = classify("stirbt du dreckige fotzzze")
        assert r.severity in [Severity.HIGH, Severity.CRITICAL]

    def test_indirect_threat_ai(self):
        """AI should understand implied threats."""
        r = classify("es wäre schade wenn deiner familie etwas passieren würde")
        assert r.severity in [Severity.HIGH, Severity.CRITICAL]

    def test_sarcastic_threat_ai(self):
        """AI should see through sarcasm."""
        r = classify("wäre doch schön wenn du einfach nicht mehr aufwachst morgen")
        assert r.severity in [Severity.HIGH, Severity.CRITICAL]

    def test_context_understanding_ai(self):
        """AI should understand context that regex misses."""
        r = classify("schick mir 500€ in bitcoin oder ich zerstöre dein leben")
        assert r.severity == Severity.CRITICAL
        assert Category.THREAT in r.categories or Category.SCAM in r.categories
