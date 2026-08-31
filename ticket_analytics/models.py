from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

DEFAULT_SLA_HOURS = {
    "Critical": 4.0,
    "High": 8.0,
    "Medium": 24.0,
    "Low": 72.0,
}

VALID_PRIORITIES = tuple(DEFAULT_SLA_HOURS.keys())


@dataclass
class Ticket:
    ticket_id: str
    created_at: datetime
    priority: str
    category: str
    status: str
    assignee: str = ""
    resolved_at: datetime | None = None

    @property
    def is_resolved(self):
        return self.resolved_at is not None

    def resolution_hours(self):
        if self.resolved_at is None:
            return None
        return (self.resolved_at - self.created_at).total_seconds() / 3600.0

    def sla_target_hours(self, sla_config=None):
        config = sla_config or DEFAULT_SLA_HOURS
        return config.get(self.priority, DEFAULT_SLA_HOURS.get("Medium", 24.0))

    def met_sla(self, sla_config=None):
        hours = self.resolution_hours()
        if hours is None:
            return None
        return hours <= self.sla_target_hours(sla_config)

    def age_hours(self, as_of):
        end = self.resolved_at or as_of
        return (end - self.created_at).total_seconds() / 3600.0
