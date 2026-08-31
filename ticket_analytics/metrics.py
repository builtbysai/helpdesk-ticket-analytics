"""Computes helpdesk metrics: volume, resolution time, SLA compliance, backlog aging."""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from .models import DEFAULT_SLA_HOURS, Ticket

BACKLOG_BUCKETS = [
    ("0-1 days", 0, 24),
    ("1-3 days", 24, 72),
    ("3-7 days", 72, 168),
    ("7+ days", 168, float("inf")),
]

_DOW_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@dataclass
class MetricsReport:
    total_tickets: int
    resolved_count: int
    open_count: int
    avg_resolution_hours: float | None
    median_resolution_hours: float | None
    resolution_by_priority: dict
    sla_compliance_overall_pct: float | None
    sla_compliance_by_priority: dict
    volume_by_category: list
    volume_by_priority: dict
    volume_by_day_of_week: dict
    volume_by_hour: dict
    backlog_aging: dict
    date_range: tuple
    tickets_per_week: list = field(default_factory=list)


def compute_metrics(tickets, *, sla_config=None, as_of=None):
    sla_config = sla_config or DEFAULT_SLA_HOURS
    if not tickets:
        raise ValueError("No tickets to analyze")
    as_of = as_of or max((t.resolved_at or t.created_at) for t in tickets)
    resolved = [t for t in tickets if t.is_resolved]
    open_tickets = [t for t in tickets if not t.is_resolved]
    resolution_hours = [t.resolution_hours() for t in resolved]
    resolution_hours = [h for h in resolution_hours if h is not None]
    avg_res = statistics.mean(resolution_hours) if resolution_hours else None
    median_res = statistics.median(resolution_hours) if resolution_hours else None
    by_priority = defaultdict(list)
    for t in tickets:
        by_priority[t.priority].append(t)
    resolution_by_priority = {}
    sla_by_priority = {}
    for priority, group in by_priority.items():
        group_resolved = [t for t in group if t.is_resolved]
        hours = [t.resolution_hours() for t in group_resolved]
        hours = [h for h in hours if h is not None]
        resolution_by_priority[priority] = {
            "count": len(group), "resolved_count": len(group_resolved),
            "avg_hours": round(statistics.mean(hours), 2) if hours else None,
            "median_hours": round(statistics.median(hours), 2) if hours else None,
        }
        sla_flags = [t.met_sla(sla_config) for t in group_resolved]
        sla_flags = [f for f in sla_flags if f is not None]
        sla_by_priority[priority] = round(100.0 * sum(sla_flags) / len(sla_flags), 1) if sla_flags else None
    overall_sla_flags = [t.met_sla(sla_config) for t in resolved]
    overall_sla_flags = [f for f in overall_sla_flags if f is not None]
    sla_overall = round(100.0 * sum(overall_sla_flags) / len(overall_sla_flags), 1) if overall_sla_flags else None
    category_counts = Counter(t.category for t in tickets)
    volume_by_category = category_counts.most_common()
    priority_counts = Counter(t.priority for t in tickets)
    dow_counts = Counter(_DOW_NAMES[t.created_at.weekday()] for t in tickets)
    volume_by_dow = {name: dow_counts.get(name, 0) for name in _DOW_NAMES}
    hour_counts = Counter(t.created_at.hour for t in tickets)
    volume_by_hour = {h: hour_counts.get(h, 0) for h in range(24)}
    backlog_aging = {label: 0 for label, _, _ in BACKLOG_BUCKETS}
    for t in open_tickets:
        age = t.age_hours(as_of)
        for label, low, high in BACKLOG_BUCKETS:
            if low <= age < high:
                backlog_aging[label] += 1
                break
    week_counts = Counter()
    for t in tickets:
        iso_year, iso_week, _ = t.created_at.isocalendar()
        week_counts[f"{iso_year}-W{iso_week:02d}"] += 1
    tickets_per_week = sorted(week_counts.items())
    date_range = (min(t.created_at for t in tickets), max(t.created_at for t in tickets))
    return MetricsReport(
        total_tickets=len(tickets), resolved_count=len(resolved), open_count=len(open_tickets),
        avg_resolution_hours=round(avg_res, 2) if avg_res is not None else None,
        median_resolution_hours=round(median_res, 2) if median_res is not None else None,
        resolution_by_priority=resolution_by_priority, sla_compliance_overall_pct=sla_overall,
        sla_compliance_by_priority=sla_by_priority, volume_by_category=volume_by_category,
        volume_by_priority=dict(priority_counts), volume_by_day_of_week=volume_by_dow,
        volume_by_hour=volume_by_hour, backlog_aging=backlog_aging, date_range=date_range,
        tickets_per_week=tickets_per_week,
    )
