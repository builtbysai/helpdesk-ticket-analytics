from __future__ import annotations

from datetime import datetime, timedelta

from ticket_analytics.compare import compare_reports, format_change, format_value
from ticket_analytics.metrics import compute_metrics
from ticket_analytics.models import Ticket

BASE = datetime(2026, 5, 4, 9, 0, 0)


def _ticket(hours_to_resolve, priority="Medium", created=None, ticket_id="INC1"):
    created = created or BASE
    resolved = created + timedelta(hours=hours_to_resolve) if hours_to_resolve is not None else None
    return Ticket(
        ticket_id=ticket_id, created_at=created, resolved_at=resolved,
        priority=priority, category="Printer", status="Resolved" if resolved else "Open",
    )


def _reports():
    # Previous period: slower, sloppier.
    prev = [
        _ticket(30.0, ticket_id="P1"),          # Medium, breach (24h target)
        _ticket(10.0, ticket_id="P2"),          # Medium, met
        _ticket(None, ticket_id="P3"),         # open
        _ticket(None, ticket_id="P4"),         # open
    ]
    # Current period: faster, cleaner, one less open ticket.
    cur = [
        _ticket(5.0, ticket_id="C1"),          # Medium, met
        _ticket(8.0, ticket_id="C2"),          # Medium, met
        _ticket(None, ticket_id="C3"),         # open
    ]
    return compute_metrics(cur), compute_metrics(prev)


def test_sla_delta_up_is_good():
    cur, prev = _reports()
    cmp = compare_reports(cur, prev)
    d = cmp.by_key("sla_overall")
    assert d.previous == 50.0
    assert d.current == 100.0
    assert d.change == 50.0
    assert d.direction == "up"
    assert d.sentiment == "good"


def test_median_resolution_delta_down_is_good():
    cur, prev = _reports()
    cmp = compare_reports(cur, prev)
    d = cmp.by_key("median_resolution")
    assert d.previous == 20.0
    assert d.current == 6.5
    assert d.direction == "down"
    assert d.sentiment == "good"


def test_median_resolution_delta_up_is_bad():
    fast = compute_metrics([_ticket(2.0, ticket_id="A")])
    slow = compute_metrics([_ticket(2.0, ticket_id="B"), _ticket(20.0, ticket_id="C")])
    cmp = compare_reports(slow, fast)
    d = cmp.by_key("median_resolution")
    assert d.direction == "up"
    assert d.sentiment == "bad"


def test_open_backlog_down_is_good():
    cur, prev = _reports()
    cmp = compare_reports(cur, prev)
    d = cmp.by_key("open_backlog")
    assert d.previous == 2.0
    assert d.current == 1.0
    assert d.sentiment == "good"


def test_breaches_down_is_good():
    cur, prev = _reports()
    cmp = compare_reports(cur, prev)
    d = cmp.by_key("breaches")
    assert d.previous == 1
    assert d.current == 0
    assert d.sentiment == "good"


def test_volume_is_neutral_context():
    cur, prev = _reports()
    cmp = compare_reports(cur, prev)
    d = cmp.by_key("volume")
    assert d.previous == 4.0
    assert d.current == 3.0
    assert d.sentiment == "neutral"


def test_per_priority_deltas_present():
    cur, prev = _reports()
    cmp = compare_reports(cur, prev)
    d = cmp.by_key("sla_medium")
    assert d is not None
    assert d.sentiment == "good"
    assert cmp.by_key("sla_critical").direction == "n/a"


def test_missing_data_yields_na():
    cur, _ = _reports()
    empty_sla = compute_metrics([_ticket(None, ticket_id="X")])
    cmp = compare_reports(cur, empty_sla)
    d = cmp.by_key("sla_overall")
    assert d.direction == "n/a"
    assert d.change is None
    assert format_change(d) == "n/a"
    assert format_value(d, "previous") == "-"


def test_format_change_units():
    cur, prev = _reports()
    cmp = compare_reports(cur, prev)
    assert format_change(cmp.by_key("sla_overall")) == "+50 pts"
    assert format_change(cmp.by_key("median_resolution")) == "-13.5 h"
    assert format_change(cmp.by_key("open_backlog")) == "-1"
