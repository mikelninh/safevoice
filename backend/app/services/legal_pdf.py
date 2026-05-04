"""
Legal-grade PDF exporter — NGO-ready reports.

Extends the existing pdf_generator.py with:
  - Org letterhead (logo + text header) from org.settings.letterhead_*
  - Chain-of-custody appendix (hash chain visualization)
  - Digital signature placeholder (for future integration with Adobe / DocuSign)
  - Auftragsverarbeitungs-relevant metadata footer

For use by NGOs filing Strafanzeige / forwarding to counsel.
Each PDF includes evidence trail, classifications, and a legal disclosure.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Image,
)
from reportlab.lib.utils import ImageReader

from app.database import Case, Org, Classification, EvidenceItem
from app.services import org_service

logger = logging.getLogger(__name__)


# ── Styles ──

_STYLES = getSampleStyleSheet()

_H1 = ParagraphStyle(
    "H1", parent=_STYLES["Heading1"],
    fontSize=18, spaceAfter=12, textColor=colors.HexColor("#1a1a1a"),
)
_H2 = ParagraphStyle(
    "H2", parent=_STYLES["Heading2"],
    fontSize=13, spaceAfter=8, textColor=colors.HexColor("#333333"),
)
_H3 = ParagraphStyle(
    "H3", parent=_STYLES["Heading3"],
    fontSize=11, spaceAfter=6, textColor=colors.HexColor("#555555"),
)
_BODY = ParagraphStyle(
    "Body", parent=_STYLES["BodyText"],
    fontSize=9.5, leading=13, alignment=TA_JUSTIFY, spaceAfter=6,
)
_SMALL = ParagraphStyle(
    "Small", parent=_STYLES["BodyText"],
    fontSize=8, leading=10, textColor=colors.grey,
)
_LETTERHEAD_TEXT = ParagraphStyle(
    "Letterhead", parent=_STYLES["BodyText"],
    fontSize=10, leading=12, alignment=TA_LEFT,
    textColor=colors.HexColor("#000000"),
)
_DISCLAIMER = ParagraphStyle(
    "Disclaimer", parent=_STYLES["BodyText"],
    fontSize=8, leading=10, textColor=colors.grey, alignment=TA_JUSTIFY,
    backColor=colors.HexColor("#f5f5f5"), borderPadding=6, borderWidth=0,
)


# ── Builders ──

def _letterhead_block(org: Org | None) -> list:
    """Top-of-document letterhead. Falls back to minimal branding if no org."""
    elements = []
    if org:
        settings = org_service.get_org_settings(org)
        letterhead_text = settings.get("letterhead_text", org.display_name)
        contact = org.contact_email or ""

        header_rows = [[Paragraph(f"<b>{letterhead_text}</b>", _LETTERHEAD_TEXT)]]
        if contact:
            header_rows.append([Paragraph(contact, _SMALL)])

        t = Table(header_rows, colWidths=[16 * cm])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph(
            "<b>SafeVoice</b> — Digitale Gewalt Dokumentation",
            _LETTERHEAD_TEXT,
        ))
    elements.append(Spacer(1, 0.6 * cm))
    return elements


def _case_summary_block(case: Case, org: Org | None) -> list:
    """Title, case metadata, summary block."""
    elements = [
        Paragraph(f"Fall #{case.id[:8]}", _H1),
        Paragraph(f"<b>{case.title or 'Ohne Titel'}</b>", _H2),
    ]

    meta = [
        ["Status", (case.status or "open").upper()],
        ["Schwere", (case.overall_severity or "unbekannt").upper()],
        ["Erstellt am", case.created_at.strftime("%Y-%m-%d %H:%M UTC") if case.created_at else "—"],
        ["Aktualisiert am", case.updated_at.strftime("%Y-%m-%d %H:%M UTC") if case.updated_at else "—"],
        ["Beweisstücke", str(len(case.evidence_items))],
    ]
    if org:
        meta.insert(0, ["Organisation", org.display_name])

    t = Table(meta, colWidths=[4 * cm, 12 * cm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dddddd")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t)

    if case.summary_de:
        elements += [
            Spacer(1, 0.4 * cm),
            Paragraph("<b>Zusammenfassung</b>", _H3),
            Paragraph(case.summary_de, _BODY),
        ]

    return elements


def _latest_case_analysis(case: Case):
    """Return the newest persisted case analysis row if present."""
    try:
        analyses = case.case_analyses or []
        return analyses[0] if analyses else None
    except Exception:
        return None


def _legal_analysis_block(case: Case) -> list:
    """Render the second AI layer as a concrete, auditable report section."""
    row = _latest_case_analysis(case)
    if row is None:
        return []

    elements = [
        Spacer(1, 0.4 * cm),
        Paragraph("Juristische Gesamteinschaetzung", _H2),
    ]

    if row.legal_assessment_de:
        elements.append(Paragraph(row.legal_assessment_de, _BODY))

    try:
        charges = json.loads(row.strongest_charges_json or "[]")
    except json.JSONDecodeError:
        charges = []
    if charges:
        elements.append(Spacer(1, 0.2 * cm))
        elements.append(Paragraph("<b>Staerkste Vorwuerfe</b>", _H3))
        for charge in charges[:5]:
            paragraph = charge.get("paragraph", "—")
            strength = charge.get("strength", "—")
            reason_de = charge.get("reason_de", "")
            elements.append(Paragraph(
                f"<b>{paragraph}</b> ({strength})<br/>{reason_de}",
                _BODY,
            ))

    try:
        actions = json.loads(row.recommended_actions_json or "[]")
    except json.JSONDecodeError:
        actions = []
    if actions:
        elements.append(Spacer(1, 0.2 * cm))
        elements.append(Paragraph("<b>Empfohlene naechste Schritte</b>", _H3))
        for action in actions[:5]:
            priority = action.get("priority", "—")
            deadline = action.get("deadline", "—")
            action_de = action.get("action_de", "")
            elements.append(Paragraph(
                f"<b>{priority}</b> (Frist: {deadline})<br/>{action_de}",
                _BODY,
            ))

    try:
        risk = json.loads(row.risk_assessment_json or "{}")
    except json.JSONDecodeError:
        risk = {}
    if risk:
        risk_rows = [
            ["Eskalationsrisiko", str(risk.get("escalation_risk", "—")).upper()],
            ["Begruendung", risk.get("reason_de", "—")],
        ]
        t = Table(risk_rows, colWidths=[4 * cm, 12 * cm])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dddddd")),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(Spacer(1, 0.2 * cm))
        elements.append(t)

    return elements


def _extract_screenshot(ev: EvidenceItem) -> tuple[bytes, str] | None:
    """
    Return (image_bytes, mime_type) if the evidence carries an embedded
    screenshot, or None. We look in two places:
      1. metadata_json['screenshot_base64'] — data URL or raw base64
      2. raw_content starting with 'data:image/' — data URL directly
    """
    # Try metadata_json first
    if ev.metadata_json:
        try:
            meta = json.loads(ev.metadata_json)
            b64 = meta.get("screenshot_base64")
            if b64:
                return _decode_data_url(b64)
        except (json.JSONDecodeError, AttributeError):
            pass

    # Fallback: raw_content as data URL (some upload flows stash it there)
    if ev.raw_content and ev.raw_content.startswith("data:image/"):
        return _decode_data_url(ev.raw_content)

    return None


def _decode_data_url(s: str) -> tuple[bytes, str] | None:
    """Decode 'data:image/png;base64,....' or a bare base64 string."""
    m = re.match(r"^data:(image/[a-zA-Z+.-]+);base64,(.*)$", s, re.DOTALL)
    if m:
        mime, b64 = m.group(1), m.group(2)
    else:
        # Bare base64 — assume PNG
        mime, b64 = "image/png", s
    try:
        return base64.b64decode(b64, validate=False), mime
    except (ValueError, base64.binascii.Error):
        return None


def _evidence_block(ev: EvidenceItem, idx: int) -> list:
    """One evidence item — text, classification, hash, embedded screenshot if present."""
    elements = [
        Paragraph(f"Beweisstück {idx + 1}", _H3),
    ]

    meta_rows = [
        ["Typ", ev.content_type or "text"],
        ["Plattform", ev.platform or "—"],
        ["Erfasst am", ev.timestamp_utc.strftime("%Y-%m-%d %H:%M UTC") if ev.timestamp_utc else "—"],
    ]
    if ev.source_url:
        meta_rows.append(["Quell-URL", ev.source_url[:80]])
    if ev.archived_url:
        meta_rows.append(["Archive.org", ev.archived_url[:80]])
    meta_rows.append(["SHA-256", (ev.content_hash or "—")[:64]])
    if ev.hash_chain_previous:
        meta_rows.append(["Vorheriger Hash", ev.hash_chain_previous[:64]])

    t = Table(meta_rows, colWidths=[3.5 * cm, 12.5 * cm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.2 * cm))

    # Content — text body (skip if content is itself an embedded image)
    raw = ev.raw_content or ""
    if not raw.startswith("data:image/"):
        text = raw[:2000]  # cap length for PDF
        text_escaped = text.replace("<", "&lt;").replace(">", "&gt;")
        elements.append(Paragraph(f"<i>„{text_escaped}“</i>", _BODY))
        elements.append(Spacer(1, 0.2 * cm))

    # Embedded screenshot (if present in metadata_json or as data URL in raw_content)
    screenshot = _extract_screenshot(ev)
    if screenshot:
        img_bytes, mime = screenshot
        try:
            img_reader = ImageReader(BytesIO(img_bytes))
            orig_w, orig_h = img_reader.getSize()
            # Scale to max 15 cm wide, preserve aspect ratio
            max_w = 15 * cm
            max_h = 18 * cm
            ratio = min(max_w / orig_w, max_h / orig_h, 1.0)
            w = orig_w * ratio
            h = orig_h * ratio
            img_hash = hashlib.sha256(img_bytes).hexdigest()
            elements.append(Spacer(1, 0.2 * cm))
            elements.append(Paragraph(
                f"<b>Bildbeleg</b> <font size='7' color='#777777'>({mime}, "
                f"{len(img_bytes) // 1024} KB, SHA-256: {img_hash[:12]}…)</font>",
                _H3,
            ))
            elements.append(Spacer(1, 0.15 * cm))
            elements.append(Image(BytesIO(img_bytes), width=w, height=h))
            elements.append(Spacer(1, 0.3 * cm))
        except Exception as e:
            logger.warning("Could not embed screenshot in PDF: %s", e)
            elements.append(Paragraph(
                f"<i>[Screenshot liegt vor, konnte aber nicht gerendert werden: {e}]</i>",
                _SMALL,
            ))

    # Classification
    cl: Classification | None = ev.classification
    if cl:
        laws_str = ", ".join(
            f"§ {l.section} {l.code.upper()}" for l in (cl.laws or [])
        ) or "—"
        cat_str = ", ".join(c.name_de or c.name for c in (cl.categories or [])) or "—"

        class_rows = [
            ["Schwere", (cl.severity or "—").upper()],
            ["Konfidenz", f"{(cl.confidence or 0) * 100:.0f}%"],
            ["Kategorien", cat_str],
            ["Anwendbare Gesetze", laws_str],
        ]
        t = Table(class_rows, colWidths=[3.5 * cm, 12.5 * cm])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#fff8e1")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e0c966")),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.2 * cm))
        if cl.summary_de:
            elements.append(Paragraph(f"<b>Analyse:</b> {cl.summary_de}", _BODY))
        if cl.potential_consequences_de:
            elements.append(Paragraph(
                f"<b>Mögliche Konsequenzen:</b> {cl.potential_consequences_de}",
                _BODY,
            ))

    elements.append(Spacer(1, 0.4 * cm))
    return elements


def _chain_of_custody_appendix(case: Case) -> list:
    """Hash-chain visualization for evidence integrity."""
    elements = [
        PageBreak(),
        Paragraph("Anhang A: Chain of Custody", _H1),
        Paragraph(
            "Alle Beweisstücke sind durch eine kryptografische Hash-Kette (SHA-256) "
            "gesichert. Eine Manipulation eines Beweisstücks ändert seinen Hash und "
            "bricht die Kette — dies macht nachträgliche Veränderungen nachweisbar.",
            _BODY,
        ),
        Spacer(1, 0.4 * cm),
    ]

    rows = [["#", "Hash (SHA-256)", "Vorheriger Hash", "Zeitstempel"]]
    for idx, ev in enumerate(case.evidence_items):
        rows.append([
            str(idx + 1),
            (ev.content_hash or "—")[:16] + "...",
            (ev.hash_chain_previous or "—")[:16] + ("..." if ev.hash_chain_previous else ""),
            ev.timestamp_utc.strftime("%Y-%m-%d %H:%M") if ev.timestamp_utc else "—",
        ])

    t = Table(rows, colWidths=[1 * cm, 5.5 * cm, 5.5 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(t)
    return elements


def _disclaimer_block(org: Org | None) -> list:
    """Legal disclaimer block. Critical: this is NOT legal advice."""
    if org:
        settings = org_service.get_org_settings(org)
        signature_url = settings.get("signature_url")
    else:
        signature_url = None

    elements = [
        PageBreak(),
        Paragraph("Anhang B: Rechtliche Hinweise", _H1),
        Paragraph(
            "Dieses Dokument wurde mithilfe der SafeVoice-Plattform erstellt. Die "
            "enthaltenen Klassifizierungen basieren auf KI-Analyse (OpenAI GPT-4o-mini, "
            "Temperatur 0, strukturierte Ausgabe gemäß Schema-Validierung). Sie stellen "
            "eine <b>juristische Einschätzung, keine verbindliche Rechtsberatung</b> dar. "
            "Für verbindliche Auskünfte wenden Sie sich an eine zugelassene Rechtsanwältin "
            "oder einen zugelassenen Rechtsanwalt, sowie bei digitaler Gewalt an Beratungsstellen "
            "wie HateAid (hateaid.org) oder den Weißen Ring.",
            _DISCLAIMER,
        ),
        Spacer(1, 0.4 * cm),
        Paragraph(
            "Die Integrität der Beweisstücke ist durch SHA-256 Hash-Ketten gesichert "
            "(Anhang A). Zusätzlich wurden — soweit möglich — Archiv-Kopien bei "
            "archive.org erstellt. Dies erlaubt Gerichten und Ermittlungsbehörden die "
            "Verifizierung der Beweisstücke auch nach nachträglicher Löschung durch "
            "Plattformen oder Täter.",
            _BODY,
        ),
        Spacer(1, 0.6 * cm),
    ]

    # Signature placeholder
    elements.append(Paragraph("Unterschrift / Stempel", _H3))
    if signature_url:
        # If org has configured a signature image URL, embed it here
        elements.append(Paragraph(f"[Signatur: {signature_url}]", _SMALL))
    else:
        elements.append(Spacer(1, 2 * cm))
        elements.append(Paragraph("_______________________________________", _SMALL))
        elements.append(Paragraph("Datum, Unterschrift", _SMALL))

    return elements


# ── Public API ──

def generate_legal_pdf(case: Case, org: Org | None = None) -> bytes:
    """
    Generate an NGO-grade legal PDF for a case.

    If `org` is provided, uses its letterhead + settings.
    Returns raw bytes suitable for HTTP response or file write.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title=f"SafeVoice Report - {case.title or case.id[:8]}",
        author=org.display_name if org else "SafeVoice",
        pageCompression=0,
    )

    story: list = []
    story += _letterhead_block(org)
    story += _case_summary_block(case, org)
    story += _legal_analysis_block(case)

    if case.evidence_items:
        story.append(PageBreak())
        story.append(Paragraph("Beweisstücke", _H1))
        for idx, ev in enumerate(case.evidence_items):
            story += _evidence_block(ev, idx)

        story += _chain_of_custody_appendix(case)

    story += _disclaimer_block(org)

    doc.build(story)
    return buf.getvalue()
