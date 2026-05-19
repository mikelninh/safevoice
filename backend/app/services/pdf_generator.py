"""
PDF generator for court-ready evidence reports.

Design notes (aesthetic pass 2026-05-09):
- Quiet, restrained, NYT/legal-tech elegance — not corporate-saas decorative.
- Generous whitespace; the page must breathe.
- Soft, paper-friendly palette (slate/paper-grey, muted accents).
- Typography rhythm: large title, tracked-out small caps for section labels,
  body 10pt at 1.4 leading, mono for hashes/IDs.
- Backgrounds tinted at 6–10% opacity max — never bold colour blocks.
- Severity coded but desaturated; one shade darker than typical UI palette.
- ReportLab built-ins only (Helvetica + Courier + Times-Roman).
"""

import io
from datetime import datetime, timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Flowable
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


# ── Palette ────────────────────────────────────────────────────────────────
# Calm, paper-friendly. Severity colours are one shade darker than typical UI
# accents so they still read as restrained on cream-white paper.
INK = "#0f172a"  # near-black ink
INK_SOFT = "#1e293b"  # slate-800 — primary accent / titles
GREY_500 = "#64748b"
GREY_600 = "#475569"
GREY_400 = "#94a3b8"
RULE = "#cbd5e1"
RULE_SOFT = "#e2e8f0"
PAPER_TINT = "#f8fafc"  # 4% slate

_SEVERITY_PALETTE = {
    # (subtle bg ~6–8%, fg-text, dot/accent)
    "low": ("#ecfdf5", "#15803d", "#15803d"),
    "medium": ("#fef9c3", "#a16207", "#a16207"),
    "high": ("#fff1e6", "#c2410c", "#c2410c"),
    "critical": ("#fef2f2", "#b91c1c", "#b91c1c"),
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
        _severity_key(sev), ("#f1f5f9", GREY_600, GREY_500)
    )
    return colors.HexColor(bg), colors.HexColor(fg), colors.HexColor(accent)


# ── Tracked-out small caps helper ──────────────────────────────────────────
def _tracked(text: str) -> str:
    """Render text as tracked-out caps using thin spaces between letters.
    ReportLab has no letter-spacing, so we approximate with U+2009 thin space."""
    out = []
    for word in text.split(" "):
        out.append(" ".join(word.upper()))
    return "  ".join(out)  # double-space between words


