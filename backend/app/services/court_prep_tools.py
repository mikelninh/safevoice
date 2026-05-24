"""
Tools for the Court-Prep Agent.

Each tool is a small, pure-ish function that reads case state, performs a
well-defined transformation, and returns JSON-serialisable output. The agent
loop wires these via `ToolDef` and invokes them in whatever order the model
chooses; the model only has access to the surface described in the schemas.

Side effects are limited to:
  - `re_archive_urls`: hits archive.org (idempotent at the archive's end)
  - `generate_strafanzeige_pdf`: builds bytes in memory (no DB write)
  - `draft_netzdg_email`: builds bytes in memory (no DB write)
No tool sends mail, posts to police, or modifies the case.
"""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.database import Case as DBCase, EvidenceItem as DBEvidence


# ── Reference data ──────────────────────────────────────────────────────


# Zuständige Staatsanwaltschaft nach Bundesland.
# Quelle: justiz.de + jeweilige LJM-Webseiten, Stand 2026-05-19.
# Adressen sind die zentrale Anlaufstelle; je nach Tatortgericht kann
# innerhalb des Bundeslands eine andere StA örtlich zuständig sein.
# Für eine MVP-Lösung reicht die Bundesland-Ebene — die Anwält:in/StA-Pforte
# routet ggf. intern weiter (Lebensrealität, nicht Bug).
_STA_BY_BUNDESLAND: dict[str, dict[str, str]] = {
    "BE": {
        "name": "Staatsanwaltschaft Berlin",
        "address": "Turmstraße 91, 10559 Berlin",
        "email": "poststelle@sta.berlin.de",
    },
    "BW": {
        "name": "Generalstaatsanwaltschaft Stuttgart",
        "address": "Olgastraße 2, 70182 Stuttgart",
        "email": "poststelle@gensta-stuttgart.justiz.bwl.de",
    },
    "BY": {
        "name": "Staatsanwaltschaft München I",
        "address": "Linprunstraße 25, 80335 München",
        "email": "poststelle@sta-m1.bayern.de",
    },
    "BB": {
        "name": "Staatsanwaltschaft Potsdam",
        "address": "Jägerallee 10-12, 14469 Potsdam",
        "email": "poststelle@sta-potsdam.brandenburg.de",
    },
    "HB": {
        "name": "Staatsanwaltschaft Bremen",
        "address": "Domsheide 16, 28195 Bremen",
        "email": "office@staatsanwaltschaft.bremen.de",
    },
    "HH": {
        "name": "Staatsanwaltschaft Hamburg",
        "address": "Gorch-Fock-Wall 15, 20354 Hamburg",
        "email": "poststelle@sta.justiz.hamburg.de",
    },
    "HE": {
        "name": "Staatsanwaltschaft Frankfurt am Main",
        "address": "Konrad-Adenauer-Straße 20, 60313 Frankfurt am Main",
        "email": "poststelle@sta-frankfurt.justiz.hessen.de",
    },
    "MV": {
        "name": "Staatsanwaltschaft Rostock",
        "address": "Friedrich-Engels-Platz 1, 18055 Rostock",
        "email": "poststelle@sta-hro.mv-justiz.de",
    },
    "NI": {
        "name": "Staatsanwaltschaft Hannover",
        "address": "Volgersweg 65, 30175 Hannover",
        "email": "poststelle@stahan.niedersachsen.de",
    },
    "NW": {
        "name": "Staatsanwaltschaft Köln",
        "address": "Luxemburger Straße 101, 50939 Köln",
        "email": "poststelle@sta-koeln.nrw.de",
    },
    "RP": {
        "name": "Staatsanwaltschaft Mainz",
        "address": "Ernst-Ludwig-Straße 5, 55116 Mainz",
        "email": "poststelle@stamz.mjv.rlp.de",
    },
    "SL": {
        "name": "Staatsanwaltschaft Saarbrücken",
        "address": "Zähringerstraße 12, 66119 Saarbrücken",
        "email": "poststelle@sta-sb.justiz.saarland.de",
    },
    "SN": {
        "name": "Staatsanwaltschaft Dresden",
        "address": "Lothringer Straße 1, 01069 Dresden",
        "email": "poststelle@sta-dd.justiz.sachsen.de",
    },
    "ST": {
        "name": "Staatsanwaltschaft Magdeburg",
        "address": "Halberstädter Straße 8, 39112 Magdeburg",
        "email": "poststelle@sta-md.justiz.sachsen-anhalt.de",
    },
    "SH": {
        "name": "Staatsanwaltschaft Kiel",
        "address": "Harmsstraße 96, 24114 Kiel",
        "email": "poststelle@stakiel.landsh.de",
    },
    "TH": {
        "name": "Staatsanwaltschaft Erfurt",
        "address": "Rudolfstraße 46, 99092 Erfurt",
        "email": "poststelle@staef.thueringen.de",
    },
}


