"""Loads tickets from a CSV export."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from .models import Ticket

REQUIRED_COLUMNS = {"ticket_id", "created_at", "priority", "category", "status"}


class TicketLoadError(ValueError):
    pass


def _parse_ts(value):
    value = (value or "").strip()
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_tickets(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise TicketLoadError(f"{path}: file has no header row")
        normalized_fields = {f.strip().lower(): f for f in reader.fieldnames}
        missing = REQUIRED_COLUMNS - set(normalized_fields)
        if missing:
            raise TicketLoadError(f"{path}: missing required column(s) {sorted(missing)}. Found columns: {reader.fieldnames}")
        tickets = []
        for line_no, row in enumerate(reader, start=2):
            row = {k.strip().lower(): v for k, v in row.items()}
            try:
                created = _parse_ts(row["created_at"])
                if created is None:
                    raise TicketLoadError(f"{path}:{line_no}: created_at is required")
                tickets.append(Ticket(
                    ticket_id=row["ticket_id"], created_at=created,
                    resolved_at=_parse_ts(row.get("resolved_at", "")),
                    priority=row["priority"].strip(), category=row["category"].strip(),
                    status=row["status"].strip(), assignee=(row.get("assignee") or "").strip(),
                ))
            except (KeyError, ValueError) as exc:
                raise TicketLoadError(f"{path}:{line_no}: {exc}") from exc
    return sorted(tickets, key=lambda t: t.created_at)
