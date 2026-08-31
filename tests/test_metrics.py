from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from ticket_analytics.metrics import compute_metrics
from ticket_analytics.models import Ticket

BASE = datetime(2026, 5, 4, 9, 0, 0)


def _ticket(hours_to_resolve=None, priority="Medium", category="Printer", created=None, ticket_id="INC1"):
    created = created or BASE
    resolved = created + timedelta(hours=hours_to_resolve) if hours_to_resolve is not None else None
    return Ticket(
        ticket_id=ticket_id, created_at=created, resolved_at=resolved,
        priority=priority, category=category, status="Resolved" if resolved else "Open",
    )


def test_empty_list_raises():
    with pytest.raises(ValueError):
        compute_metrics([])


def test_basic_counts():
    tickets = [_ticket(1.0, ticket_id="INC1"), _ticket(None, ticket_id="INC2")]
    report = compute_metrics(tickets)
    assert report.total_tickets == 2
    assert report.resolved_count == 1
    assert report.open_count == 1


def test_avg_and_median_resolution():
    tickets = [_ticket(2.0, ticket_id="INC1"), _ticket(4.0, ticket_id="INC2"), _ticket(6.0, ticket_id="INC3")]
    report = compute_metrics(tickets)
    assert report.avg_resolution_hours == 4.0
    assert report.median_resolution_hours == 4.0


def test_sla_compliance_flags_breach():
    within = _ticket(10.0, priority="Medium", ticket_id="INC1")
    breach = _ticket(30.0, priority="Medium", ticket_id="INC2")
    report = compute_metrics([within, breach])
    assert report.sla_compliance_overall_pct == 50.0
    assert report.sla_compliance_by_priority["Medium"] == 50.0


def test_sla_compliance_none_when_nothing_resolved():
    tickets = [_ticket(None, priority="Low", ticket_id="INC1")]
    report = compute_metrics(tickets)
    assert report.sla_compliance_overall_pct is None
    assert report.sla_compliance_by_priority["Low"] is None


def test_custom_sla_config_overrides_default():
    ticket = _ticket(5.0, priority="Medium", ticket_id="INC1")
    report = compute_metrics([ticket], sla_config={"Medium": 2.0})
    assert report.sla_compliance_overall_pct == 0.0


def test_volume_by_category_sorted_descending():
    tickets = [
        _ticket(1.0, category="Printer", ticket_id="INC1"),
        _ticket(1.0, category="Printer", ticket_id="INC2"),
        _ticket(1.0, category="VPN", ticket_id="INC3"),
    ]
    report = compute_metrics(tickets)
    assert report.volume_by_category[0] == ("Printer", 2)


def test_backlog_aging_buckets_open_tickets_by_age():
    as_of = BASE + timedelta(days=10)
    tickets = [
        _ticket(None, created=BASE, ticket_id="INC1"),
        _ticket(None, created=BASE + timedelta(days=9, hours=12), ticket_id="INC2"),
    ]
    report = compute_metrics(tickets, as_of=as_of)
    assert report.backlog_aging["7+ days"] == 1
    assert report.backlog_aging["0-1 days"] == 1


def test_day_of_week_and_hour_breakdown():
    tickets = [_ticket(1.0, created=BASE, ticket_id="INC1")]
    report = compute_metrics(tickets)
    assert report.volume_by_day_of_week["Monday"] == 1
    assert report.volume_by_hour[9] == 1
