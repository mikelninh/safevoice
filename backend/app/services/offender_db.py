"""
Serial offender database — cross-case pattern matching (anonymized).
Tracks offender usernames across cases to detect repeat/serial harassers.
All data is pseudonymized — no victim PII stored.
"""

import hashlib
import logging
from datetime import datetime, timezone
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from app.models.evidence import Case, EvidenceItem, Severity, Category

logger = logging.getLogger(__name__)


@dataclass
class OffenderProfile:
    """Anonymized profile of a repeat offender."""
    username_hash: str  # SHA-256 of username (pseudonymized)
    username: str  # Original username (only stored in-memory, not persisted)
    platforms: set[str] = field(default_factory=set)
    case_count: int = 0
    evidence_count: int = 0
    categories: Counter = field(default_factory=Counter)
    max_severity: str = "low"
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    is_serial: bool = False  # 3+ cases


@dataclass
class OffenderMatch:
    """Result of checking if a username is a known offender."""
    is_known: bool
    is_serial: bool
    prior_cases: int
    prior_evidence: int
    top_categories: list[str]
    max_severity: str
    risk_level: str  # low, medium, high, critical


# In-memory offender store
_offenders: dict[str, OffenderProfile] = {}


def _hash_username(username: str) -> str:
    """Pseudonymize a username."""
    return hashlib.sha256(username.lower().strip().encode()).hexdigest()[:16]


def index_case(case: Case) -> list[OffenderProfile]:
    """Index all offender usernames from a case."""
    updated = []

    for ev in case.evidence_items:
        username = ev.author_username.lower().strip()
        if username in ("unknown", ""):
            continue

        h = _hash_username(username)

        if h not in _offenders:
            _offenders[h] = OffenderProfile(
                username_hash=h,
                username=username,
            )

        profile = _offenders[h]
        profile.platforms.add(ev.platform)
        profile.evidence_count += 1

        if ev.classification:
            for cat in ev.classification.categories:
                profile.categories[cat.value] += 1

            sev_order = ["low", "medium", "high", "critical"]
            current = ev.classification.severity.value
            if sev_order.index(current) > sev_order.index(profile.max_severity):
                profile.max_severity = current

        captured = ev.captured_at
        if isinstance(captured, str):
            captured = datetime.fromisoformat(captured)
        if profile.first_seen is None or captured < profile.first_seen:
            profile.first_seen = captured
        if profile.last_seen is None or captured > profile.last_seen:
            profile.last_seen = captured

        updated.append(profile)

    # Update case counts (deduplicate by case)
    case_offenders = set()
    for ev in case.evidence_items:
        username = ev.author_username.lower().strip()
        if username not in ("unknown", ""):
            case_offenders.add(_hash_username(username))

    for h in case_offenders:
        if h in _offenders:
            _offenders[h].case_count += 1
            _offenders[h].is_serial = _offenders[h].case_count >= 3

    return updated


def check_offender(username: str) -> OffenderMatch:
    """Check if a username is a known offender."""
    h = _hash_username(username)
    profile = _offenders.get(h)

    if not profile:
        return OffenderMatch(
            is_known=False, is_serial=False,
            prior_cases=0, prior_evidence=0,
            top_categories=[], max_severity="low",
            risk_level="low",
        )

    top_cats = [cat for cat, _ in profile.categories.most_common(3)]

    # Risk assessment
    if profile.is_serial and profile.max_severity in ("critical", "high"):
        risk = "critical"
    elif profile.is_serial:
        risk = "high"
    elif profile.case_count >= 2:
        risk = "medium"
    else:
        risk = "low"

    return OffenderMatch(
        is_known=True,
        is_serial=profile.is_serial,
        prior_cases=profile.case_count,
        prior_evidence=profile.evidence_count,
        top_categories=top_cats,
        max_severity=profile.max_severity,
        risk_level=risk,
    )


def get_serial_offenders() -> list[dict]:
    """Get all serial offenders (3+ cases). Anonymized output."""
    serials = [p for p in _offenders.values() if p.is_serial]
    return [
        {
            "username_hash": p.username_hash,
            "platforms": list(p.platforms),
            "case_count": p.case_count,
            "evidence_count": p.evidence_count,
            "top_categories": [c for c, _ in p.categories.most_common(5)],
            "max_severity": p.max_severity,
            "first_seen": p.first_seen.isoformat() if p.first_seen else None,
            "last_seen": p.last_seen.isoformat() if p.last_seen else None,
        }
        for p in sorted(serials, key=lambda x: x.evidence_count, reverse=True)
    ]


def get_offender_stats() -> dict:
    """Aggregate stats about the offender database."""
    total = len(_offenders)
    serial = sum(1 for p in _offenders.values() if p.is_serial)
    multi_platform = sum(1 for p in _offenders.values() if len(p.platforms) > 1)

    severity_dist = Counter(p.max_severity for p in _offenders.values())

    return {
        "total_tracked": total,
        "serial_offenders": serial,
        "multi_platform": multi_platform,
        "severity_distribution": dict(severity_dist),
    }


def index_all_cases(cases: list[Case]):
    """Bulk index all cases."""
    for case in cases:
        index_case(case)


# Auto-index mock cases on module load
def _seed():
    from app.data.mock_data import get_all_cases
    index_all_cases(get_all_cases())

_seed()
