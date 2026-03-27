"""
Classification service.
MVP: rule-based classifier with keyword signals.
Production: replace with fine-tuned transformer model + LLM legal analysis.
"""

import re
from app.models.evidence import (
    ClassificationResult, Severity, Category, GermanLaw
)
from app.data.mock_data import LAW_185, LAW_186, LAW_241, LAW_126A, NETZ_DG, LAW_263, LAW_263A, LAW_269


# Signal dictionaries - extend these significantly in production
DEATH_THREAT_SIGNALS = [
    r"\b(kill|murder|slaughter|hunt|eliminate)\s+(you|u|her|them|yourself)\b",
    r"\bkill\s+your\s*self\b",
    r"\b(kys|go\s+die|go\s+kill\s+yourself)\b",
    r"\b(you|u|she)\s+(will|won't)\s+(die|survive|live)\b",
    r"\btod\b.*\b(dir|ihr|dich)\b",
    r"\b(umbringen|töten|ermorden)\b",
    r"\bwatch\s+(your|yourself)\b",
    r"\bI\s+know\s+where\s+you\b",
    r"\bich\s+weiß\s+wo\s+du\b",
    r"\bpas\s+auf\s+dich\s+auf\b",
]

THREAT_SIGNALS = [
    r"\b(you'll|you will|you're going to)\s+(regret|pay|suffer)\b",
    r"\bsomething\s+(will|might|could)\s+happen\b",
    r"\b(watch|careful|beware)\b",
    r"\bdrohe\b",
    r"\bpassiert\s+(dir|ihr)\s+(was|etwas)\b",
]

MISOGYNY_SIGNALS = [
    r"\b(women|woman|female|girl)\s+(should|must|need to)\s+(shut up|be quiet|stay home|stay in the kitchen)\b",
    r"\bfrauen\s+(gehören|sollen|müssen|haben\s+kein(e)?|sind)\b",
    r"\bfrauen\s+wie\s+du\b",
    r"\bkein\s+(platz|recht)\s+für\s+(frauen|weiber)\b",
    r"\b(weib|weiber|schlampe|hure|schlampen)\b",
    r"\b(bitch|whore|slut|cunt)\b",
    r"\b(keine\s+meinung|keine\s+ahnung|nichts\s+zu\s+sagen)\s+(haben|verdient)\b",
    r"\b(meinung\s+verdient|recht\s+auf\s+meinung)\b",
    r"frauen\s+(können|können\s+nicht|dürfen\s+nicht)\b",
]

SEXUAL_HARASSMENT_SIGNALS = [
    r"\b(send|show)\s+(me|nudes|pics|photos)\b",
    r"\bsex\s+(with|from)\s+(you|her)\b",
    r"\b(fick|fick dich|ficken)\b",
    r"\b(schick|zeig)\s+(mir|bilder|fotos)\b",
]

HARASSMENT_SIGNALS = [
    r"\b(idiot|moron|stupid|dumb|brain\s*dead|malnourished|loser)\b",
    r"\b(shut\s+up|stfu|nobody\s+asked|nobody\s+cares)\b",
    r"\b(delete\s+(this|yourself)|go\s+die|kys)\b",
    r"\b(idiot|dumm|blöd|vollidiot|depp)\b",
    r"\bhalt\s+(die\s+)?klappe\b",
]

BODY_SHAMING_SIGNALS = [
    r"\b(fat|ugly|disgusting|gross|hideous)\b",
    r"\b(lose\s+weight|diet|gym)\b",
    r"\b(nobody\s+wants|no\s+one\s+wants)\s+(you|her)\b",
    r"\b(hässlich|fett|eklig|widerlich)\b",
]

FALSE_FACTS_SIGNALS = [
    r"\b(protein\s+deficient|b12\s+deficient|malnourished|unhealthy\s+diet)\b",
    r"\b(vegans\s+(are|will|can))\b",
    r"\bwissenschaftlich\s+bewiesen\b",
]

