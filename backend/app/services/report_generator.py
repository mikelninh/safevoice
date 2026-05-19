"""
Report generator service.
Produces structured reports for NetzDG, police (Strafanzeige), and general export.
"""

from datetime import datetime
from app.models.evidence import Case, Severity, Category


def generate_report(case: Case, report_type: str = "general", lang: str = "de") -> dict:
    if report_type == "netzdg":
        return _netzdg_report(case, lang)
    elif report_type == "police":
        return _police_report(case, lang)
    else:
        return _general_report(case, lang)


def _general_report(case: Case, lang: str) -> dict:
    is_de = lang == "de"

    evidence_summaries = []
    for ev in case.evidence_items:
        c = ev.classification
        evidence_summaries.append(
            {
                "url": ev.url,
                "author": ev.author_username,
                "captured_at": ev.captured_at.isoformat(),
                "content": ev.content_text,
                "severity": c.severity.value if c else "unknown",
                "categories": [cat.value for cat in c.categories] if c else [],
                "laws": [l.paragraph for l in c.applicable_laws] if c else [],
                "archived_url": ev.archived_url,
                "content_hash": ev.content_hash,
            }
        )

    return {
        "report_type": "general",
        "generated_at": datetime.now().isoformat(),
        "case_id": case.id,
        "title": case.title,
        "overall_severity": case.overall_severity.value,
        "victim_context": case.victim_context,
        "evidence_count": len(case.evidence_items),
        "pattern_flags": [
            {
                "type": f.type,
                "description": f.description_de if is_de else f.description,
                "severity": f.severity.value,
                "evidence_count": f.evidence_count,
            }
            for f in case.pattern_flags
        ],
        "evidence": evidence_summaries,
        "recommended_actions": _recommended_actions(case, lang),
    }


def _netzdg_report(case: Case, lang: str) -> dict:
    is_de = lang == "de"

    illegal_items = [
        ev
        for ev in case.evidence_items
        if ev.classification
        and ev.classification.severity in [Severity.HIGH, Severity.CRITICAL]
    ]

    laws_referenced = set()
    for ev in illegal_items:
        if ev.classification:
            for law in ev.classification.applicable_laws:
                if law.paragraph != "NetzDG § 3":
                    laws_referenced.add(law.paragraph)

    return {
        "report_type": "netzdg",
        "generated_at": datetime.now().isoformat(),
        "platform": "Instagram (Meta Platforms Ireland Limited)",
        "platform_contact": "https://www.facebook.com/help/contact/274459462613911",
        "legal_basis": "Netzwerkdurchsetzungsgesetz (NetzDG) § 3",
        "case_id": case.id,
        "subject": (
            f"NetzDG-Meldung: Rechtswidrige Inhalte – {len(illegal_items)} Vorfälle"
            if is_de
            else f"NetzDG Report: Illegal Content – {len(illegal_items)} incidents"
        ),
        "body": _netzdg_body(case, illegal_items, laws_referenced, is_de),
        "referenced_laws": list(laws_referenced),
        "urls_to_report": [ev.url for ev in illegal_items],
        "archived_evidence": [
            ev.archived_url for ev in illegal_items if ev.archived_url
        ],
        "removal_deadline": (
            "24 Stunden (offensichtlich rechtswidrige Inhalte)"
            if is_de
            else "24 hours (clearly illegal content)"
        )
        if case.overall_severity == Severity.CRITICAL
        else ("7 Tage" if is_de else "7 days"),
    }