# § 77b StGB — Antragsdelikte. Maps `code:section` → frist_months.
# Only "relative Antragsdelikte" (3-Monats-Frist ab Kenntnis) listed.
# Absolute Antragsdelikte (z. B. § 247) sind hier irrelevant für SafeVoice.
_ANTRAGSDELIKTE_MONTHS: dict[str, int] = {
    "stgb:185": 3,  # Beleidigung
    "stgb:186": 3,  # Üble Nachrede
    "stgb:201a": 3,  # Verletzung des höchstpersönlichen Lebensbereichs
    "stgb:238": 3,  # Nachstellung — Offizialdelikt, aber Strafantrag empfohlen
}


# Plattformen sortiert nach „URL-Verschwinde-Wahrscheinlichkeit".
# TikTok-Posts werden am häufigsten gelöscht → höchste Re-Archivierungs-
# Priorität. X/Twitter ist mittel; Reddit am stabilsten.
_ARCHIVE_PRIORITY = {
    "tiktok": 5,
    "instagram": 4,
    "facebook": 4,
    "twitter": 3,
    "x": 3,
    "youtube": 2,
    "reddit": 1,
    "web": 1,
    "unknown": 1,
}


# Each Bundesland has its own Onlinewache (24/7 digital police front desk).
# Court-Prep generates a paste-ready text + the right URL so the user can
# file the Strafanzeige through this official digital channel directly,
# instead of mailing a paper letter to the Staatsanwaltschaft.
_ONLINEWACHE_URLS: dict[str, dict[str, str]] = {
    "BW": {"name": "Baden-Württemberg", "url": "https://www.polizei-bw.de/onlinewache"},
    "BY": {"name": "Bayern", "url": "https://www.polizei.bayern.de/onlinewache"},
    "BE": {"name": "Berlin", "url": "https://www.internetwache-polizei-berlin.de"},
    "BB": {
        "name": "Brandenburg",
        "url": "https://polizei.brandenburg.de/onlineanzeige",
    },
    "HB": {"name": "Bremen", "url": "https://www.polizei.bremen.de/onlinewache"},
    "HH": {"name": "Hamburg", "url": "https://www.polizei.hamburg/onlinewache"},
    "HE": {"name": "Hessen", "url": "https://onlinewache.polizei.hessen.de"},
    "MV": {
        "name": "Mecklenburg-Vorpommern",
        "url": "https://www.polizei.mvnet.de/Onlineanzeige",
    },
    "NI": {
        "name": "Niedersachsen",
        "url": "https://www.onlinewache.polizei.niedersachsen.de",
    },
    "NW": {"name": "Nordrhein-Westfalen", "url": "https://polizei.nrw/internetwache"},
    "RP": {"name": "Rheinland-Pfalz", "url": "https://www.polizei.rlp.de/onlinewache"},
    "SL": {"name": "Saarland", "url": "https://www.polizei.saarland.de/onlinewache"},
    "SN": {"name": "Sachsen", "url": "https://www.polizei.sachsen.de/onlinewache"},
    "ST": {
        "name": "Sachsen-Anhalt",
        "url": "https://www.polizei.sachsen-anhalt.de/onlinewache",
    },
    "SH": {
        "name": "Schleswig-Holstein",
        "url": "https://www.schleswig-holstein.de/onlinewache",
    },
    "TH": {
        "name": "Thüringen",
        "url": "https://www.thueringen.de/th3/polizei/onlinewache",
    },
}


# NetzDG-Meldekontakte je Plattform.
# Real-world: die Plattformen haben Web-Formulare, nicht offene Email-
# Adressen. Wir generieren ein .eml-File für Outlook/Mail, damit die
# Anwält:in den Inhalt 1:1 in das jeweilige Formular kopieren kann.
_NETZDG_RECIPIENTS: dict[str, str] = {
    "instagram": "netzdg@meta.com",
    "facebook": "netzdg@meta.com",
    "tiktok": "netzdg@tiktok.com",
    "twitter": "netzdg@x.com",
    "x": "netzdg@x.com",
    "youtube": "netzdg@google.com",
}


