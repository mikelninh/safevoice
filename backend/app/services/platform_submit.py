"""
Platform API integration — structured NetzDG submission to social media platforms.
MVP: generates pre-filled submission data. Production: direct API calls.

Each platform has different NetzDG reporting mechanisms:
- Instagram/Facebook: Meta's content reporting API
- X/Twitter: X's transparency reporting
- TikTok: TikTok's content moderation portal
"""

from datetime import datetime, timezone
from app.models.evidence import Case, EvidenceItem, Severity


def generate_platform_submission(case: Case, platform: str, lang: str = "de") -> dict:
    """
    Generate a structured submission for a specific platform's NetzDG reporting.
    """
    is_de = lang == "de"

    platform_items = [ev for ev in case.evidence_items if ev.platform == platform]
    if not platform_items:
        platform_items = case.evidence_items  # fallback: all items

    handler = PLATFORM_HANDLERS.get(platform, _generic_submission)
    return handler(case, platform_items, is_de)


def _instagram_submission(case: Case, items: list[EvidenceItem], is_de: bool) -> dict:
    """Instagram/Meta NetzDG submission format."""
    urls = [ev.url for ev in items]
    critical = any(
        ev.classification and ev.classification.severity == Severity.CRITICAL
        for ev in items
    )

    return {
        "platform": "Instagram (Meta Platforms Ireland Limited)",
        "submission_type": "NetzDG § 3 Report",
        "submission_url": "https://help.instagram.com/contact/723586364339498",
        "alternative_url": "https://www.facebook.com/help/contact/274459462613911",
        "deadline": "24 Stunden" if critical and is_de else "24 hours" if critical else "7 Tage" if is_de else "7 days",
        "is_urgent": critical,
        "fields": {
            "reported_content_urls": urls,
            "violation_type": "NetzDG - rechtswidriger Inhalt" if is_de else "NetzDG - illegal content",
            "legal_basis": _collect_laws(items),
            "description": _build_description(case, items, is_de),
            "evidence_hashes": [ev.content_hash for ev in items],
            "archived_urls": [ev.archived_url for ev in items if ev.archived_url],
        },
        "instructions_de": (
            "1. Öffnen Sie den Link oben\n"
            "2. Wählen Sie 'NetzDG-Meldung'\n"
            "3. Fügen Sie die URLs der gemeldeten Inhalte ein\n"
            "4. Kopieren Sie den vorbereiteten Text in das Beschreibungsfeld\n"
            "5. Senden Sie die Meldung ab\n"
            "6. Speichern Sie die Bestätigungsnummer"
        ),
        "instructions_en": (
            "1. Open the link above\n"
            "2. Select 'NetzDG Report'\n"
            "3. Paste the reported content URLs\n"
            "4. Copy the prepared text into the description field\n"
            "5. Submit the report\n"
            "6. Save the confirmation number"
        ),
    }


def _x_submission(case: Case, items: list[EvidenceItem], is_de: bool) -> dict:
    """X/Twitter NetzDG submission format."""
    urls = [ev.url for ev in items]
    critical = any(
        ev.classification and ev.classification.severity == Severity.CRITICAL
        for ev in items
    )

    return {
        "platform": "X Corp. (formerly Twitter International ULC)",
        "submission_type": "NetzDG § 3 Report",
        "submission_url": "https://help.twitter.com/forms/netzdg",
        "deadline": "24 Stunden" if critical and is_de else "24 hours" if critical else "7 Tage" if is_de else "7 days",
        "is_urgent": critical,
        "fields": {
            "reported_content_urls": urls,
            "violation_type": "NetzDG - rechtswidriger Inhalt" if is_de else "NetzDG - illegal content",
            "legal_basis": _collect_laws(items),
            "description": _build_description(case, items, is_de),
            "evidence_hashes": [ev.content_hash for ev in items],
        },
        "instructions_de": (
            "1. Öffnen Sie den NetzDG-Meldelink oben\n"
            "2. Geben Sie die URLs der gemeldeten Tweets ein\n"
            "3. Wählen Sie die Art des Verstoßes\n"
            "4. Fügen Sie den vorbereiteten Text ein\n"
            "5. Senden Sie ab und notieren Sie die Referenznummer"
        ),
        "instructions_en": (
            "1. Open the NetzDG report link above\n"
            "2. Enter the URLs of the reported tweets\n"
            "3. Select the type of violation\n"
            "4. Paste the prepared description\n"
            "5. Submit and note the reference number"
        ),
    }