def _netzdg_body(case, items, laws, is_de: bool) -> str:
    if is_de:
        return f"""Sehr geehrte Damen und Herren,

hiermit erstatten wir gemäß § 3 NetzDG eine Meldung über rechtswidrige Inhalte auf Ihrer Plattform.

Fallnummer: {case.id}
Datum der Erfassung: {case.created_at.strftime("%d.%m.%Y")}
Anzahl gemeldeter Inhalte: {len(items)}

Kontext:
{case.victim_context or "Siehe beigefügte Belege."}

Die gemeldeten Inhalte verstoßen gegen folgende Straftatbestände des deutschen Rechts:
{chr(10).join(f"- {law}" for law in laws)}

Die vollständigen Belege inkl. Archivierungslinks und Prüfsummen sind beigefügt.

Wir bitten um Entfernung der Inhalte innerhalb der gesetzlichen Frist und um Bestätigung der Maßnahmen.

Mit freundlichen Grüßen,
SafeVoice – Dokumentationsplattform für digitale Gewalt"""
    else:
        return f"""Dear Sir or Madam,

We hereby file a report under § 3 NetzDG regarding illegal content on your platform.

Case ID: {case.id}
Date of capture: {case.created_at.strftime("%Y-%m-%d")}
Number of reported items: {len(items)}

Context:
{case.victim_context or "See attached evidence."}

The reported content violates the following provisions of German criminal law:
{chr(10).join(f"- {law}" for law in laws)}

Full evidence including archive links and checksums is attached.

We request removal within the statutory deadline and confirmation of actions taken.

Regards,
SafeVoice – Digital Violence Documentation Platform"""


def _police_report(case: Case, lang: str) -> dict:
    is_de = lang == "de"

    # Every documented incident goes into a Strafanzeige — Beleidigung (§ 185)
    # is reportable even at medium severity. We mark critical ones inline in
    # the body but never drop non-critical evidence.
    all_items = list(case.evidence_items)
    critical_count = sum(
        1
        for ev in all_items
        if ev.classification and ev.classification.requires_immediate_action
    )

    if is_de:
        if critical_count:
            subject = (
                f"Strafanzeige: Digitale Belästigung und Bedrohung – "
                f"{len(all_items)} Vorfälle ({critical_count} kritisch)"
            )
        else:
            subject = f"Strafanzeige: Digitale Belästigung – {len(all_items)} dokumentierte Vorfälle"
    else:
        if critical_count:
            subject = (
                f"Criminal Complaint: Digital Harassment and Threats – "
                f"{len(all_items)} incidents ({critical_count} critical)"
            )
        else:
            subject = f"Criminal Complaint: Digital Harassment – {len(all_items)} documented incidents"

    return {
        "report_type": "police",
        "generated_at": datetime.now().isoformat(),
        "case_id": case.id,
        "online_report_url": "https://www.polizei.de/Polizei/DE/Einrichtungen/onlinewache_node.html",
        "subject": subject,
        "body": _police_body(case, all_items, is_de),
        "what_to_bring": (
            [
                "Diesen Bericht (ausgedruckt oder digital)",
                "Screenshots aller Vorfälle",
                "Archivierungslinks als Nachweis",
                "Lichtbildausweis",
                "Zeitliche Dokumentation der Vorfälle",
            ]
            if is_de
            else [
                "This report (printed or digital)",
                "Screenshots of all incidents",
                "Archive links as evidence",
                "Photo ID",
                "Timeline documentation of incidents",
            ]
        ),
    }


