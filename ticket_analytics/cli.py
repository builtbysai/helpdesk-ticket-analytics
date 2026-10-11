from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from .loader import TicketLoadError, load_tickets
from .metrics import DEFAULT_SLA_HOURS, compute_metrics
from .report import PdfExportError, export_pdf, print_console_report, write_html_report, write_summary_csv


def build_parser():
    p = argparse.ArgumentParser(
        prog="ticket-analytics",
        description="Turn a helpdesk ticket export (CSV) into SLA, resolution-time, and volume metrics.",
    )
    p.add_argument("input", help="Path to a ticket export CSV")
    p.add_argument("--html-out", help="Write an HTML report (with charts) to this path")
    p.add_argument("--csv-out", help="Write a metrics summary CSV to this path")
    p.add_argument("--sla-config", help="Path to a JSON file overriding default SLA hours per priority")
    p.add_argument("--compare", metavar="PREV_CSV",
                   help="Path to a previous-period ticket export CSV; adds a "
                        "period-over-period trend comparison to the console and HTML output")
    p.add_argument("--pdf-out", metavar="PDF_PATH",
                   help="Write a PDF of the report to this path (needs Chromium/Chrome on PATH "
                        "or CHROMIUM_BIN set; uses the report's print stylesheet)")
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
    previous = None
    if args.compare:
        try:
            prev_tickets = load_tickets(args.compare)
        except (TicketLoadError, FileNotFoundError) as exc:
            print(f"Error loading comparison file '{args.compare}': {exc}", file=sys.stderr)
            return 2
        if not prev_tickets:
            print(f"'{args.compare}' contained no tickets.", file=sys.stderr)
            return 2
    sla_config = dict(DEFAULT_SLA_HOURS)
    if args.sla_config:
        with open(args.sla_config, encoding="utf-8") as fh:
            sla_config.update(json.load(fh))
    report = compute_metrics(tickets, sla_config=sla_config)
    if args.compare:
        previous = compute_metrics(prev_tickets, sla_config=sla_config)
    print_console_report(report, previous)
    if args.csv_out:
        write_summary_csv(report, args.csv_out)
        print(f"Wrote CSV summary: {args.csv_out}")
    html_path = args.html_out
    if args.html_out:
        write_html_report(report, args.html_out, previous)
        print(f"Wrote HTML report: {args.html_out}")
    if args.pdf_out:
        source = Path(html_path) if html_path else None
        temp_html = None
        try:
            if source is None:
                temp_html = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
                temp_html.close()
                source = Path(temp_html.name)
                write_html_report(report, source, previous)
            export_pdf(source, args.pdf_out)
            print(f"Wrote PDF report: {args.pdf_out}")
        except PdfExportError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
        finally:
            if temp_html is not None:
                Path(temp_html.name).unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
