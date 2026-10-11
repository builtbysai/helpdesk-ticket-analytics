#!/usr/bin/env python3
"""Generates a synthetic previous-period ticket export for --compare demos.

Same generator logic as generate_sample_data.py, but covering Feb 1 to
Apr 30, 2026 (the 89 days before the main sample) with a different seed and
a deliberately higher breach rate, so the period-over-period comparison has
visible deltas. Fully synthetic; for demo purposes only.
"""
import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

random.seed(7)
OUT_PATH = Path(__file__).resolve().parent.parent / "sample_data" / "tickets_prev_period.csv"
CATEGORIES = [
    ("Password Reset", 0.22, 0.5, "Low"),
    ("Account Unlock", 0.12, 0.4, "Low"),
    ("Printer / Print Queue", 0.14, 1.5, "Low"),
    ("Network Connectivity", 0.12, 3.0, "Medium"),
    ("Active Directory Access", 0.10, 2.0, "Medium"),
    ("System Crash / BSOD", 0.08, 6.0, "High"),
    ("Software Install/Update", 0.10, 4.0, "Medium"),
    ("Hardware Failure", 0.07, 10.0, "High"),
    ("Security Incident", 0.03, 3.0, "Critical"),
    ("VPN / Remote Access", 0.02, 2.5, "Medium"),
]
ASSIGNEES = ["H. Sai", "M. Chen", "D. Ibrahim", "P. Natarajan", "R. Foster"]
START = datetime(2026, 2, 1, tzinfo=timezone.utc)
DAYS = 89
TARGET_TICKETS = 585
BREACH_PROB = 0.20  # higher than the main sample's 0.12: the trend should show improvement


def weighted_category():
    names = [c[0] for c in CATEGORIES]
    weights = [c[1] for c in CATEGORIES]
    return random.choices(names, weights=weights, k=1)[0]


def category_info(name):
    for cat, _, base_hours, priority in CATEGORIES:
        if cat == name:
            return base_hours, priority
    return 4.0, "Medium"


def business_hour_timestamp(day_offset):
    day = START + timedelta(days=day_offset)
    weekday = day.weekday()
    if weekday >= 5 and random.random() > 0.12:
        return None
    hour = int(random.triangular(6, 22, 13))
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return day.replace(hour=min(hour, 23), minute=minute, second=second)


def main():
    rows = []
    ticket_num = 5000
    attempts = 0
    while len(rows) < TARGET_TICKETS and attempts < TARGET_TICKETS * 4:
        attempts += 1
        day_offset = random.randint(0, DAYS - 1)
        created = business_hour_timestamp(day_offset)
        if created is None:
            continue
        category = weighted_category()
        base_hours, priority = category_info(category)
        ticket_num += 1
        ticket_id = f"INC{ticket_num:06d}"
        assignee = random.choice(ASSIGNEES)
        days_old = (START + timedelta(days=DAYS) - created).days
        resolved_prob = 0.35 if days_old <= 3 else 0.97
        resolved_at = ""
        status = "Open"
        if random.random() < resolved_prob:
            status = "Resolved"
            if random.random() < BREACH_PROB:
                res_hours = base_hours * random.uniform(2.2, 6.0)
            else:
                res_hours = max(0.1, random.gauss(base_hours * 0.6, base_hours * 0.35))
            resolved_dt = created + timedelta(hours=res_hours)
            resolved_at = resolved_dt.isoformat()
        rows.append({
            "ticket_id": ticket_id, "created_at": created.isoformat(), "resolved_at": resolved_at,
            "priority": priority, "category": category, "status": status, "assignee": assignee,
        })
    rows.sort(key=lambda r: r["created_at"])
    OUT_PATH.parent.mkdir(exist_ok=True)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["ticket_id", "created_at", "resolved_at", "priority", "category", "status", "assignee"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} tickets -> {OUT_PATH}")


if __name__ == "__main__":
    main()