def _police_body(case, items, is_de: bool) -> str:
    """Build the Strafanzeige body. `items` should be ALL evidence — never
    pre-filtered to "critical only", because Beleidigung (§ 185) is
    reportable at any severity. Critical pieces are flagged inline."""
    crit_count = sum(
        1
        for ev in items
        if ev.classification and ev.classification.requires_immediate_action
    )

    def _author(ev) -> str:
        # "@unknown" reads as a bug in the body of a Strafanzeige. Switch
        # absent handles to a labelled placeholder that survives copy-paste
        # into the Onlinewache form.
        h = (ev.author_username or "").strip()
        if not h or h.lower() in {"unknown", "anonymous", "—", "-", "anonym"}:
            return "Verfasser:in unbekannt"
        return f"@{h}"

    def _author_en(ev) -> str:
        h = (ev.author_username or "").strip()
        if not h or h.lower() in {"unknown", "anonymous", "—", "-", "anonym"}:
            return "Author unknown"
        return f"@{h}"

    def _fmt_de(ev) -> str:
        crit = (
            " [KRITISCH]"
            if ev.classification and ev.classification.requires_immediate_action
            else ""
        )
        return (
            f"- {ev.captured_at.strftime('%d.%m.%Y %H:%M')} Uhr | "
            f"{_author(ev)}{crit}: {ev.content_text[:140]}"
            + ("…" if len(ev.content_text) > 140 else "")
        )

    def _fmt_en(ev) -> str:
        crit = (
            " [CRITICAL]"
            if ev.classification and ev.classification.requires_immediate_action
            else ""
        )
        return (
            f"- {ev.captured_at.strftime('%Y-%m-%d %H:%M')} | "
            f"{_author_en(ev)}{crit}: {ev.content_text[:140]}"
            + ("…" if len(ev.content_text) > 140 else "")
        )

    # Derive Tatort + applicable laws from the actual evidence — the old
    # hardcoded "Instagram, Meta Platforms Ireland" mislabels every X /
    # TikTok / YouTube case and is the kind of detail that destroys
    # credibility when an Anwält:in reads the PDF.
    tatort_de, tatort_en = _build_tatort_lines(items)
    laws_de, laws_en = _build_laws_paragraph(items)
    beschuldigte_de, beschuldigte_en = _build_beschuldigte_lines(items)

    if is_de:
        header = (
            f"Dokumentierte Vorfälle ({len(items)} gesamt"
            + (f", davon {crit_count} kritisch" if crit_count else "")
            + "):"
        )
        listing = (
            "\n".join(_fmt_de(ev) for ev in items) or "- Keine Vorfälle dokumentiert."
        )
        return f"""STRAFANZEIGE

Anzeigeerstatterin/Anzeigeerstatter: [NAME DES OPFERS]
Datum: {datetime.now().strftime("%d.%m.%Y")}

Sachverhalt:
Ich erstatte Strafanzeige wegen digitaler Belästigung, Bedrohung und/oder übler Nachrede über {tatort_de["sachverhalt"]}.

Beschuldigte: {beschuldigte_de}
Tatzeit: {case.created_at.strftime("%d.%m.%Y")} bis {case.updated_at.strftime("%d.%m.%Y")}
Tatort: {tatort_de["tatort"]}

Kontext:
{case.victim_context or "Siehe Anlagen."}

{header}
{listing}

Rechtliche Einordnung:
{laws_de}

Alle Beweise wurden digital archiviert und mit Prüfsummen gesichert. Archivierungslinks sowie Bildschirmfotos sind beigefügt.

Ich bitte um Aufnahme der Strafanzeige und Einleitung der erforderlichen Ermittlungsmaßnahmen.

[UNTERSCHRIFT]"""

    header = (
        f"Documented incidents ({len(items)} total"
        + (f", {crit_count} critical" if crit_count else "")
        + "):"
    )
    listing = "\n".join(_fmt_en(ev) for ev in items) or "- No incidents documented."
    return f"""CRIMINAL COMPLAINT

Complainant: [VICTIM NAME]
Date: {datetime.now().strftime("%Y-%m-%d")}

Facts:
I hereby file a criminal complaint for digital harassment, threats, and/or defamation via {tatort_en["sachverhalt"]}.

Accused: {beschuldigte_en}
Time of offense: {case.created_at.strftime("%Y-%m-%d")} to {case.updated_at.strftime("%Y-%m-%d")}
Location: {tatort_en["tatort"]}

Context:
{case.victim_context or "See attachments."}

{header}
{listing}

Legal classification:
{laws_en}

All evidence has been digitally archived and secured with checksums. Archive links and screenshots are attached.

I request that this complaint be recorded and appropriate investigations initiated.

[SIGNATURE]"""


_PLATFORM_OPERATORS: dict[str, str] = {
    "instagram": "Meta Platforms Ireland Ltd.",
    "facebook": "Meta Platforms Ireland Ltd.",
    "threads": "Meta Platforms Ireland Ltd.",
    "whatsapp": "Meta Platforms Ireland Ltd.",
    "tiktok": "TikTok Technology Ltd. (Irland)",
    "x": "X Corp. / Twitter International Unlimited Company",
    "twitter": "X Corp. / Twitter International Unlimited Company",
    "youtube": "Google Ireland Ltd.",
    "reddit": "Reddit Inc.",
    "telegram": "Telegram FZ-LLC",
    "discord": "Discord Netherlands B.V.",
    "linkedin": "LinkedIn Ireland Unlimited Company",
}

