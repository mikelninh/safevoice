"""
Authoritative-statute lookup — Phase 1 of the cross-project RAG layer.

Reads German law markdown files from the GitLaw corpus
(`/Users/mikel/gitlaw/laws/*.md`, ~5,936 laws), extracts the full text of a
specific paragraph (e.g. "§ 241 StGB"), and returns it as a structured
LawText so the case-level Legal-AI prompt can ground its analysis in
actual current statutory text instead of model-recall.

Design:
- Local file read for v1. Switch to GitLaw HTTP API in Phase 2 when GitLaw deploys separately.
- Caching: in-process LRU on the citation string so we don't re-parse the same law file across calls in one request.
- Failure mode: returns None on any error (file missing, paragraph not found, parse error). Caller falls back to model knowledge — never breaks the analysis.

The law file format (verified against gitlaw/laws/stgb.md):
    # <law name>
    **Abkürzung:** <abbreviation>
    **Stand:** <last update info>
    ---
    ...
    ### § <number> — <paragraph name>
    <paragraph text, possibly multiple paragraphs (1)(2)...>
    ### § <next number> — <next paragraph name>
    ...
"""

from __future__ import annotations

import os
import re
import hashlib
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

# Default location of the GitLaw corpus. Override via env var when paths differ.
GITLAW_LAWS_DIR = Path(os.environ.get("GITLAW_LAWS_DIR", "/Users/mikel/gitlaw/laws"))


@dataclass
class LawText:
    """Authoritative paragraph text fetched from the GitLaw corpus."""
    paragraph: str           # canonical citation, e.g. "§ 241 StGB"
    title: str               # paragraph heading, e.g. "Bedrohung"
    full_text: str           # the actual statutory text (multiple Absätze concatenated)
    law_name: str            # "Strafgesetzbuch"
    law_abbr: str            # "StGB"
    source_path: str         # absolute path to the law file (for provenance)
    last_updated: str        # the "**Stand:**" line from the file, if present
    text_sha256: str         # hash of full_text — pin a case_analysis to a specific revision


# Regex to capture e.g. "§ 241 StGB", "§ 241a StGB", "§ 130 StGB", "NetzDG § 3"
_CITATION_PATTERNS = [
    re.compile(r"^§\s*(\d+[a-z]?)\s+([A-Za-z]+)$"),         # "§ 241 StGB"
    re.compile(r"^([A-Za-z]+)\s*§\s*(\d+[a-z]?)$"),         # "NetzDG § 3"
]


def _parse_citation(citation: str) -> tuple[str, str] | None:
    """Parse a citation string → (law_abbr_lowercase, paragraph_number).
    Returns None if the format is unrecognised."""
    s = citation.strip()
    for pat in _CITATION_PATTERNS:
        m = pat.match(s)
        if not m:
            continue
        groups = m.groups()
        # First pattern: (number, abbr) → we want (abbr, number)
        if pat is _CITATION_PATTERNS[0]:
            return groups[1].lower(), groups[0]
        # Second: (abbr, number) already
        return groups[0].lower(), groups[1]
    return None


def _law_file_path(law_abbr: str) -> Path | None:
    """GitLaw stores each law as `<lowercase abbreviation>.md`. Return the path
    if it exists, else None."""
    candidate = GITLAW_LAWS_DIR / f"{law_abbr}.md"
    return candidate if candidate.exists() else None


_HEADING_RE = re.compile(r"^###\s*§\s*([\dA-Za-z]+)\s*[—–-]?\s*(.*)$", re.MULTILINE)


def _extract_paragraph(content: str, paragraph_number: str) -> tuple[str, str] | None:
    """Find the heading `### § N — Name` and return (title, body) where body
    runs until the next `### ` heading. None if not found."""
    target = paragraph_number.lower()
    matches = list(_HEADING_RE.finditer(content))
    for i, m in enumerate(matches):
        if m.group(1).lower() != target:
            continue
        title = m.group(2).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[body_start:body_end].strip()
        return title, body
    return None


def _extract_law_meta(content: str) -> tuple[str, str, str]:
    """Pull the law's full name, abbreviation, and 'Stand' line from the front matter."""
    name = ""
    abbr = ""
    stand = ""
    for line in content.split("\n", 30):  # check the first 30 lines
        s = line.strip()
        if not name and s.startswith("# "):
            name = s[2:].strip()
        elif s.startswith("**Abkürzung:**"):
            abbr = s.replace("**Abkürzung:**", "").strip()
        elif s.startswith("**Stand:**"):
            stand = s.replace("**Stand:**", "").strip().rstrip(";")
    return name, abbr, stand


@lru_cache(maxsize=256)
def get_law_text(citation: str) -> LawText | None:
    """Fetch the authoritative text of a paragraph by its citation string.

    Examples that work:
      get_law_text("§ 241 StGB")
      get_law_text("§ 185 StGB")
      get_law_text("NetzDG § 3")  # returns None today — NetzDG isn't in the
                                  # main StGB corpus shape; falls back gracefully

    Returns None on any failure. Caller (legal_ai.py) treats None as "no
    authoritative source available" and falls back to model knowledge.
    """
    parsed = _parse_citation(citation)
    if parsed is None:
        logger.debug("law_text: unrecognised citation format: %r", citation)
        return None
    law_abbr, paragraph_number = parsed

    path = _law_file_path(law_abbr)
    if path is None:
        logger.debug("law_text: no file for law %r (looked for %s.md)", law_abbr, law_abbr)
        return None

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning("law_text: failed reading %s: %s", path, e)
        return None

    extracted = _extract_paragraph(content, paragraph_number)
    if extracted is None:
        logger.debug("law_text: paragraph %r not found in %s", paragraph_number, path)
        return None
    title, body = extracted

    law_name, law_abbr_real, stand = _extract_law_meta(content)
    text_sha = hashlib.sha256(body.encode("utf-8")).hexdigest()

    return LawText(
        paragraph=citation.strip(),
        title=title,
        full_text=body,
        law_name=law_name,
        law_abbr=law_abbr_real or law_abbr.upper(),
        source_path=str(path),
        last_updated=stand,
        text_sha256=text_sha,
    )


def format_authoritative_block(law_texts: list[LawText]) -> str:
    """Render a list of LawText objects into the authoritative-source prompt block."""
    if not law_texts:
        return ""
    parts = ["AUTHORITATIVE STATUTE TEXTS (from the GitLaw corpus — German Federal law repository).",
             "Ground your legal assessment in these exact texts. Do not invent text not present below.",
             ""]
    for lt in law_texts:
        parts.append(f"=== {lt.paragraph} — {lt.title} ===")
        if lt.last_updated:
            parts.append(f"_Source: {lt.law_name} ({lt.law_abbr}) · Stand: {lt.last_updated}_")
        parts.append("")
        parts.append(lt.full_text)
        parts.append("")
    return "\n".join(parts)
