"""Period-over-period comparison of two MetricsReport objects.

Given a current-period report and a previous-period report, produces a list of
MetricDelta values with explicit good/bad/neutral sentiment, so the report and
the console can render trend badges with the right meaning (SLA up is good,
median resolution up is bad).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .metrics import MetricsReport

PRIORITY_ORDER = ["Critical", "High", "Medium", "Low"]


@dataclass
class MetricDelta:
    key: str
    label: str
    current: float | None
    previous: float | None
    change: float | None
    unit: str          # how to render change: "pts", "h", or ""
    direction: str     # "up", "down", "unchanged", or "n/a"
    sentiment: str     # "good", "bad", or "neutral"


@dataclass
class PeriodComparison:
    current_range: tuple
    previous_range: tuple
    deltas: list = field(default_factory=list)

    def by_key(self, key):
        for d in self.deltas:
            if d.key == key:
                return d
        return None


def _delta(key, label, current, previous, *, unit="", good_when="up"):
    if current is None or previous is None:
        return MetricDelta(key, label, current, previous, None, unit, "n/a", "neutral")
    change = round(current - previous, 2)
    if change == 0:
        return MetricDelta(key, label, current, previous, 0.0, unit, "unchanged", "neutral")
    direction = "up" if change > 0 else "down"
    sentiment = "good" if direction == good_when else "bad"
    return MetricDelta(key, label, current, previous, change, unit, direction, sentiment)


def _breach_count(report: MetricsReport) -> int | None:
    """Total resolved tickets that missed their SLA target."""
    total = 0
    any_resolved = False
    for priority, stats in report.resolution_by_priority.items():
        resolved = stats["resolved_count"]
        pct = report.sla_compliance_by_priority.get(priority)
        if resolved and pct is not None:
            any_resolved = True
            met = round(resolved * pct / 100)
            total += resolved - met
    return total if any_resolved else None


def compare_reports(current: MetricsReport, previous: MetricsReport) -> PeriodComparison:
    """Compute period-over-period deltas for the headline metrics."""
    deltas = [
        _delta("sla_overall", "SLA compliance (overall)",
               current.sla_compliance_overall_pct, previous.sla_compliance_overall_pct,
               unit="pts", good_when="up"),
        _delta("median_resolution", "Median resolution",
               current.median_resolution_hours, previous.median_resolution_hours,
               unit="h", good_when="down"),
        _delta("avg_resolution", "Average resolution",
               current.avg_resolution_hours, previous.avg_resolution_hours,
               unit="h", good_when="down"),
        _delta("open_backlog", "Open backlog",
               float(current.open_count), float(previous.open_count),
               good_when="down"),
        _delta("breaches", "SLA breaches",
               _breach_count(current), _breach_count(previous),
               good_when="down"),
        _delta("volume", "Ticket volume",
               float(current.total_tickets), float(previous.total_tickets),
               unit="", good_when="up"),
    ]
    # volume is context, not performance: never good or bad
    vol = deltas[-1]
    deltas[-1] = MetricDelta(vol.key, vol.label, vol.current, vol.previous,
                             vol.change, vol.unit, vol.direction, "neutral")
    for priority in PRIORITY_ORDER:
        cur_pct = current.sla_compliance_by_priority.get(priority)
        prev_pct = previous.sla_compliance_by_priority.get(priority)
        deltas.append(
            _delta(f"sla_{priority.lower()}", f"SLA compliance ({priority})",
                   cur_pct, prev_pct, unit="pts", good_when="up"))
    return PeriodComparison(
        current_range=current.date_range,
        previous_range=previous.date_range,
        deltas=deltas,
    )


def format_change(delta: MetricDelta) -> str:
    """Human-readable change, e.g. '+2.3 pts', '-1.5h', 'no change', 'n/a'."""
    if delta.direction == "n/a":
        return "n/a"
    if delta.direction == "unchanged":
        return "no change"
    sign = "+" if delta.change > 0 else ""
    unit = f" {delta.unit}" if delta.unit else ""
    return f"{sign}{delta.change:g}{unit}"


def format_value(delta: MetricDelta, which: str) -> str:
    """Format a delta's current/previous value with its unit, e.g. '96.2%'."""
    value = delta.current if which == "current" else delta.previous
    if value is None:
        return "-"
    if delta.unit == "pts":
        return f"{value:g}%"
    if delta.unit == "h":
        return f"{value:g}h"
    if delta.key in ("open_backlog", "breaches", "volume"):
        return f"{int(value)}"
    return f"{value:g}"