# ── Tool 1: read_case ───────────────────────────────────────────────────


READ_CASE_SCHEMA = {
    "type": "object",
    "properties": {
        "case_id": {"type": "string", "description": "The case UUID to load."}
    },
    "required": ["case_id"],
    "additionalProperties": False,
}


def make_read_case(db: Session):
    def handler(args: dict) -> Any:
        case_id = args["case_id"]
        case = db.query(DBCase).filter_by(id=case_id).first()
        if not case:
            return {"error": f"case '{case_id}' not found"}

        evidence = []
        _seen_ev: set[tuple] = set()
        for ev in case.evidence_items:
            # Defensive dedup: collapse exact-duplicate evidence rows (same text,
            # type, source) so the agent + PDF never list the same incident twice.
            # The upstream double-insert is a separate TODO.
            _key = ((ev.raw_content or "").strip(), ev.content_type, ev.source_url)
            if _key in _seen_ev:
                continue
            _seen_ev.add(_key)
            cls = ev.classification
            evidence.append(
                {
                    "id": ev.id,
                    "content_type": ev.content_type,
                    "platform": ev.platform or "unknown",
                    "source_url": ev.source_url,
                    "archived_url": ev.archived_url,
                    "timestamp_utc": (
                        ev.timestamp_utc.isoformat() if ev.timestamp_utc else None
                    ),
                    "content_text": (ev.raw_content or "")[:500],
                    "content_hash": ev.content_hash,
                    "classification": (
                        {
                            "severity": cls.severity,
                            # Use category IDs (stable enum-like keys), not
                            # display names — downstream tools match on IDs
                            # like 'doxxing', not on 'Doxxing (publication…)'.
                            "categories": [c.id for c in cls.categories],
                            "laws": [f"{l.code}:{l.section}" for l in cls.laws],
                            "summary_de": cls.summary_de,
                        }
                        if cls
                        else None
                    ),
                }
            )

        return {
            "case_id": case.id,
            "title": case.title,
            "status": case.status,
            "overall_severity": case.overall_severity,
            "created_at": case.created_at.isoformat() if case.created_at else None,
            "evidence_count": len(evidence),
            "evidence": evidence,
        }

    return handler


# ── Tool 2: determine_jurisdiction ──────────────────────────────────────


DETERMINE_JURISDICTION_SCHEMA = {
    "type": "object",
    "properties": {
        "bundesland_code": {
            "type": "string",
            "description": (
                "ISO 3166-2 code of the Bundesland where the victim lives "
                "(BE, BW, BY, BB, HB, HH, HE, MV, NI, NW, RP, SL, SN, ST, SH, TH)."
            ),
        }
    },
    "required": ["bundesland_code"],
    "additionalProperties": False,
}


def determine_jurisdiction(args: dict) -> Any:
    code = (args.get("bundesland_code") or "").upper().strip()
    sta = _STA_BY_BUNDESLAND.get(code)
    if not sta:
        return {
            "error": f"unknown bundesland_code '{code}'",
            "available": sorted(_STA_BY_BUNDESLAND.keys()),
        }
    return {
        "bundesland_code": code,
        "staatsanwaltschaft": sta,
        "rechtsgrundlage": "§ 7 StPO (Gerichtsstand des Wohnsitzes)",
    }


# ── Tool 3: check_strafantrag_frist ─────────────────────────────────────


CHECK_FRIST_SCHEMA = {
    "type": "object",
    "properties": {
        "earliest_evidence_iso": {
            "type": "string",
            "description": (
                "ISO 8601 timestamp of the earliest evidence in the case "
                "(taken as the date of first Kenntnisnahme by the victim)."
            ),
        },
        "applicable_laws": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                "List of statute codes in 'code:section' format, e.g. "
                "['stgb:185', 'stgb:241']. Determines which "
                "Antragsfristen apply."
            ),
        },
    },
    "required": ["earliest_evidence_iso", "applicable_laws"],
    "additionalProperties": False,
}