_PLATFORM_DISPLAY: dict[str, str] = {
    "instagram": "Instagram",
    "facebook": "Facebook",
    "threads": "Threads",
    "whatsapp": "WhatsApp",
    "tiktok": "TikTok",
    "x": "X (vormals Twitter)",
    "twitter": "X (vormals Twitter)",
    "youtube": "YouTube",
    "reddit": "Reddit",
    "telegram": "Telegram",
    "discord": "Discord",
    "linkedin": "LinkedIn",
}


def _build_tatort_lines(items) -> tuple[dict[str, str], dict[str, str]]:
    """Build the Tatort + Sachverhalt-Plattform-Phrase from the evidence
    list. Empty platforms collapse to "Onlineplattformen". Multi-platform
    cases list every operator distinctly so the StA can route NetzDG
    requests correctly.
    """
    platforms_seen: list[str] = []
    for ev in items:
        p = (getattr(ev, "platform", "") or "").lower().strip()
        if p and p != "unknown" and p not in platforms_seen:
            platforms_seen.append(p)

    if not platforms_seen:
        return (
            {
                "sachverhalt": "Onlineplattformen",
                "tatort": "Onlineplattformen (Internet); Plattformbetreiber siehe Beweismittel",
            },
            {
                "sachverhalt": "online platforms",
                "tatort": "online platforms (internet); operators listed in evidence",
            },
        )

    display_de = [_PLATFORM_DISPLAY.get(p, p.capitalize()) for p in platforms_seen]
    operators = []
    for p in platforms_seen:
        op = _PLATFORM_OPERATORS.get(p)
        if op and op not in operators:
            operators.append(op)

    sachverhalt = (
        f"die Plattform {display_de[0]}"
        if len(display_de) == 1
        else f"die Plattformen {', '.join(display_de[:-1])} und {display_de[-1]}"
    )
    operator_clause = (
        (
            f", betrieben von {operators[0]}"
            if len(operators) == 1
            else f", betrieben von {'; '.join(operators)}"
        )
        if operators
        else ""
    )

    tatort_de = (
        f"{display_de[0]} (online){operator_clause}"
        if len(display_de) == 1
        else f"{', '.join(display_de)} (online){operator_clause}"
    )
    tatort_en = (
        f"{display_de[0]} (online){operator_clause}"
        if len(display_de) == 1
        else f"{', '.join(display_de)} (online){operator_clause}"
    )

    return (
        {"sachverhalt": sachverhalt, "tatort": tatort_de},
        {
            "sachverhalt": (
                f"the platform {display_de[0]}"
                if len(display_de) == 1
                else f"the platforms {', '.join(display_de[:-1])} and {display_de[-1]}"
            ),
            "tatort": tatort_en,
        },
    )


