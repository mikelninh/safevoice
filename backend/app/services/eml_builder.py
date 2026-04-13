"""
EML (RFC 5322) builder — generates a complete email file including
pre-filled body + attached evidence (PDF, hash-chain CSV).

Why EML instead of server-side SMTP:
- User owns the send action (no spoofing, no third-party mail risk)
- No SMTP credentials, no Postmark bill, no DSGVO sub-processor
- Browser downloads `.eml` → double-click opens Apple Mail / Outlook /
  Thunderbird with EVERYTHING pre-filled: recipient, subject, body,
  AND attachments (unlike mailto: which only sets text)
- Gmail web-only users fall back to mailto (still better than nothing)

Limitation: Gmail web doesn't open .eml natively. Desktop mail clients
(Apple Mail, Outlook desktop, Thunderbird) work great.
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

from app.database import Case, Org

logger = logging.getLogger(__name__)


def build_hash_chain_csv(case: Case) -> bytes:
    """
    Human-verifiable hash chain as CSV. A police officer can open this in
    Excel, hand-verify each SHA-256 with the `shasum` tool against the
    original evidence content, and confirm the chain is unbroken.

    Columns: index, evidence_id, timestamp_utc, content_hash, previous_hash
    """
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["#", "evidence_id", "timestamp_utc", "content_hash", "previous_hash"])
    for i, ev in enumerate(case.evidence_items, start=1):
        writer.writerow([
            i,
            ev.id,
            ev.timestamp_utc.isoformat() if ev.timestamp_utc else "",
            ev.content_hash or "",
            ev.hash_chain_previous or "",
        ])
    return buf.getvalue().encode("utf-8")


def build_eml(
    *,
    case: Case,
    org: Org | None,
    recipient_email: str,
    subject: str,
    body: str,
    victim_email: str | None,
    victim_name: str | None,
    pdf_bytes: bytes,
    pdf_filename: str = "safevoice-bericht.pdf",
) -> bytes:
    """
    Assemble a complete .eml file. Returns raw RFC 5322 bytes.

    - `body` should be the victim-personalized report text
    - `pdf_bytes` should already be the legal PDF (with embedded screenshots)
    - attaches hash_chain.csv for independent verification
    """
    msg = EmailMessage()

    # Headers
    if victim_email and victim_name:
        msg["From"] = f'"{victim_name}" <{victim_email}>'
    elif victim_email:
        msg["From"] = victim_email
    # Note: we do NOT invent a From address — if the victim didn't provide
    # one, leave it blank; the mail client will fill it from their account.

    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=False)
    msg["Message-ID"] = make_msgid(domain="safevoice.app")
    # Helpful header for police triage (X- is the RFC-appropriate prefix)
    msg["X-SafeVoice-Case-ID"] = case.id
    msg["X-SafeVoice-Generated-At"] = datetime.now(timezone.utc).isoformat()
    msg["X-SafeVoice-Evidence-Count"] = str(len(case.evidence_items))
    if org:
        msg["X-SafeVoice-Organization"] = org.slug

    # Plain-text body (most police/StA mail systems prefer plain over HTML)
    msg.set_content(body)

    # Attach the legal PDF (contains embedded screenshots, hash chain,
    # classifications — self-contained dossier)
    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=pdf_filename,
    )

    # Attach the hash chain CSV for independent, tool-free verification
    msg.add_attachment(
        build_hash_chain_csv(case),
        maintype="text",
        subtype="csv",
        filename=f"hash-chain-{case.id[:8]}.csv",
    )

    return bytes(msg)