def check_strafantrag_frist(args: dict) -> Any:
    try:
        anchor = datetime.fromisoformat(
            args["earliest_evidence_iso"].replace("Z", "+00:00")
        )
    except Exception as e:
        return {"error": f"unparseable timestamp: {e}"}
    if anchor.tzinfo is None:
        anchor = anchor.replace(tzinfo=timezone.utc)

    laws = args.get("applicable_laws") or []
    now = datetime.now(timezone.utc)

    relevant: list[dict] = []
    for law in laws:
        months = _ANTRAGSDELIKTE_MONTHS.get(law.lower())
        if months is None:
            continue
        # § 187 BGB Fristen-Berechnung: Monatsfrist endet am gleichnamigen
        # Tag des Folgemonats; wir nähern mit 30 Tagen pro Monat an, was
        # für die Warn-Logik (Frist < 7 Tage) ausreichend ist.
        deadline = anchor + timedelta(days=30 * months)
        days_left = (deadline - now).days
        relevant.append(
            {
                "law": law,
                "frist_months": months,
                "deadline_utc": deadline.isoformat(),
                "days_left": days_left,
                "expired": days_left < 0,
                "urgent": 0 <= days_left < 7,
            }
        )

    if not relevant:
        return {
            "anchor_utc": anchor.isoformat(),
            "applicable_antragsdelikte": [],
            "summary": "Keine Antragsfristen anwendbar (Offizialdelikte oder Frist nicht relevant).",
        }

    worst_expired = any(r["expired"] for r in relevant)
    worst_urgent = any(r["urgent"] for r in relevant)
    level = "expired" if worst_expired else "urgent" if worst_urgent else "ok"

    return {
        "anchor_utc": anchor.isoformat(),
        "applicable_antragsdelikte": relevant,
        "warning_level": level,
        "summary": (
            "MINDESTENS EIN STRAFANTRAG IST BEREITS VERFRISTET — sofort prüfen."
            if worst_expired
            else "Mindestens ein Strafantrag läuft in unter 7 Tagen ab — Eilantrag empfohlen."
            if worst_urgent
            else "Alle relevanten Antragsfristen liegen in der Zukunft."
        ),
    }


# ── Tool 4: detect_anonymisierung_needed ────────────────────────────────


DETECT_ANON_SCHEMA = {
    "type": "object",
    "properties": {
        "categories": {
            "type": "array",
            "items": {"type": "string"},
            "description": "All unique categories across the case's evidence.",
        },
        "overall_severity": {
            "type": "string",
            "enum": ["none", "low", "medium", "high", "critical"],
        },
    },
    "required": ["categories", "overall_severity"],
    "additionalProperties": False,
}


def detect_anonymisierung_needed(args: dict) -> Any:
    cats = {c.lower() for c in (args.get("categories") or [])}
    severity = (args.get("overall_severity") or "none").lower()
    # Accept both the classifier's own enum names (doxxing/stalking/death_threat)
    # and the DB-mapped equivalents (cyberstalking, threat-in-doxxing-context),
    # because `read_case` returns DB-side names while a directly-passed list
    # may use classifier names. Single source of legal truth: a § 68 Abs. 2, 3 StPO
    # Antrag is justified when the Beschuldigte would gain dangerous knowledge
    # of the complainant's whereabouts.
    triggers = cats & {
        "doxxing",
        "stalking",
        "cyberstalking",
        "death_threat",
        "intimate_images",
    }
    is_high = severity in {"high", "critical"}
    needed = bool(triggers) and is_high

    return {
        "needed": needed,
        "rechtsgrundlage": (
            "§ 68 Abs. 2, 3 StPO (Anonymisierungsantrag für Anschrift der Anzeigenden)"
            if needed
            else None
        ),
        "begruendung": (
            f"Kategorien {sorted(triggers)} bei Severity '{severity}' begründen "
            "ein konkretes Schutzbedürfnis der Anzeigenden."
            if needed
            else "Severity und Kategorien begründen kein konkretes Schutzbedürfnis."
        ),
        "triggering_categories": sorted(triggers),
    }


# ── Tool 5: re_archive_urls ─────────────────────────────────────────────


RE_ARCHIVE_SCHEMA = {
    "type": "object",
    "properties": {
        "urls": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "platform": {"type": "string"},
                },
                "required": ["url", "platform"],
                "additionalProperties": False,
            },
            "description": (
                "List of {url, platform} pairs to re-archive. Caller should "
                "pass URLs from evidence that lack an archived_url, or where "
                "the existing snapshot is older than 7 days."
            ),
        }
    },
    "required": ["urls"],
    "additionalProperties": False,
}


