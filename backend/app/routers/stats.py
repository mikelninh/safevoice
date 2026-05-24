"""
Public aggregate stats — the "Lagebild digitale Gewalt" data layer.

Privacy by construction:
  - Only counts. No content, no usernames, no case IDs, no per-incident rows.
  - Single-dimension aggregates (severity / category / statute / platform /
    month). We never cross-tabulate, so cells can't be narrowed to a person.
  - MIN_BUCKET suppresses tiny cells in the dimensions that could, combined
    with outside knowledge, get close to one case. Raise it in production.

This reuses the same classification data the app already stores — no new
logging needed for v1. v2 (time-series outcome funnel) builds on the M3
events table.
"""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import (
    Classification,
    EvidenceItem,
    get_db,
)

router = APIRouter(prefix="/stats", tags=["stats"])

# Cells below this are dropped from the breakdowns that could approach a single
# case. Counts themselves are not personal data ("5 misogyny cases"), but a
# small cell + outside knowledge could narrow things — so we suppress them.
# Raise to 5+ once real volume exists.
MIN_BUCKET = 1

# Fixed severity order so the UI renders consistently.
_SEVERITY_ORDER = ["low", "medium", "high", "critical"]


def _suppress(counter: Counter) -> list[dict]:
    """Sorted [{label, count}], dropping cells below MIN_BUCKET."""
    return [
        {"label": label, "count": count}
        for label, count in counter.most_common()
        if count >= MIN_BUCKET
    ]


@router.get("/public")
def public_stats(db: Session = Depends(get_db)) -> dict:
    """Aggregate, privacy-safe counts for the public Lagebild page."""
    classifications = db.query(Classification).all()
    total = len(classifications)

    severity = Counter()
    category = Counter()
    statute = Counter()
    for c in classifications:
        if c.severity:
            severity[c.severity] += 1
        for cat in c.categories or []:
            category[cat.name_de or cat.name] += 1
        for law in c.laws or []:
            statute[f"§ {law.section} {law.code.upper()}"] += 1

    platform = Counter()
    month = Counter()  # YYYY-MM buckets from evidence timestamps — the trend line
    for ev in db.query(EvidenceItem).all():
        if ev.platform:
            platform[ev.platform] += 1
        if ev.timestamp_utc:
            month[ev.timestamp_utc.strftime("%Y-%m")] += 1

    severity_ordered = [
        {"label": s, "count": severity.get(s, 0)}
        for s in _SEVERITY_ORDER
        if severity.get(s, 0) >= MIN_BUCKET
    ]

    return {
        "total_incidents": total,
        "by_severity": severity_ordered,
        "by_category": _suppress(category),
        "by_statute": _suppress(statute),
        "by_platform": _suppress(platform),
        "by_month": sorted(
            ({"label": m, "count": n} for m, n in month.items() if n >= MIN_BUCKET),
            key=lambda x: x["label"],
        ),
        "privacy_note": (
            "Aggregate counts only. No content, no identities, no per-incident "
            "data. Small cells are suppressed."
        ),
    }
