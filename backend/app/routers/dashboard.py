"""
Anonymized data dashboard — aggregate statistics for BKA, researchers, and public transparency.
All data is fully anonymized: no PII, no individual case details.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from collections import Counter
from app.data.mock_data import get_all_cases
from app.models.evidence import Severity, Category

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DashboardStats(BaseModel):
    total_cases: int
    total_evidence_items: int
    severity_distribution: dict[str, int]
    category_distribution: dict[str, int]
    platform_distribution: dict[str, int]
    requires_immediate_action_count: int
    avg_evidence_per_case: float
    top_categories: list[dict]
    severity_trend: list[dict]  # Simplified: severity counts


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats():
    """
    Get fully anonymized aggregate statistics.
    No PII or individual case details are exposed.
    """
    cases = get_all_cases()

    total_cases = len(cases)
    all_evidence = []
    for c in cases:
        all_evidence.extend(c.evidence_items)

    total_evidence = len(all_evidence)

    # Severity distribution
    severity_counter: Counter = Counter()
    for c in cases:
        severity_counter[c.overall_severity.value] += 1

    # Category distribution (across all evidence)
    category_counter: Counter = Counter()
    immediate_action_count = 0
    platform_counter: Counter = Counter()

    for ev in all_evidence:
        platform_counter[ev.platform] += 1
        if ev.classification:
            for cat in ev.classification.categories:
                category_counter[cat.value] += 1
            if ev.classification.requires_immediate_action:
                immediate_action_count += 1

    # Top categories
    top_cats = [
        {"category": cat, "count": count}
        for cat, count in category_counter.most_common(10)
    ]

    # Severity trend (simplified — just counts per severity)
    severity_trend = [
        {"severity": sev, "count": count}
        for sev, count in severity_counter.most_common()
    ]

    avg_evidence = total_evidence / total_cases if total_cases > 0 else 0

    return DashboardStats(
        total_cases=total_cases,
        total_evidence_items=total_evidence,
        severity_distribution=dict(severity_counter),
        category_distribution=dict(category_counter),
        platform_distribution=dict(platform_counter),
        requires_immediate_action_count=immediate_action_count,
        avg_evidence_per_case=round(avg_evidence, 1),
        top_categories=top_cats,
        severity_trend=severity_trend,
    )


@router.get("/categories")
def get_category_breakdown():
    """Category breakdown with severity cross-tabulation."""
    cases = get_all_cases()
    breakdown: dict[str, dict[str, int]] = {}

    for case in cases:
        for ev in case.evidence_items:
            if not ev.classification:
                continue
            for cat in ev.classification.categories:
                cat_name = cat.value
                if cat_name not in breakdown:
                    breakdown[cat_name] = {"low": 0, "medium": 0, "high": 0, "critical": 0, "total": 0}
                breakdown[cat_name][ev.classification.severity.value] += 1
                breakdown[cat_name]["total"] += 1

    return {"categories": breakdown}


@router.get("/platforms")
def get_platform_stats():
    """Platform-level statistics."""
    cases = get_all_cases()
    platform_stats: dict[str, dict] = {}

    for case in cases:
        for ev in case.evidence_items:
            p = ev.platform
            if p not in platform_stats:
                platform_stats[p] = {"total": 0, "critical": 0, "high": 0}
            platform_stats[p]["total"] += 1
            if ev.classification:
                if ev.classification.severity == Severity.CRITICAL:
                    platform_stats[p]["critical"] += 1
                elif ev.classification.severity == Severity.HIGH:
                    platform_stats[p]["high"] += 1

    return {"platforms": platform_stats}
