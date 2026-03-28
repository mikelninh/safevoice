"""
Court export — generates a ZIP package with all evidence for legal proceedings.
Contains:
- PDF report (general + NetzDG + police)
- Evidence manifest (JSON)
- Hash verification file
- Chain of evidence verification
- Individual evidence text files
"""

import io
import json
import zipfile
from datetime import datetime, timezone

from app.models.evidence import Case
from app.services.pdf_generator import generate_pdf
from app.services.evidence import verify_hash


def generate_court_package(case: Case, lang: str = "de") -> bytes:
    """Generate a ZIP file containing all court-ready evidence."""
    buf = io.BytesIO()
    is_de = lang == "de"

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. PDF reports
        for report_type in ("general", "netzdg", "police"):
            pdf = generate_pdf(case, report_type=report_type, lang=lang)
            zf.writestr(f"reports/{report_type}_{lang}.pdf", pdf)

        # 2. Evidence manifest
        manifest = _build_manifest(case, is_de)
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False, default=str))

        # 3. Individual evidence files
        for i, ev in enumerate(case.evidence_items, 1):
            # Text content
            zf.writestr(
                f"evidence/{i:03d}_{ev.author_username}.txt",
                _evidence_text(ev, i, is_de)
            )

        # 4. Hash verification file
        hash_report = _build_hash_report(case, is_de)
        zf.writestr("verification/hash_verification.txt", hash_report)

        # 5. Chain of evidence
        chain_report = _build_chain_report(case, is_de)
        zf.writestr("verification/chain_of_evidence.txt", chain_report)

        # 6. README
        zf.writestr("README.txt", _readme(case, is_de))

    return buf.getvalue()


def _build_manifest(case: Case, is_de: bool) -> dict:
    """Build a JSON manifest of all evidence."""
    return {
        "safevoice_version": "1.0",
        "export_type": "court_evidence_package",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "case": {
            "id": case.id,
            "title": case.title,
            "created_at": case.created_at.isoformat() if hasattr(case.created_at, 'isoformat') else str(case.created_at),
            "overall_severity": case.overall_severity.value,
            "status": case.status,
            "victim_context": case.victim_context,
            "evidence_count": len(case.evidence_items),
            "pattern_count": len(case.pattern_flags),
        },
        "evidence": [
            {
                "id": ev.id,
                "url": ev.url,
                "platform": ev.platform,
                "author": ev.author_username,
                "captured_at": ev.captured_at.isoformat() if hasattr(ev.captured_at, 'isoformat') else str(ev.captured_at),
                "content_hash": ev.content_hash,
                "archived_url": ev.archived_url,
                "severity": ev.classification.severity.value if ev.classification else None,
                "categories": [c.value for c in ev.classification.categories] if ev.classification else [],
                "laws": [l.paragraph for l in ev.classification.applicable_laws] if ev.classification else [],
            }
            for ev in case.evidence_items
        ],
        "patterns": [
            {
                "type": f.type,
                "description": f.description_de if is_de else f.description,
                "severity": f.severity.value,
                "evidence_count": f.evidence_count,
            }
            for f in case.pattern_flags
        ],
    }


def _evidence_text(ev, idx: int, is_de: bool) -> str:
    """Generate a text file for a single evidence item."""
    lines = [
        f"{'BEWEIS' if is_de else 'EVIDENCE'} #{idx}",
        "=" * 40,
        "",
        f"ID: {ev.id}",
        f"URL: {ev.url}",
        f"{'Plattform' if is_de else 'Platform'}: {ev.platform}",
        f"{'Verfasser:in' if is_de else 'Author'}: @{ev.author_username}",
        f"{'Erfasst' if is_de else 'Captured'}: {ev.captured_at}",
        f"{'Prüfsumme' if is_de else 'Hash'}: {ev.content_hash}",
    ]
    if ev.archived_url:
        lines.append(f"{'Archiv' if is_de else 'Archive'}: {ev.archived_url}")
    lines.extend([
        "",
        f"{'INHALT' if is_de else 'CONTENT'}:",
        "-" * 40,
        ev.content_text,
        "-" * 40,
    ])
    if ev.classification:
        c = ev.classification
        lines.extend([
            "",
            f"{'EINORDNUNG' if is_de else 'CLASSIFICATION'}:",
            f"  {'Schweregrad' if is_de else 'Severity'}: {c.severity.value}",
            f"  {'Kategorien' if is_de else 'Categories'}: {', '.join(cat.value for cat in c.categories)}",
            f"  {'Konfidenz' if is_de else 'Confidence'}: {c.confidence:.0%}",
            f"  {'Sofortmaßnahme' if is_de else 'Immediate action'}: {'Ja' if c.requires_immediate_action else 'Nein'}" if is_de else f"  Immediate action: {'Yes' if c.requires_immediate_action else 'No'}",
            "",
            f"  {'Zusammenfassung' if is_de else 'Summary'}:",
            f"  {c.summary_de if is_de else c.summary}",
            "",
            f"  {'Gesetze' if is_de else 'Laws'}:",
        ])
        for law in c.applicable_laws:
            title = law.title_de if is_de else law.title
            lines.append(f"  - {law.paragraph}: {title}")
    return "\n".join(lines)