def re_archive_urls(args: dict) -> Any:
    from app.services.evidence import archive_url_sync

    items = args.get("urls") or []
    # Sortierung nach Verschwinde-Risiko — TikTok/IG zuerst, weil dort der
    # Inhalt am ehesten gelöscht wird, bevor wir nochmal hingucken.
    items_sorted = sorted(
        items,
        key=lambda i: _ARCHIVE_PRIORITY.get(
            (i.get("platform") or "unknown").lower(), 0
        ),
        reverse=True,
    )

    results = []
    for it in items_sorted[:25]:  # hard cap so an agent loop can't bomb us
        url = it.get("url") or ""
        if not url:
            results.append({"url": url, "ok": False, "error": "empty url"})
            continue
        try:
            archived = archive_url_sync(url)
            results.append(
                {
                    "url": url,
                    "platform": it.get("platform"),
                    "ok": bool(archived),
                    "archived_url": archived,
                }
            )
        except Exception as e:
            results.append(
                {
                    "url": url,
                    "platform": it.get("platform"),
                    "ok": False,
                    "error": str(e),
                }
            )

    return {
        "attempted": len(results),
        "succeeded": sum(1 for r in results if r["ok"]),
        "results": results,
    }


# ── Tool 6: draft_netzdg_email ──────────────────────────────────────────


DRAFT_NETZDG_SCHEMA = {
    "type": "object",
    "properties": {
        "case_id": {"type": "string"},
        "platform": {
            "type": "string",
            "description": "Platform key — instagram, facebook, tiktok, twitter, x, youtube.",
        },
        "victim_name": {"type": "string"},
        "victim_email": {"type": "string"},
    },
    "required": ["case_id", "platform"],
    "additionalProperties": False,
}


def make_draft_netzdg_email(db: Session):
    def handler(args: dict) -> Any:
        from app.services.db_helpers import case_to_pydantic
        from app.services.eml_builder import build_eml
        from app.services.pdf_generator import generate_pdf
        from app.services.report_generator import generate_report

        case_id = args["case_id"]
        platform = (args.get("platform") or "").lower()
        recipient = _NETZDG_RECIPIENTS.get(platform)
        if not recipient:
            return {
                "ok": False,
                "error": f"no NetzDG contact for platform '{platform}'",
                "supported_platforms": sorted(_NETZDG_RECIPIENTS.keys()),
            }

        case = db.query(DBCase).filter_by(id=case_id).first()
        if not case:
            return {"ok": False, "error": f"case '{case_id}' not found"}

        # Subset evidence to the requested platform — NetzDG-Meldung an Meta
        # zitiert keine X-Tweets und umgekehrt. Soft-filter: tolerant gegen
        # 'instagram' vs 'instagram.com'.
        platform_evidence = [
            ev
            for ev in case.evidence_items
            if (ev.platform or "").lower().startswith(platform)
        ]
        if not platform_evidence:
            return {
                "ok": False,
                "error": f"case has no evidence on platform '{platform}'",
            }

        pydantic_case = case_to_pydantic(case)
        report = generate_report(pydantic_case, report_type="netzdg", lang="de")
        default_body = report.get("body", "") or ""

        # Personalise body if victim data passed in.
        victim_name = args.get("victim_name")
        victim_email = args.get("victim_email")
        if victim_name:
            sender_block = victim_name
            if victim_email:
                sender_block += f"\nE-Mail: {victim_email}"
            default_body = default_body.replace("[NAME DES OPFERS]", sender_block)
            default_body = default_body.replace("[UNTERSCHRIFT]", victim_name)

        subject = report.get("subject") or f"NetzDG-Meldung — Case {case.id[:8]}"
        pdf_bytes = generate_pdf(
            case=pydantic_case,
            report_type="netzdg",
            lang="de",
            victim_name=victim_name,
            victim_email=victim_email,
        )
        eml_bytes = build_eml(
            case=case,
            org=None,
            recipient_email=recipient,
            subject=subject,
            body=default_body,
            victim_email=victim_email,
            victim_name=victim_name,
            pdf_bytes=pdf_bytes,
            pdf_filename=f"netzdg-{case.id[:8]}.pdf",
        )

        return {
            "ok": True,
            "platform": platform,
            "recipient": recipient,
            "subject": subject,
            "eml_base64": base64.b64encode(eml_bytes).decode("ascii"),
            "eml_bytes_len": len(eml_bytes),
            "evidence_count": len(platform_evidence),
        }

    return handler