def _build_beschuldigte_lines(items) -> tuple[str, str]:
    """Render the Beschuldigte block from evidence.

    Previously the Sachverhalt said "unbekannte bzw. bekannte Täter" —
    a generic catch-all that gives the StA no handle. Now we derive
    the actual state from the evidence: collect non-placeholder author
    handles. If all are unknown → "unbekannt". If some known → list
    them as platform pseudonyms (StA can use them for Auskunftsersuchen).
    """
    real_handles: list[str] = []
    for ev in items:
        h = (getattr(ev, "author_username", "") or "").strip().lstrip("@")
        if not h:
            continue
        if h.lower() in {"unknown", "anonymous", "anonym", "—", "-"}:
            continue
        if h not in real_handles:
            real_handles.append(h)

    if not real_handles:
        return (
            "unbekannt (Täter:innen treten unter Pseudonym auf — siehe "
            "Hinweise an die Behörde zur Bestandsdaten-Auskunft).",
            "unknown (perpetrators acting under pseudonyms — see notes to "
            "investigating authority for subscriber-data request).",
        )

    handles_str = ", ".join(f"@{h}" for h in real_handles)
    if len(real_handles) == 1:
        return (
            f"bekannt unter Plattform-Pseudonym {handles_str} "
            f"(Identität dahinter unbekannt; Bestandsdaten-Auskunft "
            f"siehe Hinweise an die ermittelnde Behörde).",
            f"known as platform handle {handles_str} (identity unknown; "
            f"subscriber-data request — see notes to authority).",
        )
    return (
        f"{len(real_handles)} Plattform-Pseudonyme: {handles_str} "
        f"(Identitäten dahinter unbekannt; Bestandsdaten-Auskunft "
        f"siehe Hinweise an die ermittelnde Behörde).",
        f"{len(real_handles)} platform handles: {handles_str} (identities "
        f"unknown; subscriber-data request — see notes to authority).",
    )


def _build_laws_paragraph(items) -> tuple[str, str]:
    """Build the "Rechtliche Einordnung" paragraph from the actual statutes
    cited in the case's classifications. Avoids the previous hardcoded
    "§§ 185, 186, 241 StGB sowie ggf. § 126a StGB" which mislabels e.g. a
    pure death-threat case as a defamation case."""
    seen: list[str] = []
    for ev in items:
        c = getattr(ev, "classification", None)
        if not c:
            continue
        for law in getattr(c, "applicable_laws", []) or []:
            ref = getattr(law, "paragraph", None) or getattr(law, "section", None)
            if ref and ref not in seen:
                seen.append(str(ref))

    if not seen:
        return (
            "Die beschriebenen Handlungen können diverse Tatbestände des "
            "Strafrechts erfüllen. Die einschlägigen Paragraphen sind in "
            "den einzelnen Beweismittel-Abschnitten aufgeführt.",
            "The described conduct may fulfil multiple criminal offences. "
            "The applicable statutes are listed per evidence item.",
        )

    de = (
        "Die beschriebenen Handlungen erfüllen möglicherweise die Tatbestände der "
        + ", ".join(seen[:-1])
        + (" sowie " if len(seen) > 1 else "")
        + seen[-1]
        + "."
    )
    en = (
        "The described conduct may constitute offences under "
        + ", ".join(seen[:-1])
        + (" and " if len(seen) > 1 else "")
        + seen[-1]
        + "."
    )
    return de, en


def _recommended_actions(case: Case, lang: str) -> list[str]:
    is_de = lang == "de"
    actions = []

    has_critical = case.overall_severity == Severity.CRITICAL
    has_high = case.overall_severity in [Severity.HIGH, Severity.CRITICAL]

    if has_critical:
        actions.append(
            "SOFORT: Strafanzeige bei der Polizei erstatten (online: www.polizei.de/Polizei/DE/Einrichtungen/onlinewache_node.html)"
            if is_de
            else "IMMEDIATELY: File police report (online: www.polizei.de/Polizei/DE/Einrichtungen/onlinewache_node.html)"
        )
        actions.append(
            "SOFORT: NetzDG-Meldung bei Instagram einreichen (24h-Löschfrist)"
            if is_de
            else "IMMEDIATELY: File NetzDG report with Instagram (24h removal deadline)"
        )

    if has_high:
        actions.append(
            "Unterstützung bei HateAid suchen: https://hateaid.org (kostenlose Beratung)"
            if is_de
            else "Seek support at HateAid: https://hateaid.org (free counseling)"
        )
        actions.append(
            "Konten der Täter:innen auf Instagram melden"
            if is_de
            else "Report perpetrator accounts on Instagram"
        )

    actions.append(
        "Alle Belege an einem sicheren Ort aufbewahren"
        if is_de
        else "Keep all evidence stored securely"
    )
    actions.append(
        "Betroffene Accounts blockieren um weiteren Kontakt zu verhindern"
        if is_de
        else "Block offending accounts to prevent further contact"
    )

    return actions
