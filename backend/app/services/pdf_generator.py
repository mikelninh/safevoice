"""
PDF generator for court-ready evidence reports.
Uses ReportLab to produce structured, professional PDFs.
Supports DE + EN, includes all evidence, classification, and legal references.

Design notes (revamped 2026-05-09):
- A4 print typography: 18pt section heads, 11pt body, 9pt meta, 8pt mono.
- Left margin 30mm so police/lawyers can 2-hole-punch without losing text.
- Severity is colour-coded across the document (green/amber/orange/red).
- Each evidence card looks like a court-exhibit row, not a flow of paragraphs.
- AI legal-assessment block is visually separated (tinted frame + disclaimer)
  so police can tell at a glance which words are the victim's vs. the model's.
- Footer on every page: "Generiert mit SafeVoice am DD.MM.YYYY · Fall <id8> · Seite N/M".
"""

import io
from datetime import datetime, timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)

from app.models.evidence import Case, EvidenceItem, Severity


# ── Severity palette ──────────────────────────────────────────────────────
# (badge bg, badge text, accent / left-rule)
_SEVERITY_PALETTE = {
    "low": ("#dcfce7", "#166534", "#16a34a"),  # green
    "medium": ("#fef3c7", "#92400e", "#d97706"),  # amber
    "high": ("#ffedd5", "#9a3412", "#ea580c"),  # orange
    "critical": ("#fee2e2", "#991b1b", "#dc2626"),  # red
}


def _severity_key(sev) -> str:
    if isinstance(sev, str):
        return sev
    try:
        return sev.value
    except Exception:
        return str(sev)


def _severity_colors(sev):
    bg, fg, accent = _SEVERITY_PALETTE.get(
        _severity_key(sev), ("#e2e8f0", "#334155", "#64748b")
    )
    return colors.HexColor(bg), colors.HexColor(fg), colors.HexColor(accent)