SCAM_SIGNALS = [
    r"\b(guaranteed|garantiert)\s+(return|profit|rendite|gewinn)\b",
    r"\b\d+\s*%\s*(monthly|monatlich|täglich|daily|weekly|wöchentlich)\s*(return|rendite|profit|gewinn)\b",
    r"\b\d+\s*%\s*(monatliche|tägliche|wöchentliche)\s*(rendite|gewinn|profit)\b",
    r"\b(send|transfer|überweise|schick|sende)\s+(bitcoin|btc|crypto|ethereum|eth|usdt|geld|money)\b",
    r"\bwallet\s+(address|adresse)\b",
    r"\b(verification|withdrawal)\s+fee\b",
    r"\b(verifizierungsgebühr|auszahlungsgebühr|freischaltgebühr)\b",
    r"\b(act\s+now|jetzt\s+handeln|limited\s+time|begrenzte\s+zeit)\b",
    r"\b(investment\s+platform|investitionsplattform|trading\s+platform|handelsplattform)\b",
    r"\bi\s+(help|helped)\s+\d+\s+(people|clients|customers|kunden)\s+(earn|make|profit)\b",
    r"\b(double|verdoppeln)\s+(your\s+money|dein\s+geld)\b",
    r"\b(schick|überweise|sende)\s+\d+\s*€?\s*(in|per|via)?\s*(bitcoin|btc|crypto|krypto)\b",
    r"\bmonatliche\s+rendite\b",
    r"\b(investier|investiere)\s+(jetzt|heute|sofort)\b",
]

PHISHING_SIGNALS = [
    r"\b(click|klick(e)?)\s+(here|hier|this\s+link|diesen\s+link)\b",
    r"\b(verify|verifizier(e)?)\s+(your|dein(e)?)\s+(account|konto|identity|identität)\b",
    r"\b(account\s+(suspended|gesperrt|blocked|deaktiviert))\b",
    r"\b(login|anmeld(e|en))\s+(required|erforderlich|needed)\b",
    r"\b(update|aktualisier(e|en))\s+(your|dein(e)?)\s+(payment|zahlung|billing)\b",
    r"http[s]?://(?!instagram\.com|facebook\.com|google\.com)\S+\.(ru|cn|xyz|top|click|tk)\b",
]

ROMANCE_SCAM_SIGNALS = [
    r"\b(i\s+love\s+you|ich\s+liebe\s+dich)\b.*\b(money|geld|send|überweise)\b",
    r"\b(stranded|stuck|gestrandet|festgehalten)\b.*\b(money|geld|help|hilfe)\b",
    r"\b(military|soldat|soldier|deployed|im\s+einsatz)\b.*\b(money|geld|send)\b",
    r"\b(gift\s+card|geschenkkarte|itunes|amazon\s+card)\b",
    r"\bcan('t)?\s+(video|videocall|webcam)\b",
]

IMPERSONATION_SIGNALS = [
    r"\b(official|offiziell|verified|verifiziert)\s+(account|konto|representative|mitarbeiter)\b",
    r"\b(i\s+am|ich\s+bin)\s+(from|von|bei)\s+(instagram|facebook|google|amazon|microsoft|apple|paypal|bank)\b",
    r"\b(support\s+team|kundendienst|customer\s+service)\b.*\b(urgent|dringend|immediately|sofort)\b",
    r"\byour\s+account\s+will\s+be\s+(deleted|suspended|terminated|gesperrt|gelöscht)\b",
]


def _match_signals(text: str, patterns: list[str]) -> bool:
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in patterns)