# ── Tool 7: generate_strafanzeige_pdf ───────────────────────────────────


GENERATE_PDF_SCHEMA = {
    "type": "object",
    "properties": {
        "case_id": {"type": "string"},
        "victim_name": {"type": "string"},
        "victim_address": {"type": "string"},
        "victim_email": {"type": "string"},
        "victim_phone": {"type": "string"},
        "relationship": {
            "type": "string",
            "enum": ["self", "guardian", "caretaker"],
            "description": (
                "Relationship of the person filing to the victim. "
                "'self' = victim files themselves (default). "
                "'guardian' = legal guardian for a minor (Eltern für Kind, § 77 III StGB). "
                "'caretaker' = filing on behalf of another adult with their authorisation."
            ),
        },
        "represented_name": {
            "type": "string",
            "description": "Name of the represented person — only used when relationship != 'self'.",
        },
    },
    "required": ["case_id"],
    "additionalProperties": False,
}


def make_generate_strafanzeige_pdf(db: Session):
    def handler(args: dict) -> Any:
        from app.services.db_helpers import case_to_pydantic
        from app.services.pdf_generator import generate_pdf

        case = db.query(DBCase).filter_by(id=args["case_id"]).first()
        if not case:
            return {"ok": False, "error": f"case '{args['case_id']}' not found"}

        # pdf_generator expects the Pydantic Case (with requires_immediate_action,
        # categories enum etc.), not the SQLAlchemy row. Same conversion as
        # reports.py uses.
        pydantic_case = case_to_pydantic(case)
        pdf_bytes = generate_pdf(
            case=pydantic_case,
            report_type="police",
            lang="de",
            victim_name=args.get("victim_name"),
            victim_address=args.get("victim_address"),
            victim_phone=args.get("victim_phone"),
            victim_email=args.get("victim_email"),
            relationship=args.get("relationship") or "self",
            represented_name=args.get("represented_name"),
        )
        return {
            "ok": True,
            "case_id": case.id,
            "pdf_base64": base64.b64encode(pdf_bytes).decode("ascii"),
            "pdf_bytes_len": len(pdf_bytes),
            "filename": f"strafanzeige-{case.id[:8]}.pdf",
        }

    return handler


# ── Tool 8: build_onlinewache_text ──────────────────────────────────────


ONLINEWACHE_SCHEMA = {
    "type": "object",
    "properties": {
        "case_id": {"type": "string"},
        "bundesland_code": {
            "type": "string",
            "description": (
                "ISO 3166-2 code of the victim's Bundesland — selects the right "
                "Onlinewache URL."
            ),
        },
        "victim_name": {"type": "string"},
        "victim_address": {"type": "string"},
        "victim_email": {"type": "string"},
        "victim_phone": {"type": "string"},
    },
    "required": ["case_id", "bundesland_code"],
    "additionalProperties": False,
}


def make_build_onlinewache_text(db: Session):
    def handler(args: dict) -> Any:
        from app.services.db_helpers import case_to_pydantic
        from app.services.report_generator import generate_report

        case_id = args["case_id"]
        code = (args.get("bundesland_code") or "").upper()
        onlinewache = _ONLINEWACHE_URLS.get(code)
        if not onlinewache:
            return {
                "ok": False,
                "error": f"unknown bundesland_code '{code}'",
                "available": sorted(_ONLINEWACHE_URLS.keys()),
            }

        case = db.query(DBCase).filter_by(id=case_id).first()
        if not case:
            return {"ok": False, "error": f"case '{case_id}' not found"}

        pydantic_case = case_to_pydantic(case)
        report = generate_report(pydantic_case, report_type="police", lang="de")
        body = report.get("body", "") or ""

        victim_name = args.get("victim_name")
        if victim_name:
            sender_block_parts = [victim_name]
            if args.get("victim_address"):
                sender_block_parts.append(args["victim_address"])
            if args.get("victim_phone"):
                sender_block_parts.append(f"Tel: {args['victim_phone']}")
            if args.get("victim_email"):
                sender_block_parts.append(f"E-Mail: {args['victim_email']}")
            sender_block = "\n".join(sender_block_parts)
            body = body.replace("[NAME DES OPFERS]", sender_block)
            body = body.replace("[UNTERSCHRIFT]", victim_name)

        return {
            "ok": True,
            "bundesland_code": code,
            "bundesland_name": onlinewache["name"],
            "onlinewache_url": onlinewache["url"],
            "text_for_paste": body,
            "instructions_de": (
                f"1. Klick auf 'Onlinewache {onlinewache['name']} öffnen' — Tab geht auf.\n"
                "2. Im Formular zuerst deine Daten als Anzeigeerstatter:in eintragen.\n"
                "3. Den oben kopierten Text in das 'Sachverhalt'-Feld einfügen (Cmd/Ctrl+V).\n"
                "4. Absenden — du bekommst per Email eine Eingangsbestätigung."
            ),
        }

    return handler


