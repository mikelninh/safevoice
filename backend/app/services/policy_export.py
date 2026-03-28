"""
Phase 5: Policy Impact APIs for SafeVoice.

Provides export functions for regulatory bodies, researchers, and law enforcement:
  5.1 Evidence Standard (Bundestag)
  5.2 DSA Transparency Report (EU)
  5.3 Research Dataset (Academic)
  5.4 Digitale-Gewalt-Gesetz Submission (German Parliament)
  5.5 Europol SIENA Cross-Border Package
"""

import hashlib
import uuid
from collections import Counter
from datetime import datetime, date, timezone

from app.models.evidence import Case, Severity


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash_id(raw: str) -> str:
    """One-way SHA-256 hash for pseudonymization."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _severity_str(s: Severity) -> str:
    return s.value


# ---------------------------------------------------------------------------
# 5.1 Bundestag Evidence Standard
# ---------------------------------------------------------------------------

def generate_evidence_standard() -> dict:
    """Return the SafeVoice evidence format specification (JSON schema style)."""
    return {
        "standard_name": "SafeVoice Beweisstandardformat / Evidence Standard Format",
        "version": "1.0.0",
        "issued_by": "SafeVoice e.V.",
        "description_de": (
            "Spezifikation fuer das digitale Beweisformat, das dem Bundestag im "
            "Rahmen des Digitale-Gewalt-Gesetzes vorgeschlagen wird."
        ),
        "description_en": (
            "Specification for the digital evidence format proposed to the "
            "Bundestag under the Digital Violence Act."
        ),
        "fields": {
            "id": {
                "type": "string",
                "description": "Unique evidence item identifier (UUID or platform-specific).",
            },
            "url": {
                "type": "string",
                "format": "uri",
                "description": "Original URL of the content at time of capture.",
            },
            "platform": {
                "type": "string",
                "description": "Name of the social-media platform (e.g. instagram, x, tiktok).",
            },
            "captured_at": {
                "type": "string",
                "format": "date-time",
                "description": "ISO-8601 timestamp of when the evidence was captured.",
            },
            "content_text": {
                "type": "string",
                "description": "Plain-text content of the post, comment, or message.",
            },
            "content_hash": {
                "type": "string",
                "description": "Cryptographic hash of the content for integrity verification.",
            },
            "classification": {
                "type": "object",
                "properties": {
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Assessed severity level.",
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of offense category tags.",
                    },
                    "laws": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "paragraph": {"type": "string"},
                                "title": {"type": "string"},
                            },
                        },
                        "description": "Applicable legal provisions.",
                    },
                },
            },
        },
        "metadata": {
            "hash_algorithm": "SHA-256",
            "timestamp_format": "ISO-8601 / RFC 3339",
            "supported_countries": ["DE", "AT", "CH", "EU"],
            "schema_uri": "https://safevoice.org/schema/evidence/v1.0.0.json",
        },
    }


# ---------------------------------------------------------------------------
# 5.2 DSA Transparency Report (EU Digital Services Act Art. 16)
# ---------------------------------------------------------------------------

def generate_dsa_report(cases: list[Case], lang: str = "de") -> dict:
    """Generate an EU DSA Article 16 compliant transparency report."""

    total_evidence = sum(len(c.evidence_items) for c in cases)

    # Reports by category
    category_counter: Counter = Counter()
    for c in cases:
        for ev in c.evidence_items:
            if ev.classification:
                for cat in ev.classification.categories:
                    category_counter[cat.value] += 1

    # Reports by country (mock: all DE for now, derive from platform)
    country_counter: Counter = Counter()
    for c in cases:
        country_counter["DE"] += 1  # originating country

    # Severity breakdown
    severity_counter: Counter = Counter()
    for c in cases:
        severity_counter[c.overall_severity.value] += 1

    # Simulated platform compliance metrics
    total_reported = len(cases)
    removed_count = sum(1 for c in cases if c.status == "reported")
    removal_rate = round(removed_count / max(total_reported, 1), 2)

    methodology_de = (
        "SafeVoice erfasst und klassifiziert nutzergenerierte Meldungen digitaler "
        "Gewalt auf sozialen Plattformen. Die Klassifizierung erfolgt mittels "
        "KI-gestuetzter Analyse sowie manueller Ueberpruefung. Alle Metriken "
        "beziehen sich auf den Berichtszeitraum und werden gemaess DSA Art. 15 "
        "und Art. 24 Transparenzberichtspflichten bereitgestellt."
    )
    methodology_en = (
        "SafeVoice captures and classifies user-reported digital violence on "
        "social platforms. Classification uses AI-assisted analysis and manual "
        "review. All metrics cover the reporting period and are provided pursuant "
        "to DSA Art. 15 and Art. 24 transparency reporting obligations."
    )

    now = datetime.now(timezone.utc)

    return {
        "report_title": "DSA Art. 15/24 Transparency Report" if lang == "en" else "DSA Art. 15/24 Transparenzbericht",
        "reporting_entity": "SafeVoice e.V.",
        "reporting_period": {
            "start": (now.replace(month=1, day=1)).strftime("%Y-%m-%d"),
            "end": now.strftime("%Y-%m-%d"),
        },
        "total_reports": total_reported,
        "total_evidence_items": total_evidence,
        "reports_by_category": dict(category_counter.most_common()),
        "reports_by_country": dict(country_counter),
        "severity_breakdown": dict(severity_counter),
        "average_response_time_hours": 36.5,  # simulated metric
        "removal_rate": removal_rate,
        "content_moderation_orders_received": 0,
        "automated_detection_percentage": 0.78,
        "methodology_description": methodology_de if lang == "de" else methodology_en,
        "legal_basis": "Regulation (EU) 2022/2065 – Digital Services Act",
        "generated_at": now.isoformat(),
    }


# ---------------------------------------------------------------------------
# 5.3 Academic Research Dataset
# ---------------------------------------------------------------------------

def generate_research_dataset(cases: list[Case]) -> dict:
    """
    Generate a fully anonymized dataset for academic research.

    CRITICAL: No PII — no usernames, URLs, raw content text, display names,
    victim_context, or any other personally identifiable information.
    """

    records = []
    for case in cases:
        # Category counts across the case
        cat_counter: Counter = Counter()
        for ev in case.evidence_items:
            if ev.classification:
                for cat in ev.classification.categories:
                    cat_counter[cat.value] += 1

        # Pattern flags (type + severity only — descriptions may leak info)
        safe_patterns = [
            {"type": pf.type, "severity": pf.severity.value}
            for pf in case.pattern_flags
        ]

        records.append({
            "case_id": _hash_id(case.id),
            "category_counts": dict(cat_counter),
            "severity": case.overall_severity.value,
            "timestamp": case.created_at.strftime("%Y-%m-%d"),  # date only
            "platform": case.evidence_items[0].platform if case.evidence_items else "unknown",
            "country": "DE",
            "evidence_count": len(case.evidence_items),
            "pattern_flags": safe_patterns,
        })

    data_dictionary = _build_data_dictionary()

    return {
        "dataset_name": "SafeVoice Anonymized Research Dataset",
        "version": "1.0.0",
        "license": "CC BY-NC 4.0",
        "anonymization_method": "SHA-256 hashing of identifiers; PII fields stripped entirely",
        "record_count": len(records),
        "records": records,
        "data_dictionary": data_dictionary,
    }


def _build_data_dictionary() -> list[dict]:
    """Return a data dictionary explaining every field in the research dataset."""
    return [
        {
            "field": "case_id",
            "type": "string",
            "description": "Truncated SHA-256 hash of the original case ID. Cannot be reversed to identify the case.",
        },
        {
            "field": "category_counts",
            "type": "object",
            "description": "Mapping of offense category to number of evidence items in that category.",
        },
        {
            "field": "severity",
            "type": "string",
            "description": "Overall case severity: low, medium, high, or critical.",
        },
        {
            "field": "timestamp",
            "type": "string (YYYY-MM-DD)",
            "description": "Date the case was created. Time component removed for privacy.",
        },
        {
            "field": "platform",
            "type": "string",
            "description": "Social-media platform where the incident originated.",
        },
        {
            "field": "country",
            "type": "string (ISO 3166-1 alpha-2)",
            "description": "Country of origin for the report.",
        },
        {
            "field": "evidence_count",
            "type": "integer",
            "description": "Number of evidence items associated with the case.",
        },
        {
            "field": "pattern_flags",
            "type": "array of objects",
            "description": "Detected behavioral patterns (type + severity only; descriptions stripped to avoid PII leakage).",
        },
    ]


# ---------------------------------------------------------------------------
# 5.4 Digitale-Gewalt-Gesetz Submission
# ---------------------------------------------------------------------------

def generate_dgeg_submission(cases: list[Case], lang: str = "de") -> dict:
    """
    Generate structured data for German parliament consultation on the
    Digitale-Gewalt-Gesetz (Digital Violence Act).
    """

    total = len(cases)

    # Severity breakdown
    severity_counter: Counter = Counter()
    for c in cases:
        severity_counter[c.overall_severity.value] += 1

    # Offense frequency
    offense_counter: Counter = Counter()
    for c in cases:
        for ev in c.evidence_items:
            if ev.classification:
                for cat in ev.classification.categories:
                    offense_counter[cat.value] += 1

    most_common = [
        {"offense": off, "count": cnt}
        for off, cnt in offense_counter.most_common(10)
    ]

    # Platform compliance (simulated)
    platform_counter: Counter = Counter()
    for c in cases:
        for ev in c.evidence_items:
            platform_counter[ev.platform] += 1

    platform_compliance = {
        platform: {
            "total_reports": count,
            "removal_rate": 0.25,  # simulated
            "average_response_days": 5,
        }
        for platform, count in platform_counter.items()
    }

    # Victim demographics — anonymized: only platform + category
    victim_demographics = []
    for c in cases:
        cats = set()
        plats = set()
        for ev in c.evidence_items:
            plats.add(ev.platform)
            if ev.classification:
                for cat in ev.classification.categories:
                    cats.add(cat.value)
        victim_demographics.append({
            "platforms": sorted(plats),
            "categories": sorted(cats),
        })

    policy_recommendations_de = [
        "Einfuehrung verbindlicher Plattform-Reaktionsfristen (24h fuer schwere, 72h fuer sonstige Faelle).",
        "Schaffung einer zentralen Meldestelle fuer digitale Gewalt beim BKA.",
        "Erweiterung des Auskunftsanspruchs (Account-Daten) fuer Opfer gemaess DGeG-Entwurf.",
        "Verankerung des SafeVoice-Beweisstandardformats als anerkannter Beweissicherungsstandard.",
        "Verpflichtende jaehrliche DSA-Transparenzberichte fuer Plattformen mit >1 Mio. Nutzern in DE.",
        "Foerderung zivilgesellschaftlicher Beratungsstellen fuer Betroffene digitaler Gewalt.",
    ]

    policy_recommendations_en = [
        "Introduce mandatory platform response deadlines (24h for severe, 72h for other cases).",
        "Establish a central digital violence reporting office at the BKA (Federal Criminal Police).",
        "Expand the right to information (account data) for victims per the DGeG draft.",
        "Adopt the SafeVoice Evidence Standard Format as a recognized evidence preservation standard.",
        "Mandate annual DSA transparency reports for platforms with >1M users in Germany.",
        "Fund civil-society counseling centers for victims of digital violence.",
    ]

    return {
        "submission_title": (
            "Stellungnahme zum Digitale-Gewalt-Gesetz (DGeG)"
            if lang == "de"
            else "Submission on the Digital Violence Act (Digitale-Gewalt-Gesetz)"
        ),
        "submitting_entity": "SafeVoice e.V.",
        "submission_date": date.today().isoformat(),
        "total_cases": total,
        "severity_breakdown": dict(severity_counter),
        "most_common_offenses": most_common,
        "platform_compliance_rates": platform_compliance,
        "victim_demographics": victim_demographics,
        "policy_recommendations_de": policy_recommendations_de,
        "policy_recommendations_en": policy_recommendations_en,
        "legal_references": [
            "Entwurf eines Gesetzes gegen digitale Gewalt (DGeG)",
            "NetzDG (Netzwerkdurchsetzungsgesetz)",
            "DSA (Regulation (EU) 2022/2065)",
            "StGB §§ 185, 186, 241, 126a, 263",
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# 5.5 Europol SIENA Cross-Border Flagging Package
# ---------------------------------------------------------------------------

def generate_europol_siena(cases: list[Case]) -> dict:
    """
    Generate a SIENA-compatible cross-border flagging package.

    SIENA = Secure Information Exchange Network Application.
    Offenders are pseudonymized (hash only, no real usernames).
    """

    # Collect pseudonymized offender hashes
    offender_hashes: set[str] = set()
    for c in cases:
        for ev in c.evidence_items:
            offender_hashes.add(_hash_id(ev.author_username))

    # Offense types across all cases
    offense_types: set[str] = set()
    for c in cases:
        for ev in c.evidence_items:
            if ev.classification:
                for cat in ev.classification.categories:
                    offense_types.add(cat.value)

    # Cross-border indicators
    cross_border_indicators = {
        "multi_language_content": _detect_multi_language(cases),
        "foreign_platform_operators": _detect_foreign_operators(cases),
        "cross_border_victim_offender": False,  # would require real geo data
    }

    # Urgency: critical if any case is CRITICAL
    has_critical = any(c.overall_severity == Severity.CRITICAL for c in cases)

    return {
        "siena_package_version": "2.0",
        "reference_number": f"SV-SIENA-{uuid.uuid4().hex[:8].upper()}",
        "originating_country": "DE",
        "requesting_authority": "SafeVoice e.V. / BKA Zentralstelle Cybercrime",
        "submission_timestamp": datetime.now(timezone.utc).isoformat(),
        "cross_border_indicators": cross_border_indicators,
        "flagged_offenders": [
            {"pseudonymized_id": h, "hash_algorithm": "SHA-256 (truncated)"}
            for h in sorted(offender_hashes)
        ],
        "offense_types": sorted(offense_types),
        "total_cases": len(cases),
        "total_evidence_items": sum(len(c.evidence_items) for c in cases),
        "urgency_level": "high" if has_critical else "standard",
        "legal_basis": [
            "Regulation (EU) 2016/794 (Europol Regulation)",
            "Council Decision 2009/371/JHA",
            "DSA Regulation (EU) 2022/2065 Art. 18",
        ],
    }


def _detect_multi_language(cases: list[Case]) -> bool:
    """Heuristic: check if evidence items contain content in multiple languages."""
    has_german = False
    has_english = False
    german_markers = {"der", "die", "das", "und", "ist", "nicht", "ein", "eine", "ich", "du", "wir"}
    for c in cases:
        for ev in c.evidence_items:
            words = set(ev.content_text.lower().split())
            if words & german_markers:
                has_german = True
            else:
                has_english = True
    return has_german and has_english


def _detect_foreign_operators(cases: list[Case]) -> list[str]:
    """Identify platforms whose parent companies are outside the originating country."""
    foreign_map = {
        "instagram": "Meta Platforms Inc. (US)",
        "x": "X Corp. (US)",
        "tiktok": "ByteDance Ltd. (CN)",
        "facebook": "Meta Platforms Inc. (US)",
        "youtube": "Alphabet Inc. (US)",
        "telegram": "Telegram FZ-LLC (AE)",
    }
    platforms_seen: set[str] = set()
    for c in cases:
        for ev in c.evidence_items:
            platforms_seen.add(ev.platform.lower())

    return [
        foreign_map[p]
        for p in sorted(platforms_seen)
        if p in foreign_map
    ]
