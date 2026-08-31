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