def classify(text: str) -> ClassificationResult:
    categories: list[Category] = []
    applicable_laws: list[GermanLaw] = []
    severity = Severity.LOW
    requires_immediate_action = False

    is_death_threat = _match_signals(text, DEATH_THREAT_SIGNALS)
    is_threat = _match_signals(text, THREAT_SIGNALS)
    is_misogyny = _match_signals(text, MISOGYNY_SIGNALS)
    is_sexual = _match_signals(text, SEXUAL_HARASSMENT_SIGNALS)
    is_harassment = _match_signals(text, HARASSMENT_SIGNALS)
    is_body_shaming = _match_signals(text, BODY_SHAMING_SIGNALS)
    is_false_facts = _match_signals(text, FALSE_FACTS_SIGNALS)
    is_scam = _match_signals(text, SCAM_SIGNALS)
    is_phishing = _match_signals(text, PHISHING_SIGNALS)
    is_romance_scam = _match_signals(text, ROMANCE_SCAM_SIGNALS)
    is_impersonation = _match_signals(text, IMPERSONATION_SIGNALS)

    if is_death_threat:
        categories.append(Category.DEATH_THREAT)
        categories.append(Category.THREAT)
        severity = Severity.CRITICAL
        requires_immediate_action = True
        applicable_laws.extend([LAW_126A, LAW_241])

    elif is_threat:
        categories.append(Category.THREAT)
        severity = Severity.HIGH
        requires_immediate_action = True
        applicable_laws.append(LAW_241)

    if is_misogyny:
        categories.append(Category.MISOGYNY)
        severity = max(severity, Severity.HIGH, key=lambda s: list(Severity).index(s))
        applicable_laws.append(LAW_185)

    if is_sexual:
        categories.append(Category.SEXUAL_HARASSMENT)
        severity = max(severity, Severity.HIGH, key=lambda s: list(Severity).index(s))
        requires_immediate_action = True
        if LAW_185 not in applicable_laws:
            applicable_laws.append(LAW_185)

    if is_harassment:
        categories.append(Category.HARASSMENT)
        if severity == Severity.LOW:
            severity = Severity.MEDIUM
        if LAW_185 not in applicable_laws:
            applicable_laws.append(LAW_185)

    if is_body_shaming:
        categories.append(Category.BODY_SHAMING)
        if severity == Severity.LOW:
            severity = Severity.MEDIUM
        if LAW_185 not in applicable_laws:
            applicable_laws.append(LAW_185)

    if is_false_facts:
        categories.append(Category.FALSE_FACTS)
        if LAW_186 not in applicable_laws:
            applicable_laws.append(LAW_186)

    if is_scam:
        categories.append(Category.SCAM)
        categories.append(Category.INVESTMENT_FRAUD)
        severity = Severity.CRITICAL
        requires_immediate_action = True
        applicable_laws.extend([LAW_263, LAW_263A])

    if is_phishing:
        categories.append(Category.PHISHING)
        severity = Severity.CRITICAL
        requires_immediate_action = True
        if LAW_263A not in applicable_laws:
            applicable_laws.extend([LAW_263, LAW_263A])

    if is_romance_scam:
        categories.append(Category.ROMANCE_SCAM)
        categories.append(Category.SCAM)
        severity = Severity.CRITICAL
        requires_immediate_action = True
        if LAW_263 not in applicable_laws:
            applicable_laws.extend([LAW_263, LAW_263A])

    if is_impersonation:
        categories.append(Category.IMPERSONATION)
        if severity not in [Severity.CRITICAL]:
            severity = Severity.HIGH
        if LAW_269 not in applicable_laws:
            applicable_laws.extend([LAW_263, LAW_269])

    if not categories:
        categories.append(Category.HARASSMENT)
        severity = Severity.LOW
        applicable_laws.append(LAW_185)

    # NetzDG always applies for Instagram content
    applicable_laws.append(NETZ_DG)

    # Remove duplicates while preserving order
    seen = set()
    applicable_laws = [l for l in applicable_laws if not (l.paragraph in seen or seen.add(l.paragraph))]

    summary_en, summary_de = _build_summaries(categories, severity)
    consequences_en, consequences_de = _build_consequences(severity, applicable_laws)

    confidence = _estimate_confidence(categories, text)

    return ClassificationResult(
        severity=severity,
        categories=list(set(categories)),
        confidence=confidence,
        requires_immediate_action=requires_immediate_action,
        summary=summary_en,
        summary_de=summary_de,
        applicable_laws=applicable_laws,
        potential_consequences=consequences_en,
        potential_consequences_de=consequences_de
    )


