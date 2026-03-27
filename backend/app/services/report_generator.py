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
        evidence_summaries.append({
            "url": ev.url,
            "author": ev.author_username,
            "captured_at": ev.captured_at.isoformat(),
            "content": ev.content_text,
            "severity": c.severity.value if c else "unknown",
            "categories": [cat.value for cat in c.categories] if c else [],
            "laws": [l.paragraph for l in c.applicable_laws] if c else [],
            "archived_url": ev.archived_url,
            "content_hash": ev.content_hash,
        })

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
        ev for ev in case.evidence_items
        if ev.classification and ev.classification.severity in [Severity.HIGH, Severity.CRITICAL]
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
            if is_de else
            f"NetzDG Report: Illegal Content – {len(illegal_items)} incidents"
        ),
        "body": _netzdg_body(case, illegal_items, laws_referenced, is_de),
        "referenced_laws": list(laws_referenced),
        "urls_to_report": [ev.url for ev in illegal_items],
        "archived_evidence": [ev.archived_url for ev in illegal_items if ev.archived_url],
        "removal_deadline": (
            "24 Stunden (offensichtlich rechtswidrige Inhalte)" if is_de
            else "24 hours (clearly illegal content)"
        ) if case.overall_severity == Severity.CRITICAL else (
            "7 Tage" if is_de else "7 days"
        ),
    }


def _netzdg_body(case, items, laws, is_de: bool) -> str:
    if is_de:
        return f"""Sehr geehrte Damen und Herren,

hiermit erstatten wir gemäß § 3 NetzDG eine Meldung über rechtswidrige Inhalte auf Ihrer Plattform.

Fallnummer: {case.id}
Datum der Erfassung: {case.created_at.strftime('%d.%m.%Y')}
Anzahl gemeldeter Inhalte: {len(items)}

Kontext:
{case.victim_context or 'Siehe beigefügte Belege.'}

Die gemeldeten Inhalte verstoßen gegen folgende Straftatbestände des deutschen Rechts:
{chr(10).join(f'- {law}' for law in laws)}

Die vollständigen Belege inkl. Archivierungslinks und Prüfsummen sind beigefügt.

Wir bitten um Entfernung der Inhalte innerhalb der gesetzlichen Frist und um Bestätigung der Maßnahmen.

Mit freundlichen Grüßen,
SafeVoice – Dokumentationsplattform für digitale Gewalt"""
    else:
        return f"""Dear Sir or Madam,

We hereby file a report under § 3 NetzDG regarding illegal content on your platform.

Case ID: {case.id}
Date of capture: {case.created_at.strftime('%Y-%m-%d')}
Number of reported items: {len(items)}

Context:
{case.victim_context or 'See attached evidence.'}

The reported content violates the following provisions of German criminal law:
{chr(10).join(f'- {law}' for law in laws)}

Full evidence including archive links and checksums is attached.

We request removal within the statutory deadline and confirmation of actions taken.

Regards,
SafeVoice – Digital Violence Documentation Platform"""


def _police_report(case: Case, lang: str) -> dict:
    is_de = lang == "de"

    critical_items = [
        ev for ev in case.evidence_items
        if ev.classification and ev.classification.requires_immediate_action
    ]

    return {
        "report_type": "police",
        "generated_at": datetime.now().isoformat(),
        "case_id": case.id,
        "online_report_url": "https://www.onlinewache.polizei.de",
        "subject": (
            f"Strafanzeige: Digitale Belästigung und Bedrohung – {len(critical_items)} kritische Vorfälle"
            if is_de else
            f"Criminal Complaint: Digital Harassment and Threats – {len(critical_items)} critical incidents"
        ),
        "body": _police_body(case, critical_items, is_de),
        "what_to_bring": (
            [
                "Diesen Bericht (ausgedruckt oder digital)",
                "Screenshots aller Vorfälle",
                "Archivierungslinks als Nachweis",
                "Lichtbildausweis",
                "Zeitliche Dokumentation der Vorfälle",
            ] if is_de else [
                "This report (printed or digital)",
                "Screenshots of all incidents",
                "Archive links as evidence",
                "Photo ID",
                "Timeline documentation of incidents",
            ]
        ),
    }