# ── Tool registry ───────────────────────────────────────────────────────


def build_tools(db: Session):
    """Wire the tool defs to a request-scoped DB session."""
    from app.services.agent_loop import ToolDef

    return [
        ToolDef(
            name="read_case",
            description=(
                "Load a SafeVoice case with all its evidence and classifications "
                "from the database. Always call this FIRST so subsequent tools "
                "have grounded inputs."
            ),
            schema=READ_CASE_SCHEMA,
            handler=make_read_case(db),
        ),
        ToolDef(
            name="determine_jurisdiction",
            description=(
                "Resolve the competent Staatsanwaltschaft for the victim's "
                "Bundesland (§ 7 StPO). Returns name, postal address, and "
                "official poststelle email."
            ),
            schema=DETERMINE_JURISDICTION_SCHEMA,
            handler=determine_jurisdiction,
        ),
        ToolDef(
            name="check_strafantrag_frist",
            description=(
                "For relative Antragsdelikte (§§ 185, 186, 201a StGB), compute "
                "how many days are left in the 3-month Strafantragsfrist "
                "(§ 77b StGB), counted from the earliest evidence's Kenntnis-"
                "date. Returns expired/urgent/ok per statute."
            ),
            schema=CHECK_FRIST_SCHEMA,
            handler=check_strafantrag_frist,
        ),
        ToolDef(
            name="detect_anonymisierung_needed",
            description=(
                "Decide whether the case warrants a § 68 Abs. 2, 3 StPO Anonymisierungs-"
                "antrag (victim's address withheld from the Beschuldigten). "
                "True for doxxing/stalking/death_threat/intimate_images at "
                "severity ≥ high."
            ),
            schema=DETECT_ANON_SCHEMA,
            handler=detect_anonymisierung_needed,
        ),
        ToolDef(
            name="re_archive_urls",
            description=(
                "Push selected evidence URLs to archive.org so that platform-"
                "side deletions don't destroy the evidence. Prioritises "
                "high-deletion-risk platforms (TikTok > IG > X) automatically."
            ),
            schema=RE_ARCHIVE_SCHEMA,
            handler=re_archive_urls,
        ),
        ToolDef(
            name="draft_netzdg_email",
            description=(
                "Build a ready-to-send .eml file (RFC 5322) for a NetzDG "
                "Meldung to one platform. Only includes evidence from that "
                "platform. Returns base64-encoded eml bytes — caller stores or "
                "downloads, never auto-sends."
            ),
            schema=DRAFT_NETZDG_SCHEMA,
            handler=make_draft_netzdg_email(db),
        ),
        ToolDef(
            name="generate_strafanzeige_pdf",
            description=(
                "Render the final court-ready Strafanzeige PDF (A4) with "
                "executive summary, numbered exhibits, hash chain footer and "
                "AI assessment block. Returns base64-encoded PDF bytes."
            ),
            schema=GENERATE_PDF_SCHEMA,
            handler=make_generate_strafanzeige_pdf(db),
        ),
        ToolDef(
            name="build_onlinewache_text",
            description=(
                "Prepare the paste-ready text + the Bundesland-specific "
                "Onlinewache URL for filing the Strafanzeige through Germany's "
                "official 24/7 digital police channel. Only call this when the "
                "user provided a bundesland_code. Returns text + URL + step-by-"
                "step instructions in German."
            ),
            schema=ONLINEWACHE_SCHEMA,
            handler=make_build_onlinewache_text(db),
        ),
    ]