def generate_pdf(
    case: Case,
    report_type: str = "general",
    lang: str = "de",
    victim_name: str | None = None,
    victim_address: str | None = None,
    victim_phone: str | None = None,
    victim_email: str | None = None,
) -> bytes:
    """Generate a court-ready PDF report for a case."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=30 * mm,  # 30mm so 2-hole punch doesn't eat content
        rightMargin=20 * mm,
        topMargin=22 * mm,
        bottomMargin=22 * mm,
        title=f"SafeVoice · {case.id[:8]}",
        author="SafeVoice",
    )

    styles = _get_styles()
    is_de = lang == "de"
    elements: list = []
    now = datetime.now(timezone.utc)

    # ── 1. Masthead ─────────────────────────────────────────────────────
    elements.append(Paragraph("SafeVoice", styles["Title"]))
    elements.append(
        Paragraph(
            "Dokumentationsplattform für digitale Gewalt"
            if is_de
            else "Digital Violence Documentation Platform",
            styles["Subtitle"],
        )
    )
    elements.append(Spacer(1, 4 * mm))

    type_labels = {
        "general": ("Beweissicherungsbericht", "Evidence Documentation Report"),
        "netzdg": ("NetzDG-Meldung", "NetzDG Report"),
        "police": ("Strafanzeige – Vorlage", "Criminal Complaint – Template"),
    }
    label = type_labels.get(report_type, type_labels["general"])
    elements.append(Paragraph(label[0] if is_de else label[1], styles["ReportType"]))
    elements.append(
        HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#4338ca"))
    )
    elements.append(Spacer(1, 5 * mm))

    # ── 2. Executive summary card — police see this in 3s ───────────────
    elements.append(_executive_summary(case, victim_name, is_de, styles))
    elements.append(Spacer(1, 6 * mm))

    # ── 3. Strafanzeige body (formal complaint) ─────────────────────────
    if report_type == "police" and victim_name:
        from app.services.report_generator import _police_body  # local: avoid cycle

        elements.append(
            Paragraph(
                _l("Förmliche Strafanzeige", "Formal Criminal Complaint", is_de),
                styles["SectionHead"],
            )
        )
        elements.append(
            HRFlowable(
                width="100%",
                thickness=0.4,
                color=colors.HexColor("#cbd5e1"),
                spaceAfter=2 * mm,
            )
        )

        body = _police_body(case, list(case.evidence_items), is_de=is_de)
        sender_lines = [victim_name]
        if victim_address:
            sender_lines.append(victim_address)
        if victim_phone:
            sender_lines.append(f"Tel: {victim_phone}")
        if victim_email:
            sender_lines.append(f"E-Mail: {victim_email}")
        body = body.replace("[NAME DES OPFERS]", "\n".join(sender_lines))
        body = body.replace("[UNTERSCHRIFT]", victim_name)

        for paragraph in body.split("\n\n"):
            html = _escape(paragraph).replace("\n", "<br/>")
            elements.append(Paragraph(html, styles["Body"]))
            elements.append(Spacer(1, 2.5 * mm))

        elements.append(Spacer(1, 3 * mm))
        elements.append(
            HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"))
        )
        elements.append(Spacer(1, 5 * mm))

    # ── 4. Victim context ───────────────────────────────────────────────
    if case.victim_context:
        elements.append(
            Paragraph(
                _l("Kontext der betroffenen Person", "Victim context", is_de),
                styles["SectionHead"],
            )
        )
        elements.append(Paragraph(_escape(case.victim_context), styles["Body"]))
        elements.append(Spacer(1, 4 * mm))

    # ── 5. Pattern flags ────────────────────────────────────────────────
    if case.pattern_flags:
        elements.append(
            Paragraph(
                _l("Erkannte Muster", "Detected patterns", is_de),
                styles["SectionHead"],
            )
        )
        for flag in case.pattern_flags:
            desc = flag.description_de if is_de else flag.description
            elements.append(
                Paragraph(
                    f"<b>{flag.type}</b> ({_severity_label(flag.severity, is_de)}): "
                    f"{_escape(desc)}",
                    styles["Body"],
                )
            )
        elements.append(Spacer(1, 4 * mm))

    # ── 6. Evidence list — court-exhibit style ──────────────────────────
    elements.append(
        Paragraph(
            _l("Beweismittel", "Evidence Exhibits", is_de)
            + f" ({len(case.evidence_items)})",
            styles["SectionHead"],
        )
    )
    elements.append(
        HRFlowable(width="100%", thickness=0.4, color=colors.HexColor("#cbd5e1"))
    )
    elements.append(Spacer(1, 3 * mm))

    for i, ev in enumerate(case.evidence_items, 1):
        elements.append(_evidence_card(ev, i, is_de, styles))
        elements.append(Spacer(1, 4 * mm))

    # ── 7. AI legal assessment (police only) ────────────────────────────
    if report_type == "police":
        try:
            from app.services.legal_ai import analyze_case_legally

            analysis = analyze_case_legally(case)
            if analysis is not None:
                elements.append(Spacer(1, 4 * mm))
                elements.extend(_ai_assessment_block(analysis, is_de, styles))
        except Exception:
            import logging

            logging.getLogger(__name__).exception("Failed to embed legal AI in PDF")

    # ── 8. Closing legal notice ─────────────────────────────────────────
    elements.append(Spacer(1, 6 * mm))
    elements.append(
        HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#4338ca"))
    )
    elements.append(Spacer(1, 2 * mm))
    elements.append(
        Paragraph(
            _l(
                "Dieser Bericht wurde automatisch von SafeVoice generiert. "
                "Alle Inhalte sind mit SHA-256 Prüfsummen gesichert. "
                "Archivierungslinks dienen als unabhängiger Nachweis der Existenz "
                "der Inhalte zum Erfassungszeitpunkt.",
                "This report was automatically generated by SafeVoice. "
                "All content is secured with SHA-256 checksums. "
                "Archive links serve as independent proof of content existence "
                "at the time of capture.",
                is_de,
            ),
            styles["FooterNotice"],
        )
    )

    # Footer / page numbers
    footer_ctx = {
        "is_de": is_de,
        "case_short": case.id[:8] if case.id else "—",
        "generated": now.strftime("%d.%m.%Y") if is_de else now.strftime("%Y-%m-%d"),
    }

    def _on_page(canvas, doc_):
        _draw_footer(canvas, doc_, footer_ctx)

    doc.build(elements, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()


# ── Executive summary card ─────────────────────────────────────────────────


def _executive_summary(case: Case, victim_name, is_de: bool, styles: dict) -> Table:
    """One-glance card: who · severity · counts · laws."""
    sev_bg, sev_fg, sev_accent = _severity_colors(case.overall_severity)
    sev_text = _severity_label(case.overall_severity, is_de)

    # Aggregate laws across all evidence (deduplicated, preserve order).
    seen_laws: list[str] = []
    crit_count = 0
    for ev in case.evidence_items:
        c = ev.classification
        if not c:
            continue
        if c.requires_immediate_action:
            crit_count += 1
        for law in c.applicable_laws:
            if law.paragraph not in seen_laws:
                seen_laws.append(law.paragraph)
    laws_str = ", ".join(seen_laws) if seen_laws else "—"

    now = datetime.now(timezone.utc)

    label_style = styles["MetaLabel"]
    value_style = styles["MetaValue"]
    badge_style = ParagraphStyle(
        "ExecBadge",
        parent=styles["Body"],
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=sev_fg,
        alignment=1,
        leading=14,
    )

    # Severity badge as nested table so it has its own bg
    badge = Table(
        [[Paragraph(sev_text.upper(), badge_style)]],
        colWidths=[40 * mm],
    )
    badge.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), sev_bg),
                ("BOX", (0, 0), (-1, -1), 0.6, sev_accent),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    rows = [
        [
            Paragraph(_l("Anzeigeerstatter:in", "Complainant", is_de), label_style),
            Paragraph(_escape(victim_name) if victim_name else "—", value_style),
            Paragraph(_l("Schweregrad", "Severity", is_de), label_style),
            badge,
        ],
        [
            Paragraph(_l("Fall-ID", "Case ID", is_de), label_style),
            Paragraph(case.id, value_style),
            Paragraph(_l("Vorfälle", "Incidents", is_de), label_style),
            Paragraph(
                f"<b>{len(case.evidence_items)}</b>"
                + (
                    f" <font color='#dc2626'>({crit_count} "
                    + _l("kritisch", "critical", is_de)
                    + ")</font>"
                    if crit_count
                    else ""
                ),
                value_style,
            ),
        ],
        [
            Paragraph(_l("Erstellt", "Created", is_de), label_style),
            Paragraph(_fmt_dt(case.created_at, is_de), value_style),
            Paragraph(_l("Generiert", "Generated", is_de), label_style),
            Paragraph(_fmt_dt(now, is_de), value_style),
        ],
        [
            Paragraph(_l("§§ Gesamt", "Statutes", is_de), label_style),
            Paragraph(_escape(laws_str), value_style),
            "",
            "",
        ],
    ]

    tbl = Table(rows, colWidths=[28 * mm, 60 * mm, 24 * mm, 48 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("LINEBEFORE", (0, 0), (0, -1), 3, sev_accent),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                # span the laws row across 3 cells (label in col 0, value cols 1-3)
                ("SPAN", (1, 3), (3, 3)),
            ]
        )
    )
    return tbl


# ── Evidence card ──────────────────────────────────────────────────────────


def _evidence_card(ev: EvidenceItem, idx: int, is_de: bool, styles: dict):
    """Court-exhibit-style block with severity-coded left rule + tinted header."""
    c = ev.classification
    sev = c.severity if c else "low"
    sev_bg, sev_fg, sev_accent = _severity_colors(sev)
    sev_text = _severity_label(sev, is_de) if c else "—"

    # Header row: "Beweis #N · @author · platform" + severity badge
    header_left = (
        f"<b>{_l('Beweis', 'Exhibit', is_de)} #{idx}</b>"
        f"  ·  @{_escape(ev.author_username)}"
        f"  ·  {_escape(ev.platform or '—')}"
        f"  ·  {_fmt_dt(ev.captured_at, is_de)}"
    )
    sev_badge = Paragraph(
        f"<font color='{_hex(sev_fg)}'><b>{sev_text.upper()}</b></font>",
        styles["EvidenceBadge"],
    )

    header = Table(
        [[Paragraph(header_left, styles["EvidenceHead"]), sev_badge]],
        colWidths=[120 * mm, 35 * mm],
    )
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, -1), sev_bg),
                ("LINEBEFORE", (0, 0), (0, -1), 3, sev_accent),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ]
        )
    )

    inner = [header, Spacer(1, 2 * mm)]

    # Quoted content
    inner.append(Paragraph(_l("Inhalt", "Content", is_de), styles["FieldLabel"]))
    inner.append(
        Paragraph(
            f"„{_escape(ev.content_text)}“",
            styles["ContentQuote"],
        )
    )
    inner.append(Spacer(1, 2 * mm))

    # Classification line
    if c:
        cats = ", ".join(cat.value for cat in c.categories)
        inner.append(
            Paragraph(
                f"<b>{_l('Kategorien', 'Categories', is_de)}:</b> {_escape(cats)}  "
                f" ·  <b>{_l('Konfidenz', 'Confidence', is_de)}:</b> {c.confidence:.0%}",
                styles["MetaLine"],
            )
        )

        summary = c.summary_de if is_de else c.summary
        if summary:
            inner.append(Paragraph(_escape(summary), styles["Body"]))

        if c.applicable_laws:
            inner.append(Spacer(1, 1 * mm))
            inner.append(
                Paragraph(
                    _l("Anwendbare Paragraphen", "Applicable statutes", is_de),
                    styles["FieldLabel"],
                )
            )
            for law in c.applicable_laws:
                title = law.title_de if is_de else law.title
                reason = law.applies_because_de if is_de else law.applies_because
                bits = [f"<b>{_escape(law.paragraph)}</b>"]
                if title:
                    bits.append(_escape(title))
                tail = ""
                if reason:
                    tail += f" — {_escape(reason)}"
                if law.max_penalty:
                    tail += (
                        f" ({_l('Höchststrafe', 'Max penalty', is_de)}: "
                        f"{_escape(law.max_penalty)})"
                    )
                inner.append(Paragraph(" – ".join(bits) + tail, styles["LawItem"]))

    # Hash + URL footer line (mono, small, last — like a court exhibit stamp)
    inner.append(Spacer(1, 2 * mm))
    foot_lines = [f"URL: {_escape(ev.url)}"]
    if ev.archived_url:
        foot_lines.append(
            f"{_l('Archiv', 'Archive', is_de)}: {_escape(ev.archived_url)}"
        )
    foot_lines.append(f"SHA-256: {_escape(ev.content_hash)}")
    inner.append(Paragraph("<br/>".join(foot_lines), styles["MonoMeta"]))

    # Wrap in a 1-col table so the whole card has a thin border + page-break safety.
    wrapper = Table([[inner]], colWidths=[160 * mm])
    wrapper.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return KeepTogether(wrapper)


# ── AI legal assessment block ──────────────────────────────────────────────


def _ai_assessment_block(analysis: dict, is_de: bool, styles: dict) -> list:
    """Tinted, framed block — visually distinct from the victim's own complaint."""
    elems: list = []

    # Disclaimer banner
    banner_text = _l(
        "KI-GESTÜTZTE BEWERTUNG · keine Rechtsberatung · automatisch erzeugt",
        "AI-ASSISTED ASSESSMENT · not legal advice · auto-generated",
        is_de,
    )
    banner = Table(
        [[Paragraph(banner_text, styles["AIDisclaimer"])]],
        colWidths=[160 * mm],
    )
    banner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef3c7")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d97706")),
                ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor("#d97706")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elems.append(banner)
    elems.append(Spacer(1, 3 * mm))

    elems.append(
        Paragraph(
            _l(
                "KI-gestützte juristische Bewertung",
                "AI-assisted legal assessment",
                is_de,
            ),
            styles["SectionHead"],
        )
    )

    # Build inner content
    inner: list = []

    assessment = analysis.get(
        "legal_assessment_de" if is_de else "legal_assessment_en", ""
    )
    if assessment:
        inner.append(Paragraph(_escape(assessment), styles["AIBody"]))
        inner.append(Spacer(1, 3 * mm))

    risk = analysis.get("risk_assessment") or {}
    risk_value = (risk.get("escalation_risk") or "").upper()
    risk_reason = risk.get("reason_de" if is_de else "reason_en") or ""
    if risk_value:
        risk_palette_key = (risk.get("escalation_risk") or "").lower()
        # map to severity palette equivalents
        risk_map = {"low": "low", "medium": "medium", "high": "critical"}
        _, risk_fg, _ = _severity_colors(risk_map.get(risk_palette_key, "medium"))
        inner.append(
            Paragraph(
                f"<b>{_l('Eskalationsrisiko', 'Escalation risk', is_de)}:</b> "
                f"<font color='{_hex(risk_fg)}'><b>{risk_value}</b></font>"
                + (f" — {_escape(risk_reason)}" if risk_reason else ""),
                styles["AIBody"],
            )
        )
        inner.append(Spacer(1, 2 * mm))

    charges = analysis.get("strongest_charges") or []
    if charges:
        inner.append(
            Paragraph(
                f"<b>{_l('Stärkste Vorwürfe', 'Strongest charges', is_de)}</b>",
                styles["AIBody"],
            )
        )
        for ch in charges[:5]:
            para = ch.get("paragraph", "?")
            strength = (ch.get("strength") or "").lower()
            strength_color = {
                "strong": "#16a34a",
                "medium": "#d97706",
                "weak": "#94a3b8",
            }.get(strength, "#64748b")
            inner.append(
                Paragraph(
                    f"  •  <b>{_escape(para)}</b>  "
                    f"<font color='{strength_color}'>[{_escape(strength)}]</font>",
                    styles["AIBody"],
                )
            )
        inner.append(Spacer(1, 2 * mm))

    actions = analysis.get("recommended_actions") or []
    if actions:
        inner.append(
            Paragraph(
                f"<b>{_l('Empfohlene nächste Schritte', 'Recommended next steps', is_de)}</b>",
                styles["AIBody"],
            )
        )
        for act in actions[:5]:
            action_text = act.get("action_de" if is_de else "action_en", "")
            priority = act.get("priority", "")
            deadline = act.get("deadline") or ""
            deadline_str = f" · {deadline}" if deadline and deadline != "none" else ""
            inner.append(
                Paragraph(
                    f"  •  <i>{_escape(priority)}{deadline_str}</i> — "
                    f"{_escape(action_text)}",
                    styles["AIBody"],
                )
            )
        inner.append(Spacer(1, 2 * mm))

    disclaimer = analysis.get("disclaimer_de" if is_de else "disclaimer_en", "")
    if disclaimer:
        inner.append(Paragraph(_escape(disclaimer), styles["AIDisclaimerFoot"]))

    # Wrap in tinted frame
    wrapper = Table([[inner]], colWidths=[160 * mm])
    wrapper.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f3ff")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#c4b5fd")),
                ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor("#7c3aed")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elems.append(wrapper)
    return elems


