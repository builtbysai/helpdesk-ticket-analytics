"""Loads tickets from a CSV export.

Built to survive real exports, not just clean synthetic data:
- header names are case-insensitive and whitespace-tolerant
- encodings: UTF-8 (with or without BOM), falling back to Windows cp1252
- dates: ISO 8601 first, then common US export formats (M/D/YYYY)
- priorities: case-insensitive, plus P1-P4 and urgent/normal aliases
- blank rows are skipped; malformed rows fail with file:line numbers
"""

from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .models import VALID_PRIORITIES, Ticket

REQUIRED_COLUMNS = {"ticket_id", "created_at", "priority", "category", "status"}

# ISO 8601 is tried first (datetime.fromisoformat); these cover the formats
# real exports actually ship: ServiceNow/Remedy/Excel-style US dates.
_DATE_FORMATS = (
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d",
)

_PRIORITY_ALIASES = {p.lower(): p for p in VALID_PRIORITIES}
_PRIORITY_ALIASES.update({
    "p1": "Critical", "p2": "High", "p3": "Medium", "p4": "Low",
    "urgent": "Critical", "normal": "Medium",
})


class TicketLoadError(ValueError):
    pass


def _parse_ts(value):
    value = (value or "").strip()
    if not value:
        return None
    dt = None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        for fmt in _DATE_FORMATS:
            try:
                dt = datetime.strptime(value, fmt)
                break
            except ValueError:
                continue
    if dt is None:
        raise ValueError(f"unrecognized date format: {value!r}")
    # Normalize to naive UTC so naive and aware timestamps can mix safely.
    if dt.tzinfo is not None:
        dt = (dt - dt.utcoffset()).replace(tzinfo=None)
    return dt


def _normalize_priority(value):
    value = (value or "").strip()
    return _PRIORITY_ALIASES.get(value.lower(), value)


def _decode(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise TicketLoadError(f"{path}: could not decode file as UTF-8 or cp1252")


def load_tickets(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    text = _decode(path)
    reader = csv.DictReader(text.splitlines())
    if reader.fieldnames is None:
        raise TicketLoadError(f"{path}: file has no header row")
    normalized_fields = {f.strip().lower(): f for f in reader.fieldnames}
    missing = REQUIRED_COLUMNS - set(normalized_fields)
    if missing:
        raise TicketLoadError(f"{path}: missing required column(s) {sorted(missing)}. Found columns: {reader.fieldnames}")
    tickets = []
    for line_no, row in enumerate(reader, start=2):
        try:
            clean = {}
            for key, value in row.items():
                if key is None:
                    continue
                clean[key.strip().lower()] = value.strip() if isinstance(value, str) else value
            if not any(v for v in clean.values() if v):
                continue  # blank line
            created = _parse_ts(clean.get("created_at"))
            if created is None:
                raise TicketLoadError(f"{path}:{line_no}: created_at is required")
            missing_vals = [c for c in REQUIRED_COLUMNS if not clean.get(c)]
            if missing_vals:
                raise TicketLoadError(f"{path}:{line_no}: missing value(s) for {missing_vals}")
            tickets.append(Ticket(
                ticket_id=clean["ticket_id"], created_at=created,
                resolved_at=_parse_ts(clean.get("resolved_at", "")),
                priority=_normalize_priority(clean["priority"]),
                category=clean["category"], status=clean["status"],
                assignee=(clean.get("assignee") or "").strip(),
            ))
        except (KeyError, ValueError, AttributeError) as exc:
            if isinstance(exc, TicketLoadError):
                raise
            raise TicketLoadError(f"{path}:{line_no}: {exc}") from exc
    return sorted(tickets, key=lambda t: t.created_at)
