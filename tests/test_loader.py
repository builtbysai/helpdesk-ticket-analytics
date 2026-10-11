from __future__ import annotations

from pathlib import Path

import pytest

from ticket_analytics.loader import TicketLoadError, load_tickets


def _write(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "tickets.csv"
    path.write_text(content)
    return path


def test_loads_basic_csv(tmp_path):
    path = _write(tmp_path, (
        "ticket_id,created_at,resolved_at,priority,category,status,assignee\n"
        "INC1,2026-05-01T09:00:00,2026-05-01T10:00:00,Medium,Printer,Resolved,H. Sai\n"
        "INC2,2026-05-01T09:30:00,,Low,Password Reset,Open,H. Sai\n"
    ))
    tickets = load_tickets(path)
    assert len(tickets) == 2
    assert tickets[0].ticket_id == "INC1"
    assert tickets[0].is_resolved
    assert not tickets[1].is_resolved


def test_sorted_by_created_at(tmp_path):
    path = _write(tmp_path, (
        "ticket_id,created_at,resolved_at,priority,category,status\n"
        "INC2,2026-05-02T09:00:00,,Low,Printer,Open\n"
        "INC1,2026-05-01T09:00:00,,Low,Printer,Open\n"
    ))
    tickets = load_tickets(path)
    assert [t.ticket_id for t in tickets] == ["INC1", "INC2"]


def test_missing_required_column_raises(tmp_path):
    path = _write(tmp_path, "ticket_id,created_at\nINC1,2026-05-01T09:00:00\n")
    with pytest.raises(TicketLoadError, match="missing required column"):
        load_tickets(path)


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_tickets(tmp_path / "does-not-exist.csv")


def test_column_names_case_insensitive(tmp_path):
    path = _write(tmp_path, (
        "Ticket_ID,Created_At,Resolved_At,Priority,Category,Status\n"
        "INC1,2026-05-01T09:00:00,,Low,Printer,Open\n"
    ))
    tickets = load_tickets(path)
    assert tickets[0].ticket_id == "INC1"


def _write_bytes(tmp_path: Path, content: bytes, name: str = "tickets.csv") -> Path:
    path = tmp_path / name
    path.write_bytes(content)
    return path


def test_us_date_formats_parsed(tmp_path):
    path = _write(tmp_path, (
        "ticket_id,created_at,resolved_at,priority,category,status\n"
        "INC1,05/01/2026 09:00,05/01/2026 10:30,Medium,Printer,Resolved\n"
        "INC2,05/02/2026,,Low,Password Reset,Open\n"
    ))
    tickets = load_tickets(path)
    assert len(tickets) == 2
    assert tickets[0].resolved_at is not None
    assert tickets[0].resolution_hours() == 1.5


def test_priority_case_and_aliases_normalized(tmp_path):
    path = _write(tmp_path, (
        "ticket_id,created_at,priority,category,status\n"
        "INC1,2026-05-01T09:00:00,HIGH,Printer,Open\n"
        "INC2,2026-05-01T10:00:00,p2,VPN,Open\n"
        "INC3,2026-05-01T11:00:00,urgent,Security,Open\n"
    ))
    tickets = load_tickets(path)
    assert [t.priority for t in tickets] == ["High", "High", "Critical"]


def test_unknown_priority_kept_as_is(tmp_path):
    path = _write(tmp_path, (
        "ticket_id,created_at,priority,category,status\n"
        "INC1,2026-05-01T09:00:00,Informational,Printer,Open\n"
    ))
    tickets = load_tickets(path)
    assert tickets[0].priority == "Informational"


def test_cp1252_encoding_with_smart_quotes(tmp_path):
    content = (
        "ticket_id,created_at,priority,category,status\n"
        'INC1,2026-05-01T09:00:00,Medium,Printer \u2013 2nd floor,Open\n'
    ).encode("cp1252")
    path = _write_bytes(tmp_path, content)
    tickets = load_tickets(path)
    assert tickets[0].category == "Printer \u2013 2nd floor"


def test_blank_rows_and_whitespace_skipped(tmp_path):
    path = _write(tmp_path, (
        "  ticket_id , created_at , priority , category , status \n"
        "\n"
        "INC1, 2026-05-01T09:00:00 , Medium , Printer , Open\n"
        "\n"
    ))
    tickets = load_tickets(path)
    assert len(tickets) == 1
    assert tickets[0].ticket_id == "INC1"
    assert tickets[0].priority == "Medium"


def test_malformed_row_raises_with_line_number(tmp_path):
    path = _write(tmp_path, (
        "ticket_id,created_at,priority,category,status\n"
        "INC1,2026-05-01T09:00:00,Medium,Printer,Open\n"
        "INC2,not-a-date,Medium,Printer,Open\n"
    ))
    with pytest.raises(TicketLoadError, match=":3:"):
        load_tickets(path)


def test_short_row_raises_with_line_number(tmp_path):
    path = _write(tmp_path, (
        "ticket_id,created_at,priority,category,status\n"
        "INC1,2026-05-01T09:00:00,Medium,Printer,Open\n"
        "INC2,2026-05-02T09:00:00\n"
    ))
    with pytest.raises(TicketLoadError, match=":3:"):
        load_tickets(path)


def test_mixed_timezone_formats_normalized(tmp_path):
    path = _write(tmp_path, (
        "ticket_id,created_at,resolved_at,priority,category,status\n"
        "INC1,2026-05-01T09:00:00Z,2026-05-01T10:00:00+00:00,Medium,Printer,Resolved\n"
        "INC2,2026-05-01T09:00:00,2026-05-01T10:00:00,Medium,Printer,Resolved\n"
    ))
    tickets = load_tickets(path)
    assert len(tickets) == 2
    assert all(t.resolution_hours() == 1.0 for t in tickets)