def _tiktok_submission(case: Case, items: list[EvidenceItem], is_de: bool) -> dict:
    """TikTok NetzDG submission format."""
    return {
        "platform": "TikTok Technology Limited",
        "submission_type": "NetzDG § 3 Report",
        "submission_url": "https://www.tiktok.com/legal/report/netzdg",
        "deadline": "7 Tage" if is_de else "7 days",
        "is_urgent": False,
        "fields": {
            "reported_content_urls": [ev.url for ev in items],
            "violation_type": "NetzDG - rechtswidriger Inhalt" if is_de else "NetzDG - illegal content",
            "legal_basis": _collect_laws(items),
            "description": _build_description(case, items, is_de),
        },
        "instructions_de": "Öffnen Sie den Link und folgen Sie dem NetzDG-Meldeformular.",
        "instructions_en": "Open the link and follow the NetzDG reporting form.",
    }


def _generic_submission(case: Case, items: list[EvidenceItem], is_de: bool) -> dict:
    """Generic submission for unknown platforms."""
    return {
        "platform": items[0].platform if items else "unknown",
        "submission_type": "NetzDG § 3 Report",
        "submission_url": None,
        "deadline": "7 Tage" if is_de else "7 days",
        "is_urgent": False,
        "fields": {
            "reported_content_urls": [ev.url for ev in items],
            "legal_basis": _collect_laws(items),
            "description": _build_description(case, items, is_de),
        },
        "instructions_de": "Suchen Sie die NetzDG-Meldestelle der Plattform und reichen Sie den vorbereiteten Text ein.",
        "instructions_en": "Find the platform's NetzDG reporting mechanism and submit the prepared text.",
    }


def _collect_laws(items: list[EvidenceItem]) -> list[str]:
    laws = set()
    for ev in items:
        if ev.classification:
            for law in ev.classification.applicable_laws:
                laws.add(law.paragraph)
    return sorted(laws)


def _build_description(case: Case, items: list[EvidenceItem], is_de: bool) -> str:
    if is_de:
        lines = [
            f"NetzDG-Meldung gemäß § 3 NetzDG",
            f"Fall-ID: {case.id}",
            f"Anzahl gemeldeter Inhalte: {len(items)}",
            "",
        ]
        for i, ev in enumerate(items, 1):
            lines.append(f"{i}. @{ev.author_username}: \"{ev.content_text[:100]}\"")
            lines.append(f"   URL: {ev.url}")
            if ev.classification:
                lines.append(f"   Schweregrad: {ev.classification.severity.value}")
                lines.append(f"   Gesetze: {', '.join(l.paragraph for l in ev.classification.applicable_laws)}")
            lines.append("")
        lines.append("Alle Beweise sind digital archiviert und mit SHA-256 Prüfsummen gesichert.")
        return "\n".join(lines)
    else:
        lines = [
            f"NetzDG Report pursuant to § 3 NetzDG",
            f"Case ID: {case.id}",
            f"Number of reported items: {len(items)}",
            "",
        ]
        for i, ev in enumerate(items, 1):
            lines.append(f"{i}. @{ev.author_username}: \"{ev.content_text[:100]}\"")
            lines.append(f"   URL: {ev.url}")
            if ev.classification:
                lines.append(f"   Severity: {ev.classification.severity.value}")
                lines.append(f"   Laws: {', '.join(l.paragraph for l in ev.classification.applicable_laws)}")
            lines.append("")
        lines.append("All evidence is digitally archived and secured with SHA-256 checksums.")
        return "\n".join(lines)


PLATFORM_HANDLERS = {
    "instagram": _instagram_submission,
    "x": _x_submission,
    "twitter": _x_submission,
    "tiktok": _tiktok_submission,
}
