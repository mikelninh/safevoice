"""
Pattern detection service.
Identifies coordinated attacks, serial harassers, and escalation patterns.
"""

from collections import Counter
from datetime import timedelta
from app.models.evidence import EvidenceItem, PatternFlag, Severity, Category


COORDINATION_WINDOW_MINUTES = 15
SERIAL_HARASSER_THRESHOLD = 2


def detect_patterns(evidence_items: list[EvidenceItem]) -> list[PatternFlag]:
    flags: list[PatternFlag] = []

    flags.extend(_detect_coordinated_attack(evidence_items))
    flags.extend(_detect_escalation(evidence_items))
    flags.extend(_detect_repeat_offender(evidence_items))

    return flags


def _detect_coordinated_attack(items: list[EvidenceItem]) -> list[PatternFlag]:
    if len(items) < 3:
        return []

    sorted_items = sorted(items, key=lambda i: i.captured_at)
    flags = []

    # Sliding window: look for 3+ items within COORDINATION_WINDOW_MINUTES
    for i, item in enumerate(sorted_items):
        window = [
            x for x in sorted_items[i:]
            if (x.captured_at - item.captured_at) <= timedelta(minutes=COORDINATION_WINDOW_MINUTES)
        ]
        unique_authors = {x.author_username for x in window}

        if len(window) >= 3 and len(unique_authors) >= 3:
            flags.append(PatternFlag(
                type="coordinated_attack",
                description=f"{len(unique_authors)} different accounts posted harassing content within {COORDINATION_WINDOW_MINUTES} minutes of each other. This suggests a coordinated attack.",
                description_de=f"{len(unique_authors)} verschiedene Konten haben innerhalb von {COORDINATION_WINDOW_MINUTES} Minuten belästigende Inhalte gepostet. Dies deutet auf einen koordinierten Angriff hin.",
                evidence_count=len(window),
                severity=Severity.HIGH
            ))
            break

    return flags


def _detect_escalation(items: list[EvidenceItem]) -> list[PatternFlag]:
    if len(items) < 2:
        return []

    severity_order = {
        Severity.LOW: 0,
        Severity.MEDIUM: 1,
        Severity.HIGH: 2,
        Severity.CRITICAL: 3
    }

    classified = [i for i in items if i.classification is not None]
    if len(classified) < 2:
        return []

    sorted_items = sorted(classified, key=lambda i: i.captured_at)
    first_severity = sorted_items[0].classification.severity
    last_severity = sorted_items[-1].classification.severity

    if severity_order[last_severity] > severity_order[first_severity]:
        has_critical = any(
            i.classification.severity == Severity.CRITICAL for i in sorted_items
        )
        return [PatternFlag(
            type="escalation",
            description=f"Content severity escalated from {first_severity.value} to {last_severity.value} over {len(sorted_items)} incidents. {'Immediate action required.' if has_critical else 'Monitor closely.'}",
            description_de=f"Der Schweregrad eskalierte von {first_severity.value} auf {last_severity.value} über {len(sorted_items)} Vorfälle. {'Sofortiges Handeln erforderlich.' if has_critical else 'Engmaschig beobachten.'}",
            evidence_count=len(sorted_items),
            severity=last_severity
        )]

    return []


def _detect_repeat_offender(items: list[EvidenceItem]) -> list[PatternFlag]:
    author_counts = Counter(i.author_username for i in items)
    flags = []

    for username, count in author_counts.items():
        if count >= SERIAL_HARASSER_THRESHOLD:
            flags.append(PatternFlag(
                type="repeat_offender",
                description=f"@{username} has posted {count} harassing items in this case. This is a pattern of repeated targeted harassment.",
                description_de=f"@{username} hat {count} belästigende Inhalte in diesem Fall gepostet. Dies ist ein Muster wiederholter gezielter Belästigung.",
                evidence_count=count,
                severity=Severity.HIGH
            ))

    return flags


def compute_overall_severity(evidence_items: list[EvidenceItem]) -> Severity:
    if not evidence_items:
        return Severity.LOW

    severity_order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]

    classified = [i for i in evidence_items if i.classification is not None]
    if not classified:
        return Severity.LOW

    max_severity = max(
        classified,
        key=lambda i: severity_order.index(i.classification.severity)
    ).classification.severity

    return max_severity