def _build_summaries(categories: list[Category], severity: Severity) -> tuple[str, str]:
    parts_en = []
    parts_de = []

    if Category.DEATH_THREAT in categories:
        parts_en.append("contains an explicit death threat")
        parts_de.append("enthält eine explizite Todesdrohung")
    elif Category.THREAT in categories:
        parts_en.append("contains a credible threat")
        parts_de.append("enthält eine glaubwürdige Drohung")

    if Category.MISOGYNY in categories:
        parts_en.append("is misogynistic in nature")
        parts_de.append("ist misogyner Natur")

    if Category.SEXUAL_HARASSMENT in categories:
        parts_en.append("constitutes sexual harassment")
        parts_de.append("stellt sexuelle Belästigung dar")

    if Category.BODY_SHAMING in categories:
        parts_en.append("contains body shaming")
        parts_de.append("enthält Body-Shaming")

    if Category.FALSE_FACTS in categories:
        parts_en.append("spreads false factual claims")
        parts_de.append("verbreitet falsche Tatsachenbehauptungen")

    if Category.SCAM in categories or Category.INVESTMENT_FRAUD in categories:
        parts_en.append("shows clear indicators of investment fraud / scam")
        parts_de.append("zeigt deutliche Merkmale von Investitionsbetrug / Scam")

    if Category.PHISHING in categories:
        parts_en.append("is a phishing attempt designed to steal credentials or data")
        parts_de.append("ist ein Phishing-Versuch zur Entwendung von Zugangsdaten oder Daten")

    if Category.ROMANCE_SCAM in categories:
        parts_en.append("shows classic romance scam / advance-fee fraud patterns")
        parts_de.append("zeigt klassische Romance-Scam / Vorschussbetrug-Muster")

    if Category.IMPERSONATION in categories:
        parts_en.append("involves impersonation of a trusted entity")
        parts_de.append("beinhaltet die Imitation einer vertrauenswürdigen Stelle")

    if Category.HARASSMENT in categories and len(parts_en) == 0:
        parts_en.append("constitutes personal harassment")
        parts_de.append("stellt persönliche Belästigung dar")

    base_en = "This content " + " and ".join(parts_en) + "."
    base_de = "Dieser Inhalt " + " und ".join(parts_de) + "."

    return base_en, base_de


def _build_consequences(severity: Severity, laws: list[GermanLaw]) -> tuple[str, str]:
    law_refs = ", ".join(l.paragraph for l in laws if l.paragraph != "NetzDG § 3")

    if severity == Severity.CRITICAL:
        en = f"URGENT: This may constitute a criminal offense under {law_refs}. File a police report (Strafanzeige) immediately. Under NetzDG, this must be removed within 24 hours."
        de = f"DRINGEND: Dies kann eine Straftat nach {law_refs} darstellen. Erstatten Sie sofort Strafanzeige. Nach NetzDG muss dies innerhalb von 24 Stunden entfernt werden."
    elif severity == Severity.HIGH:
        en = f"This likely violates {law_refs}. A formal NetzDG report to Instagram is strongly recommended. Consider filing a police report."
        de = f"Dies verstößt wahrscheinlich gegen {law_refs}. Eine formelle NetzDG-Meldung an Instagram wird dringend empfohlen. Erwägen Sie eine Strafanzeige."
    elif severity == Severity.MEDIUM:
        en = f"This may violate {law_refs}. A NetzDG report to Instagram is recommended. Document and preserve evidence."
        de = f"Dies kann gegen {law_refs} verstoßen. Eine NetzDG-Meldung an Instagram wird empfohlen. Dokumentieren und sichern Sie Beweise."
    else:
        en = f"This content may be reportable under platform terms of service. Document and preserve evidence."
        de = f"Dieser Inhalt kann nach den Nutzungsbedingungen der Plattform gemeldet werden. Dokumentieren und sichern Sie Beweise."

    return en, de


def _estimate_confidence(categories: list[Category], text: str) -> float:
    base = 0.75
    if len(text) > 50:
        base += 0.05
    if len(categories) > 1:
        base += 0.05
    if Category.DEATH_THREAT in categories or Category.THREAT in categories:
        base += 0.1
    if Category.SCAM in categories or Category.PHISHING in categories:
        base += 0.1
    return min(base, 0.99)