# ── Public entry point ────────────────────────────────────────────────────
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
        leftMargin=28 * mm,
        rightMargin=24 * mm,
        topMargin=24 * mm,
        bottomMargin=24 * mm,
        title=f"SafeVoice · {case.id[:8]}",
        author="SafeVoice",
    )

    styles = _get_styles()
    is_de = lang == "de"
    elements: list = []
    now = datetime.now(timezone.utc)

    # ── 1. Masthead ────────────────────────────────────────────────────────
    type_labels = {
        "general": ("Beweissicherungsbericht", "Evidence Documentation Report"),
        "netzdg": ("NetzDG-Meldung", "NetzDG Report"),
        "police": ("Strafanzeige", "Criminal Complaint"),
    }
    label_de, label_en = type_labels.get(report_type, type_labels["general"])

    # Subtitle differs by report_type. For a Strafanzeige we drop the
    # product-tagline ("Dokumentationsplattform für digitale Gewalt"
    # reads like marketing copy on a legal document) and surface a
    # restrained, defensibility-focused line instead.
    if report_type == "police":
        subtitle_de = "Beweissicherung mit Hash-Kette · Archive.org-Sicherung"
        subtitle_en = "Evidence chain with SHA-256 hashes · Archive.org snapshots"
    elif report_type == "netzdg":
        subtitle_de = "Plattform-Meldung nach Netzwerkdurchsetzungsgesetz"
        subtitle_en = "Platform takedown notice under NetzDG"
    else:
        subtitle_de = "Dokumentationsplattform für digitale Gewalt"
        subtitle_en = "Digital Violence Documentation Platform"

    # Two-column masthead: title left, case-id mono top-right
    masthead = Table(
        [
            [
                [
                    Paragraph("SafeVoice", styles["Title"]),
                    Paragraph(label_de if is_de else label_en, styles["ReportType"]),
                    Paragraph(
                        subtitle_de if is_de else subtitle_en,
                        styles["Subtitle"],
                    ),
                ],
                [
                    Paragraph(
                        _tracked(_l("Fall", "Case", is_de)), styles["MetaCapsRight"]
                    ),
                    Paragraph(case.id[:8], styles["CaseIdMono"]),
                    Paragraph(
                        _fmt_dt(now, is_de, with_time=False),
                        styles["MetaRightSmall"],
                    ),
                ],
            ]
        ],
        colWidths=[110 * mm, 48 * mm],
    )
    masthead.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    elements.append(masthead)
    elements.append(Spacer(1, 6 * mm))
    elements.append(
        HRFlowable(width="100%", thickness=0.6, color=colors.HexColor(INK_SOFT))
    )
    elements.append(Spacer(1, 8 * mm))

    # ── 2. One-line meta strip ─────────────────────────────────────────────
    # Replaces the previous heavy "executive summary" card which duplicated
    # everything the formal body says again. A Strafanzeige is a letter,
    # not a dashboard — keep the metadata as a single restrained line.
    elements.append(_meta_strip(case, is_de, styles, now))
    elements.append(Spacer(1, 10 * mm))

    # ── 3. Strafanzeige body (formal complaint) ────────────────────────────
    # Render for every police report — even without victim_name (placeholders
    # remain so the document still reads as a Strafanzeige, not as an
    # internal report). This is what police/StA expect; a Strafanzeige
    # without the formal "Hiermit erstatte ich…" wording is not recognisable
    # as one.
    if report_type == "police":
        from app.services.report_generator import _police_body  # local: avoid cycle

        elements.append(
            _section_label(
                _l("Förmliche Strafanzeige", "Formal Criminal Complaint", is_de), styles
            )
        )
        elements.append(Spacer(1, 5 * mm))

        # Sender block right-aligned at top of letter — render even without
        # a name; the placeholders make it obvious where to write by hand.
        sender_lines = [
            f"<b>{_escape(victim_name) if victim_name else _l('[Name der Anzeigeerstatterin]', '[Complainant name]', is_de)}</b>"
        ]
        if victim_address:
            sender_lines.append(_escape(victim_address))
        else:
            sender_lines.append(
                f"<font color='{GREY_400}'>"
                + _l("[Straße, PLZ, Ort]", "[Street, ZIP, City]", is_de)
                + "</font>"
            )
        if victim_phone:
            sender_lines.append(f"Tel.: {_escape(victim_phone)}")
        if victim_email:
            sender_lines.append(_escape(victim_email))
        sender_html = "<br/>".join(sender_lines)
        elements.append(Paragraph(sender_html, styles["SenderRight"]))
        elements.append(Spacer(1, 4 * mm))
        elements.append(
            Paragraph(
                _fmt_dt(datetime.now(), is_de, with_time=False),
                styles["DateRight"],
            )
        )
        elements.append(Spacer(1, 6 * mm))

        # Subject line
        subject = _l(
            "Strafanzeige wegen digitaler Belästigung, Bedrohung und übler Nachrede",
            "Criminal complaint regarding digital harassment, threats and defamation",
            is_de,
        )
        elements.append(
            Paragraph(
                f"<font color='{GREY_600}'>{_l('Betreff', 'Subject', is_de)}:</font>"
                f"&nbsp;&nbsp;{_escape(subject)}",
                styles["Subject"],
            )
        )
        elements.append(Spacer(1, 6 * mm))

        body = _police_body(case, list(case.evidence_items), is_de=is_de)
        # Personalise where we have data, leave placeholders visible where we
        # don't. A blank "[NAME DES OPFERS]" in the printed PDF is the right
        # signal: it tells the user / officer where to handwrite.
        if victim_name:
            body = body.replace("[NAME DES OPFERS]", victim_name)
            body = body.replace("[VICTIM NAME]", victim_name)
        # The [UNTERSCHRIFT] / [SIGNATURE] tokens we render as a proper
        # signature line below — strip them out of the body so they don't
        # appear as literal text.
        body = body.replace("[UNTERSCHRIFT]", "").replace("[SIGNATURE]", "")

        # Strip the redundant "STRAFANZEIGE" header + sender line + date line
        # from the inline body since we render them properly above.
        skip_prefixes = (
            "STRAFANZEIGE",
            "CRIMINAL COMPLAINT",
            "Anzeigeerstatterin",
            "Complainant:",
            "Datum:",
            "Date:",
        )
        cleaned = []
        for paragraph in body.split("\n\n"):
            stripped = paragraph.strip()
            if not stripped:
                continue
            if any(stripped.startswith(p) for p in skip_prefixes):
                continue
            cleaned.append(paragraph)

        for paragraph in cleaned:
            html = _escape(paragraph).replace("\n", "<br/>")
            elements.append(Paragraph(html, styles["Body"]))
            elements.append(Spacer(1, 2 * mm))

        # Signature line. A printed underscore-rule + name underneath is the
        # convention on a formal German Strafanzeige; reads as "sign here".
        elements.append(Spacer(1, 12 * mm))
        sig_name = victim_name or _l(
            "[Name der Anzeigeerstatterin]", "[Complainant name]", is_de
        )
        sig_table = Table(
            [
                [
                    HRFlowable(
                        width=60 * mm, thickness=0.6, color=colors.HexColor(INK_SOFT)
                    ),
                ],
                [
                    Paragraph(
                        f"<font color='{GREY_500}'>{_escape(sig_name)}"
                        f"&nbsp;&nbsp;·&nbsp;&nbsp;{_l('Datum', 'Date', is_de)}: "
                        f"{_fmt_dt(datetime.now(), is_de, with_time=False)}</font>",
                        styles["MetaLine"],
                    )
                ],
            ],
            colWidths=[60 * mm],
        )
        sig_table.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        elements.append(sig_table)
        elements.append(Spacer(1, 10 * mm))
        elements.append(
            HRFlowable(width="35%", thickness=0.4, color=colors.HexColor(RULE))
        )
        elements.append(Spacer(1, 8 * mm))

    # ── 4. Victim context ──────────────────────────────────────────────────
    if case.victim_context:
        elements.append(_section_label(_l("Kontext", "Victim Context", is_de), styles))
        elements.append(Spacer(1, 3 * mm))
        elements.append(Paragraph(_escape(case.victim_context), styles["Body"]))
        elements.append(Spacer(1, 8 * mm))

    # ── 5. Pattern flags ───────────────────────────────────────────────────
    if case.pattern_flags:
        elements.append(
            _section_label(_l("Erkannte Muster", "Detected Patterns", is_de), styles)
        )
        elements.append(Spacer(1, 3 * mm))
        for flag in case.pattern_flags:
            desc = flag.description_de if is_de else flag.description
            elements.append(
                Paragraph(
                    f"<b>{_escape(flag.type)}</b> "
                    f"<font color='{GREY_500}'>· {_severity_label(flag.severity, is_de)}</font><br/>"
                    f"{_escape(desc)}",
                    styles["Body"],
                )
            )
            elements.append(Spacer(1, 2 * mm))
        elements.append(Spacer(1, 6 * mm))

    # ── 6. Evidence list — exhibit pages ───────────────────────────────────
    elements.append(
        _section_label(
            _l("Beweismittel", "Evidence", is_de) + f"  ·  {len(case.evidence_items)}",
            styles,
        )
    )
    elements.append(Spacer(1, 5 * mm))

    for i, ev in enumerate(case.evidence_items, 1):
        elements.append(_evidence_card(ev, i, is_de, styles))
        if i < len(case.evidence_items):
            elements.append(Spacer(1, 7 * mm))

    elements.append(Spacer(1, 8 * mm))

    # ── 7. AI legal assessment (police only) ───────────────────────────────
    if report_type == "police":
        try:
            from app.services.legal_ai import analyze_case_legally

            analysis = analyze_case_legally(case)
            if analysis is not None:
                elements.extend(_ai_assessment_block(analysis, is_de, styles))
                elements.append(Spacer(1, 8 * mm))
        except Exception:
            import logging

            logging.getLogger(__name__).exception("Failed to embed legal AI in PDF")

    # ── 8. Closing legal notice ────────────────────────────────────────────
    elements.append(
        HRFlowable(width="100%", thickness=0.4, color=colors.HexColor(RULE))
    )
    elements.append(Spacer(1, 4 * mm))
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
        _draw_fold_mark(canvas, doc_)

    doc.build(elements, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()


# ── Section label ─────────────────────────────────────────────────────────
def _section_label(text: str, styles: dict):
    """Plain bold label — was previously tracked-out caps. After review:
    tracked-out caps used 15+ times in a single document is design-tic
    noise, not a functional signal. Keep them only for the single major
    page-internal divider (the BEWEISMITTEL header below)."""
    return Paragraph(text, styles["SectionLabel"])


# ── Executive summary — letterhead style ──────────────────────────────────
def _executive_summary(
    case: Case, victim_name, is_de: bool, styles: dict, now
) -> Table:
    """Two clean columns under a thin top rule.
    Left: complainant block. Right: case meta. Severity as soft pill."""
    sev_bg, sev_fg, sev_accent = _severity_colors(case.overall_severity)
    sev_text = _severity_label(case.overall_severity, is_de)

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
    laws_str = "  ·  ".join(seen_laws) if seen_laws else "—"

    cap = styles["MetaCaps"]
    val = styles["MetaValue"]

    # Severity pill (soft, rounded — uses borderPadding + backColor)
    pill_style = ParagraphStyle(
        "SevPill",
        parent=styles["Body"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=sev_fg,
        backColor=sev_bg,
        borderPadding=(3, 7, 3, 7),
        alignment=0,
    )
    pill = Paragraph(_tracked(sev_text), pill_style)

    left_col = [
        Paragraph(_tracked(_l("Anzeigeerstatter:in", "Complainant", is_de)), cap),
        Spacer(1, 1.5 * mm),
        Paragraph(
            f"<b>{_escape(victim_name) if victim_name else '—'}</b>",
            styles["BodyLarge"],
        ),
        Spacer(1, 4 * mm),
        Paragraph(_tracked(_l("Vorfälle", "Incidents", is_de)), cap),
        Spacer(1, 1.5 * mm),
        Paragraph(
            f"<b>{len(case.evidence_items)}</b>"
            + (
                f"  <font color='{GREY_500}' size='9'>· "
                f"{crit_count} {_l('kritisch', 'critical', is_de)}</font>"
                if crit_count
                else ""
            ),
            styles["BodyLarge"],
        ),
    ]

    right_col = [
        Paragraph(_tracked(_l("Schweregrad", "Severity", is_de)), cap),
        Spacer(1, 1.5 * mm),
        pill,
        Spacer(1, 4 * mm),
        Paragraph(_tracked(_l("Erstellt", "Created", is_de)), cap),
        Spacer(1, 1.5 * mm),
        Paragraph(_fmt_dt(case.created_at, is_de), val),
    ]

    body = Table([[left_col, right_col]], colWidths=[80 * mm, 78 * mm])
    body.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    laws_block = [
        Spacer(1, 5 * mm),
        Paragraph(
            _tracked(_l("Einschlägige Paragraphen", "Statutes invoked", is_de)), cap
        ),
        Spacer(1, 1.5 * mm),
        Paragraph(_escape(laws_str), val),
    ]

    # Wrap the whole thing with thin top + bottom rules
    inner = [
        HRFlowable(width="100%", thickness=0.4, color=colors.HexColor(INK_SOFT)),
        Spacer(1, 5 * mm),
        body,
        *laws_block,
        Spacer(1, 5 * mm),
        HRFlowable(width="100%", thickness=0.3, color=colors.HexColor(RULE)),
    ]

    wrap = Table([[inner]], colWidths=[158 * mm])
    wrap.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return wrap


# ── Meta strip — replaces the heavy executive summary ────────────────────
def _meta_strip(case: Case, is_de: bool, styles: dict, now) -> Paragraph:
    """One-line meta strip: severity pill + incident count + case-id + date.

    Replaces the old letterhead-style executive-summary table that took
    half of page 1 to repeat what the formal body says anyway. The
    Strafanzeige itself is the document; the meta strip is a quiet
    contextual line, not a dashboard."""
    sev_bg, sev_fg, _ = _severity_colors(case.overall_severity)
    sev_text = _severity_label(case.overall_severity, is_de)

    n = len(case.evidence_items)
    crit_count = sum(
        1
        for ev in case.evidence_items
        if ev.classification and ev.classification.requires_immediate_action
    )
    incidents_label = f"{n} {_l('Vorfall', 'incident', is_de) if n == 1 else _l('Vorfälle', 'incidents', is_de)}"
    if crit_count:
        incidents_label += f", {crit_count} {_l('kritisch', 'critical', is_de)}"

    case_id = (case.id or "—")[:8]
    date_str = _fmt_dt(now, is_de, with_time=False)

    # Inline severity pill as styled span (Paragraph supports <font> + bg via
    # styled spans only via separate ParagraphStyle, so we render a soft
    # coloured dot + label instead of a true pill — same visual weight,
    # simpler markup).
    sev_dot = (
        f"<font color='{_hex(sev_fg)}'>●</font> "
        f"<font color='{_hex(sev_fg)}'><b>{_escape(sev_text)}</b></font>"
    )

    line = (
        f"{sev_dot}"
        f"  <font color='{GREY_400}'>·</font>  "
        f"<font color='{INK}'>{incidents_label}</font>"
        f"  <font color='{GREY_400}'>·</font>  "
        f"<font color='{GREY_500}'>{_l('Fall', 'Case', is_de)}</font> "
        f"<font name='Courier' color='{INK}'>{case_id}</font>"
        f"  <font color='{GREY_400}'>·</font>  "
        f"<font color='{GREY_500}'>{date_str}</font>"
    )

    return Paragraph(line, styles["MetaStrip"])


# ── Evidence card — exhibit page ──────────────────────────────────────────
def _evidence_card(ev: EvidenceItem, idx: int, is_de: bool, styles: dict):
    """Thin top rule, large numeral on the left, content flowing beneath.
    Severity dot in colour next to the date; quote with thin left rule."""
    c = ev.classification
    sev = c.severity if c else "low"
    _, sev_fg, sev_accent = _severity_colors(sev)
    sev_text = _severity_label(sev, is_de) if c else "—"

    # Top rule
    top_rule = HRFlowable(width="100%", thickness=0.3, color=colors.HexColor(RULE))

    # Numeral (left) + meta (right)
    num_style = styles["ExhibitNumber"]
    meta_style = styles["EvidenceMeta"]
    sev_dot = (
        f"<font color='{_hex(sev_accent)}'>•</font> "
        f"<font color='{_hex(sev_fg)}'><b>{_escape(sev_text.upper())}</b></font>"
    )
    head = Table(
        [
            [
                Paragraph(f"{idx:02d}", num_style),
                [
                    Paragraph(
                        # Tolerant rendering for missing fields — "@unknown ·
                        # unknown" looks like a bug; a labelled placeholder
                        # ("Verfasser:in unbekannt") reads as honest absence.
                        _format_author(ev.author_username, is_de)
                        + f"  ·  {_format_platform(ev.platform, is_de)}"
                        + f"  ·  {_fmt_dt(ev.captured_at, is_de)}"
                        + f"  &nbsp;&nbsp;{sev_dot}",
                        meta_style,
                    ),
                ],
            ]
        ],
        colWidths=[14 * mm, 144 * mm],
    )
    head.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    # Content quote — italic with thin left rule (no backplate)
    quote_para = Paragraph(
        f"„{_escape(ev.content_text)}"
        + ("”" if not is_de else "“"),  # closing German quote
        styles["ContentQuote"],
    )
    # Use a 1-col table to draw a thin left rule next to the quote
    quote_block = Table([[quote_para]], colWidths=[144 * mm])
    quote_block.setStyle(
        TableStyle(
            [
                ("LINEBEFORE", (0, 0), (0, -1), 0.8, colors.HexColor(RULE)),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )
    # Indent the quote under the numeral
    quote_indent = Table([["", quote_block]], colWidths=[14 * mm, 144 * mm])
    quote_indent.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    inner = [top_rule, Spacer(1, 3 * mm), head, Spacer(1, 3 * mm), quote_indent]

    # Body text (categories + summary + laws) — indented under numeral
    body_inner: list = []
    if c:
        cats = ", ".join(cat.value for cat in c.categories)
        body_inner.append(
            Paragraph(
                f"<font color='{GREY_500}'>{_l('Kategorien', 'Categories', is_de)}:</font>"
                f"&nbsp;{_escape(cats)}"
                f"&nbsp;&nbsp;<font color='{GREY_400}'>·</font>&nbsp;&nbsp;"
                f"<font color='{GREY_500}'>{_l('Konfidenz', 'Confidence', is_de)}:</font>"
                f"&nbsp;{c.confidence:.0%}",
                styles["MetaLine"],
            )
        )

        summary = c.summary_de if is_de else c.summary
        if summary:
            body_inner.append(Spacer(1, 2 * mm))
            body_inner.append(Paragraph(_escape(summary), styles["Body"]))

        if c.applicable_laws:
            body_inner.append(Spacer(1, 3 * mm))
            body_inner.append(
                Paragraph(
                    _l("Anwendbare Paragraphen", "Applicable statutes", is_de),
                    styles["FieldLabel"],
                )
            )
            body_inner.append(Spacer(1, 1.5 * mm))
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
                        f" <font color='{GREY_500}'>("
                        f"{_l('Höchststrafe', 'Max penalty', is_de)}: "
                        f"{_escape(law.max_penalty)})</font>"
                    )
                body_inner.append(Paragraph(" — ".join(bits) + tail, styles["LawItem"]))

    # Hash + URL footer line (mono)
    body_inner.append(Spacer(1, 3 * mm))
    foot_lines = [f"<font color='{GREY_500}'>URL</font>&nbsp;&nbsp;{_escape(ev.url)}"]
    if ev.archived_url:
        foot_lines.append(
            f"<font color='{GREY_500}'>{_l('ARCHIV', 'ARCHIVE', is_de)}</font>"
            f"&nbsp;&nbsp;{_escape(ev.archived_url)}"
        )
    foot_lines.append(
        # Strip a redundant "sha256:" prefix on the stored hash so the label
        # reads cleanly ("SHA-256  abc123…") instead of "SHA-256  sha256:abc…".
        f"<font color='{GREY_500}'>SHA-256</font>&nbsp;&nbsp;{_escape(_clean_hash(ev.content_hash))}"
    )
    body_inner.append(Paragraph("<br/>".join(foot_lines), styles["MonoMeta"]))

    body_indent = Table([["", body_inner]], colWidths=[14 * mm, 144 * mm])
    body_indent.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    inner.append(Spacer(1, 3 * mm))
    inner.append(body_indent)

    wrapper = Table([[inner]], colWidths=[158 * mm])
    wrapper.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return KeepTogether(wrapper)


# ── AI legal assessment block ─────────────────────────────────────────────
def _ai_assessment_block(analysis: dict, is_de: bool, styles: dict) -> list:
    """No coloured backplate. Thin top rule + tracked-out label + italic
    subtitle. The disclaimer is the visual signal, not a tinted block."""
    elems: list = []

    elems.append(
        HRFlowable(width="100%", thickness=0.3, color=colors.HexColor(INK_SOFT))
    )
    elems.append(Spacer(1, 3 * mm))

    elems.append(
        Paragraph(
            _l(
                "Maschinelle Einordnung · nicht bindend",
                "Machine-generated assessment · non-binding",
                is_de,
            ),
            styles["SectionLabel"],
        )
    )
    elems.append(Spacer(1, 2 * mm))
    elems.append(
        Paragraph(
            _l(
                "Diese Einordnung wurde maschinell erstellt und ersetzt keine Rechtsberatung.",
                "This assessment was generated by a model and does not replace legal advice.",
                is_de,
            ),
            styles["AISubtitle"],
        )
    )
    elems.append(Spacer(1, 5 * mm))

    assessment = analysis.get(
        "legal_assessment_de" if is_de else "legal_assessment_en", ""
    )
    if assessment:
        elems.append(Paragraph(_escape(assessment), styles["Body"]))
        elems.append(Spacer(1, 4 * mm))

    risk = analysis.get("risk_assessment") or {}
    risk_value = (risk.get("escalation_risk") or "").upper()
    risk_reason = risk.get("reason_de" if is_de else "reason_en") or ""
    if risk_value:
        risk_palette_key = (risk.get("escalation_risk") or "").lower()
        risk_map = {"low": "low", "medium": "medium", "high": "critical"}
        _, risk_fg, _ = _severity_colors(risk_map.get(risk_palette_key, "medium"))
        elems.append(
            Paragraph(
                f"<font color='{GREY_500}'>"
                f"{_l('Eskalationsrisiko', 'Escalation risk', is_de)}:"
                f"</font>&nbsp;"
                f"<font color='{_hex(risk_fg)}'><b>{risk_value}</b></font>"
                + (f" — {_escape(risk_reason)}" if risk_reason else ""),
                styles["Body"],
            )
        )
        elems.append(Spacer(1, 3 * mm))

    charges = analysis.get("strongest_charges") or []
    if charges:
        elems.append(
            Paragraph(
                _l("Stärkste Vorwürfe", "Strongest charges", is_de),
                styles["FieldLabel"],
            )
        )
        elems.append(Spacer(1, 1.5 * mm))
        for ch in charges[:5]:
            para = ch.get("paragraph", "?")
            strength = (ch.get("strength") or "").lower()
            strength_color = {
                "strong": "#15803d",
                "medium": "#a16207",
                "weak": GREY_400,
            }.get(strength, GREY_500)
            elems.append(
                Paragraph(
                    f"<b>{_escape(para)}</b>"
                    f"&nbsp;&nbsp;<font color='{strength_color}'>· {_escape(strength)}</font>",
                    styles["Body"],
                )
            )
        elems.append(Spacer(1, 3 * mm))

    actions = analysis.get("recommended_actions") or []
    if actions:
        elems.append(
            Paragraph(
                _l("Empfohlene nächste Schritte", "Recommended next steps", is_de),
                styles["FieldLabel"],
            )
        )
        elems.append(Spacer(1, 1.5 * mm))
        for act in actions[:5]:
            action_text = act.get("action_de" if is_de else "action_en", "")
            priority = act.get("priority", "")
            deadline = act.get("deadline") or ""
            deadline_str = f" · {deadline}" if deadline and deadline != "none" else ""
            elems.append(
                Paragraph(
                    f"<font color='{GREY_500}'><i>{_escape(priority)}{deadline_str}</i></font>"
                    f" — {_escape(action_text)}",
                    styles["Body"],
                )
            )
            elems.append(Spacer(1, 1 * mm))
        elems.append(Spacer(1, 2 * mm))

    disclaimer = analysis.get("disclaimer_de" if is_de else "disclaimer_en", "")
    if disclaimer:
        elems.append(Spacer(1, 2 * mm))
        elems.append(Paragraph(_escape(disclaimer), styles["AISubtitle"]))

    return elems


# ── Footer + fold mark ────────────────────────────────────────────────────
def _draw_footer(canvas, doc_, ctx):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor(GREY_500))

    page_num = canvas.getPageNumber()
    page_w, page_h = doc_.pagesize
    total = getattr(doc_, "page", page_num)  # ReportLab tracks current

    # Quieter footer. Previous version stacked SafeVoice + safevoice.app +
    # Erstellt-Datum + Fall — four data points with three separators on a
    # legal document the recipient doesn't care which tool made it. Keep
    # only what helps: case-id (so the StA can refer back) + page number.
    if ctx["is_de"]:
        left = f"Fall {ctx['case_short']}"
    else:
        left = f"Case {ctx['case_short']}"
    right = f"{page_num}"

    # thin rule above footer
    canvas.setStrokeColor(colors.HexColor(RULE_SOFT))
    canvas.setLineWidth(0.3)
    canvas.line(24 * mm, 16 * mm, page_w - 24 * mm, 16 * mm)

    canvas.drawString(24 * mm, 12 * mm, left)
    canvas.drawRightString(page_w - 24 * mm, 12 * mm, right)
    canvas.restoreState()


def _draw_fold_mark(canvas, doc_):
    """Subtle fold mark at 1/3 from the top (DIN-lang envelope fold).
    Tiny tick on the left margin only — no rule across the page."""
    canvas.saveState()
    page_w, page_h = doc_.pagesize
    fold_y = page_h - (page_h / 3.0)
    canvas.setStrokeColor(colors.HexColor(GREY_400))
    canvas.setLineWidth(0.3)
    canvas.line(8 * mm, fold_y, 12 * mm, fold_y)
    canvas.setFont("Helvetica", 5.5)
    canvas.setFillColor(colors.HexColor(GREY_400))
    canvas.drawString(13 * mm, fold_y - 1.6, "✂")  # scissors glyph
    canvas.restoreState()


# ── Styles ────────────────────────────────────────────────────────────────
def _get_styles() -> dict:
    base = getSampleStyleSheet()
    s: dict = {}

    s["Title"] = ParagraphStyle(
        "SVTitle",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=27,
        leading=30,
        textColor=colors.HexColor(INK_SOFT),
        spaceAfter=1 * mm,
        alignment=0,
    )
    s["Subtitle"] = ParagraphStyle(
        "SVSubtitle",
        parent=base["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor(GREY_500),
        spaceBefore=2 * mm,
    )
    s["ReportType"] = ParagraphStyle(
        "SVReportType",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor(GREY_600),
        spaceBefore=1 * mm,
    )
    s["MetaCapsRight"] = ParagraphStyle(
        "SVMetaCapsRight",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor(GREY_600),
        alignment=2,
    )
    s["MetaRightSmall"] = ParagraphStyle(
        "SVMetaRightSmall",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor(GREY_500),
        alignment=2,
        spaceBefore=2 * mm,
    )
    s["CaseIdMono"] = ParagraphStyle(
        "SVCaseId",
        parent=base["Normal"],
        fontName="Courier-Bold",
        fontSize=14,
        leading=17,
        textColor=colors.HexColor(INK),
        alignment=2,
        spaceBefore=1 * mm,
    )
    s["SectionLabel"] = ParagraphStyle(
        "SVSectionLabel",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor(GREY_600),
    )
    s["MetaStrip"] = ParagraphStyle(
        "SVMetaStrip",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor(INK),
        alignment=0,
    )
    s["FormHint"] = ParagraphStyle(
        "SVFormHint",
        parent=base["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor(GREY_500),
        alignment=2,
    )
    s["Body"] = ParagraphStyle(
        "SVBody",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor(INK),
        spaceAfter=2 * mm,
    )
    s["BodyLarge"] = ParagraphStyle(
        "SVBodyLarge",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor(INK),
    )
    s["MetaCaps"] = ParagraphStyle(
        "SVMetaCaps",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor(GREY_600),
    )
    s["MetaValue"] = ParagraphStyle(
        "SVMetaValue",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor(INK),
    )
    s["MetaLine"] = ParagraphStyle(
        "SVMetaLine",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor(GREY_600),
    )
    s["FieldLabel"] = ParagraphStyle(
        "SVFieldLabel",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor(GREY_600),
    )
    s["EvidenceMeta"] = ParagraphStyle(
        "SVEvMeta",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor(GREY_600),
    )
    s["ExhibitNumber"] = ParagraphStyle(
        "SVExNum",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=18,
        leading=20,
        textColor=colors.HexColor(GREY_400),
        alignment=0,
    )
    s["ContentQuote"] = ParagraphStyle(
        "SVQuote",
        parent=base["Normal"],
        fontName="Times-Italic",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor(INK),
    )
    s["LawItem"] = ParagraphStyle(
        "SVLaw",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor(INK_SOFT),
        spaceAfter=1 * mm,
    )
    s["MonoMeta"] = ParagraphStyle(
        "SVMono",
        parent=base["Normal"],
        fontName="Courier",
        fontSize=7,
        leading=10,
        textColor=colors.HexColor(GREY_600),
    )
    s["AISubtitle"] = ParagraphStyle(
        "SVAISub",
        parent=base["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor(GREY_500),
    )
    s["FooterNotice"] = ParagraphStyle(
        "SVFooterNotice",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor(GREY_500),
        alignment=0,
    )
    s["SenderRight"] = ParagraphStyle(
        "SVSender",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor(GREY_600),
        alignment=2,
    )
    s["DateRight"] = ParagraphStyle(
        "SVDate",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor(GREY_600),
        alignment=2,
    )
    s["Subject"] = ParagraphStyle(
        "SVSubject",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor(INK),
    )
    return s


# ── Helpers ───────────────────────────────────────────────────────────────
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


def _fmt_dt(dt, is_de: bool, with_time: bool = True) -> str:
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    if is_de:
        return dt.strftime("%d.%m.%Y %H:%M") if with_time else dt.strftime("%d.%m.%Y")
    return dt.strftime("%Y-%m-%d %H:%M") if with_time else dt.strftime("%Y-%m-%d")


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


def _format_author(handle: str | None, is_de: bool) -> str:
    """Render evidence's author handle for the exhibit card.

    "@unknown" reads as a bug. A labelled placeholder ("Verfasser:in
    unbekannt") reads as an honest absence — important when this PDF goes
    to a Staatsanwaltschaft and every visual ambiguity costs trust.
    """
    handle = (handle or "").strip()
    if not handle or handle.lower() in {"unknown", "anonymous", "—", "-", "anonym"}:
        return (
            f"<font color='{GREY_500}'><i>"
            + _l("Verfasser:in unbekannt", "Author unknown", is_de)
            + "</i></font>"
        )
    return f"@{_escape(handle)}"


def _format_platform(platform: str | None, is_de: bool) -> str:
    p = (platform or "").strip()
    if not p or p.lower() in {"unknown", "—", "-"}:
        return (
            f"<font color='{GREY_500}'><i>"
            + _l("Plattform unbekannt", "Platform unknown", is_de)
            + "</i></font>"
        )
    return _escape(p)


def _clean_hash(h: str | None) -> str:
    """Strip a redundant 'sha256:' prefix so the PDF reads
    'SHA-256  abc123…' instead of 'SHA-256  sha256:abc123…'."""
    if not h:
        return ""
    s = str(h)
    for prefix in ("sha256:", "SHA-256:", "sha-256:"):
        if s.lower().startswith(prefix.lower()):
            return s[len(prefix) :]
    return s
