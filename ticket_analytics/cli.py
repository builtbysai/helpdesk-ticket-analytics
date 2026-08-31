from __future__ import annotations

import argparse
import json
import sys

from .loader import TicketLoadError, load_tickets
from .metrics import DEFAULT_SLA_HOURS, compute_metrics
from .report import print_console_report, write_html_report, write_summary_csv


def build_parser():
    p = argparse.ArgumentParser(
        prog="ticket-analytics",
        description="Turn a helpdesk ticket export (CSV) into SLA, resolution-time, and volume metrics.",
    )
    p.add_argument("input", help="Path to a ticket export CSV")
    p.add_argument("--html-out", help="Write an HTML report (with charts) to this path")
    p.add_argument("--csv-out", help="Write a metrics summary CSV to this path")
    p.add_argument("--sla-config", help="Path to a JSON file overriding default SLA hours per priority")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        tickets = load_tickets(args.input)
    except (TicketLoadError, FileNotFoundError) as exc:
        print(f"Error loading '{args.input}': {exc}", file=sys.stderr)
        return 2
    if not tickets:
        print(f"'{args.input}' contained no tickets.", file=sys.stderr)
        return 2
    sla_config = dict(DEFAULT_SLA_HOURS)
    if args.sla_config:
        with open(args.sla_config, encoding="utf-8") as fh:
            sla_config.update(json.load(fh))
    report = compute_metrics(tickets, sla_config=sla_config)
    print_console_report(report)
    if args.csv_out:
        write_summary_csv(report, args.csv_out)
        print(f"Wrote CSV summary: {args.csv_out}")
    if args.html_out:
        write_html_report(report, args.html_out)
        print(f"Wrote HTML report: {args.html_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
