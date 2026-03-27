"""
BaFin report generator.
Generates structured reports for the German financial regulator (Bundesanstalt
für Finanzdienstleistungsaufsicht) for investment fraud / scam cases.
"""

import re
from datetime import datetime, timezone
from app.models.evidence import Case, Category


def generate_bafin_report(case: Case, lang: str = "de") -> dict | None:
    """
    Generate a BaFin-formatted scam report.
    Returns None if the case doesn't contain scam/fraud evidence.
    """
    is_de = lang == "de"

    # Only generate for scam-related cases
    scam_categories = {Category.SCAM, Category.INVESTMENT_FRAUD, Category.ROMANCE_SCAM, Category.PHISHING}
    scam_items = [
        ev for ev in case.evidence_items
        if ev.classification and scam_categories.intersection(ev.classification.categories)
    ]

    if not scam_items:
        return None

    # Extract financial indicators from evidence
    wallet_addresses = []
    platform_names = []
    amounts = []

    for ev in scam_items:
        text = ev.content_text

        # Bitcoin/crypto wallet addresses
        btc_match = re.findall(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b', text)
        eth_match = re.findall(r'\b0x[a-fA-F0-9]{40}\b', text)
        wallet_addresses.extend(btc_match)
        wallet_addresses.extend(eth_match)

        # Euro amounts
        eur_match = re.findall(r'€\s*[\d.,]+|[\d.,]+\s*€|[\d.,]+\s*EUR', text)
        amounts.extend(eur_match)

        # Platform/website names
        url_match = re.findall(r'https?://[^\s]+', text)
        platform_names.extend(url_match)

        # Fake platform names (common patterns)
        fake_match = re.findall(r'\b\w+(?:trade|invest|crypto|profit|capital)\w*\b', text, re.IGNORECASE)
        platform_names.extend(fake_match)

    wallet_addresses = list(set(wallet_addresses))
    platform_names = list(set(platform_names))
    amounts = list(set(amounts))

    # Determine scam type
    categories_flat = set()
    for ev in scam_items:
        if ev.classification:
            categories_flat.update(ev.classification.categories)

    if Category.ROMANCE_SCAM in categories_flat:
        scam_type = "Romance Scam / Vorschussbetrug" if is_de else "Romance Scam / Advance-Fee Fraud"
    elif Category.INVESTMENT_FRAUD in categories_flat:
        scam_type = "Investitionsbetrug / Anlagebetrug" if is_de else "Investment Fraud"
    elif Category.PHISHING in categories_flat:
        scam_type = "Phishing / Identitätsdiebstahl" if is_de else "Phishing / Identity Theft"
    else:
        scam_type = "Online-Betrug" if is_de else "Online Fraud"

    now = datetime.now(timezone.utc)

    return {
        "report_type": "bafin",
        "generated_at": now.isoformat(),
        "case_id": case.id,
        "submit_url": "https://www.bafin.de/DE/Verbraucher/BeschswerdenAnsprechpartner/beschwerden_ansprechpartner_node.html",
        "subject": (
            f"Verdachtsmeldung: {scam_type} — {len(scam_items)} Vorfälle"
            if is_de else
            f"Suspicious Activity Report: {scam_type} — {len(scam_items)} incidents"
        ),
        "scam_type": scam_type,
        "evidence_count": len(scam_items),
        "financial_indicators": {
            "wallet_addresses": wallet_addresses,
            "mentioned_amounts": amounts,
            "platform_names": platform_names,
        },
        "body": _bafin_body(case, scam_items, scam_type, wallet_addresses, amounts, platform_names, is_de),
        "perpetrator_accounts": list(set(ev.author_username for ev in scam_items)),
        "urls": list(set(ev.url for ev in scam_items)),
    }


def _bafin_body(case, items, scam_type, wallets, amounts, platforms, is_de: bool) -> str:
    if is_de:
        lines = [
            "VERDACHTSMELDUNG AN DIE BAFIN",
            f"Bundesanstalt für Finanzdienstleistungsaufsicht",
            "",
            f"Datum: {datetime.now(timezone.utc).strftime('%d.%m.%Y')}",
            f"Fall-ID: {case.id}",
            f"Art des Betrugs: {scam_type}",
            "",
            "SACHVERHALT:",
            case.victim_context or "Siehe beigefügte Belege.",
            "",
            f"ANZAHL DER VORFÄLLE: {len(items)}",
            "",
        ]

        if wallets:
            lines.append("KRYPTOWÄHRUNGS-ADRESSEN:")
            for w in wallets:
                lines.append(f"  - {w}")
            lines.append("")

        if amounts:
            lines.append("GENANNTE BETRÄGE:")
            for a in amounts:
                lines.append(f"  - {a}")
            lines.append("")

        if platforms:
            lines.append("GENANNTE PLATTFORMEN/URLS:")
            for p in platforms:
                lines.append(f"  - {p}")
            lines.append("")

        lines.append("VERDÄCHTIGE KONTEN:")
        for item in items:
            lines.append(f"  - @{item.author_username} ({item.platform})")
        lines.append("")

        lines.append("BEWEISE:")
        for i, item in enumerate(items, 1):
            lines.append(f"  {i}. {item.captured_at.strftime('%d.%m.%Y') if hasattr(item.captured_at, 'strftime') else item.captured_at}")
            lines.append(f"     @{item.author_username}: \"{item.content_text[:200]}\"")
            lines.append(f"     URL: {item.url}")
            lines.append(f"     Prüfsumme: {item.content_hash}")
            lines.append("")

        lines.append("Alle Beweise wurden digital archiviert und mit SHA-256 Prüfsummen gesichert.")
        lines.append("")
        lines.append("--- Generiert von SafeVoice – Dokumentationsplattform für digitale Gewalt ---")
        return "\n".join(lines)

    else:
        lines = [
            "SUSPICIOUS ACTIVITY REPORT TO BAFIN",
            "Bundesanstalt für Finanzdienstleistungsaufsicht",
            "",
            f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
            f"Case ID: {case.id}",
            f"Fraud type: {scam_type}",
            "",
            "FACTS:",
            case.victim_context or "See attached evidence.",
            "",
            f"NUMBER OF INCIDENTS: {len(items)}",
            "",
        ]

        if wallets:
            lines.append("CRYPTOCURRENCY ADDRESSES:")
            for w in wallets:
                lines.append(f"  - {w}")
            lines.append("")

        if amounts:
            lines.append("MENTIONED AMOUNTS:")
            for a in amounts:
                lines.append(f"  - {a}")
            lines.append("")

        if platforms:
            lines.append("MENTIONED PLATFORMS/URLS:")
            for p in platforms:
                lines.append(f"  - {p}")
            lines.append("")

        lines.append("SUSPECT ACCOUNTS:")
        for item in items:
            lines.append(f"  - @{item.author_username} ({item.platform})")
        lines.append("")

        lines.append("EVIDENCE:")
        for i, item in enumerate(items, 1):
            lines.append(f"  {i}. {item.captured_at.strftime('%Y-%m-%d') if hasattr(item.captured_at, 'strftime') else item.captured_at}")
            lines.append(f"     @{item.author_username}: \"{item.content_text[:200]}\"")
            lines.append(f"     URL: {item.url}")
            lines.append(f"     Hash: {item.content_hash}")
            lines.append("")

        lines.append("All evidence has been digitally archived and secured with SHA-256 checksums.")
        lines.append("")
        lines.append("--- Generated by SafeVoice – Digital Violence Documentation Platform ---")
        return "\n".join(lines)