def _police_body(case, critical_items, is_de: bool) -> str:
    if is_de:
        return f"""STRAFANZEIGE

Anzeigeerstatterin/Anzeigeerstatter: [NAME DES OPFERS]
Datum: {datetime.now().strftime('%d.%m.%Y')}

Sachverhalt:
Ich erstatte Strafanzeige gegen unbekannte bzw. bekannte Täter wegen digitaler Belästigung, Bedrohung und/oder übler Nachrede über die Plattform Instagram.

Tatzeit: {case.created_at.strftime('%d.%m.%Y')} bis {case.updated_at.strftime('%d.%m.%Y')}
Tatort: Instagram (online), Plattform betrieben von Meta Platforms Ireland Limited

Kontext:
{case.victim_context or 'Siehe Anlagen.'}

Kritische Vorfälle ({len(critical_items)}):
{chr(10).join(f"- {ev.captured_at.strftime('%d.%m.%Y %H:%M')} Uhr | @{ev.author_username}: {ev.content_text[:100]}..." for ev in critical_items)}

Rechtliche Einordnung:
Die beschriebenen Handlungen erfüllen möglicherweise die Tatbestände der §§ 185, 186, 241 StGB sowie ggf. § 126a StGB.

Alle Beweise wurden digital archiviert und mit Prüfsummen gesichert. Archivierungslinks sowie Bildschirmfotos sind beigefügt.

Ich bitte um Aufnahme der Strafanzeige und Einleitung der erforderlichen Ermittlungsmaßnahmen.

[UNTERSCHRIFT]"""
    else:
        return f"""CRIMINAL COMPLAINT

Complainant: [VICTIM NAME]
Date: {datetime.now().strftime('%Y-%m-%d')}

Facts:
I hereby file a criminal complaint against unknown and/or identified perpetrators for digital harassment, threats, and/or defamation via Instagram.

Time of offense: {case.created_at.strftime('%Y-%m-%d')} to {case.updated_at.strftime('%Y-%m-%d')}
Location: Instagram (online), platform operated by Meta Platforms Ireland Limited

Context:
{case.victim_context or 'See attachments.'}

Critical incidents ({len(critical_items)}):
{chr(10).join(f"- {ev.captured_at.strftime('%Y-%m-%d %H:%M')} | @{ev.author_username}: {ev.content_text[:100]}..." for ev in critical_items)}

Legal classification:
The described conduct may constitute offenses under §§ 185, 186, 241 StGB and potentially § 126a StGB.

All evidence has been digitally archived and secured with checksums. Archive links and screenshots are attached.

I request that this complaint be recorded and appropriate investigations initiated.

[SIGNATURE]"""


def _recommended_actions(case: Case, lang: str) -> list[str]:
    is_de = lang == "de"
    actions = []

    has_critical = case.overall_severity == Severity.CRITICAL
    has_high = case.overall_severity in [Severity.HIGH, Severity.CRITICAL]

    if has_critical:
        actions.append(
            "SOFORT: Strafanzeige bei der Polizei erstatten (online: www.onlinewache.polizei.de)"
            if is_de else
            "IMMEDIATELY: File police report (online: www.onlinewache.polizei.de)"
        )
        actions.append(
            "SOFORT: NetzDG-Meldung bei Instagram einreichen (24h-Löschfrist)"
            if is_de else
            "IMMEDIATELY: File NetzDG report with Instagram (24h removal deadline)"
        )

    if has_high:
        actions.append(
            "Unterstützung bei HateAid suchen: https://hateaid.org (kostenlose Beratung)"
            if is_de else
            "Seek support at HateAid: https://hateaid.org (free counseling)"
        )
        actions.append(
            "Konten der Täter:innen auf Instagram melden"
            if is_de else
            "Report perpetrator accounts on Instagram"
        )

    actions.append(
        "Alle Belege an einem sicheren Ort aufbewahren"
        if is_de else
        "Keep all evidence stored securely"
    )
    actions.append(
        "Betroffene Accounts blockieren um weiteren Kontakt zu verhindern"
        if is_de else
        "Block offending accounts to prevent further contact"
    )

    return actions