# ── Footer drawing ─────────────────────────────────────────────────────────


def _draw_footer(canvas, doc_, ctx):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#94a3b8"))

    page_num = canvas.getPageNumber()
    if ctx["is_de"]:
        left = f"Generiert mit SafeVoice am {ctx['generated']}  ·  Fall {ctx['case_short']}"
        right = f"Seite {page_num}"
    else:
        left = f"Generated with SafeVoice on {ctx['generated']}  ·  Case {ctx['case_short']}"
        right = f"Page {page_num}"

    page_w = doc_.pagesize[0]
    canvas.drawString(20 * mm, 12 * mm, left)
    canvas.drawRightString(page_w - 20 * mm, 12 * mm, right)
    canvas.setStrokeColor(colors.HexColor("#e2e8f0"))
    canvas.setLineWidth(0.4)
    canvas.line(20 * mm, 15 * mm, page_w - 20 * mm, 15 * mm)
    canvas.restoreState()


# ── Styles ─────────────────────────────────────────────────────────────────


def _get_styles() -> dict:
    base = getSampleStyleSheet()
    s: dict = {}

    s["Title"] = ParagraphStyle(
        "SVTitle",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#4338ca"),
        spaceAfter=1 * mm,
    )
    s["Subtitle"] = ParagraphStyle(
        "SVSubtitle",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#64748b"),
    )
    s["ReportType"] = ParagraphStyle(
        "SVReportType",
        parent=base["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=3 * mm,
        spaceAfter=2 * mm,
    )
    s["SectionHead"] = ParagraphStyle(
        "SVSection",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=4 * mm,
        spaceAfter=2 * mm,
    )
    s["EvidenceHead"] = ParagraphStyle(
        "SVEvHead",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
    )
    s["EvidenceBadge"] = ParagraphStyle(
        "SVEvBadge",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        alignment=2,  # right
    )
    s["Body"] = ParagraphStyle(
        "SVBody",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
    )
    s["MetaLabel"] = ParagraphStyle(
        "SVMetaLabel",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b"),
    )
    s["MetaValue"] = ParagraphStyle(
        "SVMetaValue",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#0f172a"),
    )
    s["MetaLine"] = ParagraphStyle(
        "SVMetaLine",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#475569"),
        spaceAfter=1 * mm,
    )
    s["FieldLabel"] = ParagraphStyle(
        "SVFieldLabel",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#64748b"),
        spaceBefore=1 * mm,
    )
    s["ContentQuote"] = ParagraphStyle(
        "SVQuote",
        parent=base["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#0f172a"),
        leftIndent=6 * mm,
        rightIndent=6 * mm,
        backColor=colors.HexColor("#f1f5f9"),
        borderColor=colors.HexColor("#cbd5e1"),
        borderWidth=0,
        borderPadding=6,
        spaceBefore=1 * mm,
        spaceAfter=1 * mm,
    )
    s["LawItem"] = ParagraphStyle(
        "SVLaw",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155"),
        leftIndent=4 * mm,
        spaceBefore=0.5 * mm,
    )
    s["MonoMeta"] = ParagraphStyle(
        "SVMono",
        parent=base["Normal"],
        fontName="Courier",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#64748b"),
        leftIndent=0,
    )
    s["AIBody"] = ParagraphStyle(
        "SVAIBody",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#1e1b4b"),
        spaceAfter=1 * mm,
    )
    s["AIDisclaimer"] = ParagraphStyle(
        "SVAIDisc",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#92400e"),
        alignment=0,
    )
    s["AIDisclaimerFoot"] = ParagraphStyle(
        "SVAIDiscFoot",
        parent=base["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#6d28d9"),
        spaceBefore=2 * mm,
    )
    s["FooterNotice"] = ParagraphStyle(
        "SVFooterNotice",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#64748b"),
        alignment=1,
    )
    return s


# ── Helpers ────────────────────────────────────────────────────────────────


def _l(de: str, en: str, is_de: bool) -> str:
    return de if is_de else en


def _severity_label(severity, is_de: bool) -> str:
    s = _severity_key(severity)
    labels_de = {
        "low": "Niedrig",
        "medium": "Mittel",
        "high": "Hoch",
        "critical": "Kritisch",
    }
    labels_en = {
        "low": "Low",
        "medium": "Medium",
        "high": "High",
        "critical": "Critical",
    }
    return (labels_de if is_de else labels_en).get(s, s)


def _fmt_dt(dt, is_de: bool) -> str:
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    if is_de:
        return dt.strftime("%d.%m.%Y %H:%M")
    return dt.strftime("%Y-%m-%d %H:%M")


def _escape(text) -> str:
    if text is None:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _hex(c) -> str:
    """ReportLab Color → '#rrggbb' for inline <font color='...'>."""
    try:
        return "#" + "".join(
            f"{int(round(v * 255)):02x}" for v in (c.red, c.green, c.blue)
        )
    except Exception:
        return "#000000"