def _build_hash_report(case: Case, is_de: bool) -> str:
    """Build a hash verification report."""
    lines = [
        "HASH VERIFICATION REPORT" if not is_de else "PRÜFSUMMEN-VERIFIKATIONSBERICHT",
        "=" * 50,
        "",
        f"{'Fall-ID' if is_de else 'Case ID'}: {case.id}",
        f"{'Generiert' if is_de else 'Generated'}: {datetime.now(timezone.utc).isoformat()}",
        f"{'Algorithmus' if is_de else 'Algorithm'}: SHA-256",
        "",
    ]

    all_valid = True
    for i, ev in enumerate(case.evidence_items, 1):
        is_valid = verify_hash(ev.content_text, ev.content_hash)
        status = "VALID" if is_valid else "INVALID — TAMPERED"
        if not is_valid:
            all_valid = False
        lines.extend([
            f"{'Beweis' if is_de else 'Evidence'} #{i}: @{ev.author_username}",
            f"  {'Gespeichert' if is_de else 'Stored'}: {ev.content_hash}",
            f"  {'Berechnet' if is_de else 'Computed'}: sha256:{__import__('hashlib').sha256(ev.content_text.encode()).hexdigest()}",
            f"  Status: {status}",
            "",
        ])

    lines.extend([
        "=" * 50,
        f"{'GESAMTERGEBNIS' if is_de else 'OVERALL RESULT'}: {'ALL HASHES VALID — EVIDENCE INTEGRITY CONFIRMED' if all_valid else 'WARNING: INTEGRITY VIOLATION DETECTED'}",
    ])
    return "\n".join(lines)


def _build_chain_report(case: Case, is_de: bool) -> str:
    """Build a chain of evidence timeline report."""
    lines = [
        "CHAIN OF EVIDENCE" if not is_de else "BEWEISKETTE",
        "=" * 50,
        "",
        f"{'Fall' if is_de else 'Case'}: {case.id} — {case.title}",
        f"{'Schweregrad' if is_de else 'Severity'}: {case.overall_severity.value}",
        "",
    ]

    # Sort evidence by capture time
    sorted_ev = sorted(case.evidence_items, key=lambda e: str(e.captured_at))

    for i, ev in enumerate(sorted_ev, 1):
        lines.extend([
            f"[{i}] {ev.captured_at}",
            f"    @{ev.author_username} ({ev.platform})",
            f"    \"{ev.content_text[:80]}{'...' if len(ev.content_text) > 80 else ''}\"",
            f"    Hash: {ev.content_hash[:30]}...",
        ])
        if ev.classification:
            lines.append(f"    → {ev.classification.severity.value}: {', '.join(c.value for c in ev.classification.categories)}")
        lines.append("")

    if case.pattern_flags:
        lines.extend([
            "DETECTED PATTERNS:" if not is_de else "ERKANNTE MUSTER:",
            "",
        ])
        for f in case.pattern_flags:
            desc = f.description_de if is_de else f.description
            lines.append(f"  ⚑ {f.type} ({f.severity.value}): {desc}")
            lines.append("")

    return "\n".join(lines)


def _readme(case: Case, is_de: bool) -> str:
    if is_de:
        return f"""SafeVoice — Gerichtstaugliches Beweispaket
==========================================

Fall: {case.id}
Titel: {case.title}
Generiert: {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M UTC')}

Inhalt dieses Pakets:
- reports/    — PDF-Berichte (allgemein, NetzDG, Strafanzeige)
- evidence/   — Einzelne Beweisdateien mit vollständigem Inhalt
- verification/ — Hash-Verifikation und Beweiskette
- manifest.json — Strukturierte Metadaten aller Beweise

Alle Inhalte sind mit SHA-256 Prüfsummen gesichert.
Die Integrität kann über die Datei verification/hash_verification.txt überprüft werden.

Generiert von SafeVoice — Dokumentationsplattform für digitale Gewalt
https://safevoice.org
"""
    else:
        return f"""SafeVoice — Court-Ready Evidence Package
==========================================

Case: {case.id}
Title: {case.title}
Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}

Contents of this package:
- reports/    — PDF reports (general, NetzDG, police complaint)
- evidence/   — Individual evidence files with full content
- verification/ — Hash verification and chain of evidence
- manifest.json — Structured metadata of all evidence

All content is secured with SHA-256 checksums.
Integrity can be verified via verification/hash_verification.txt

Generated by SafeVoice — Digital Violence Documentation Platform
https://safevoice.org
"""
