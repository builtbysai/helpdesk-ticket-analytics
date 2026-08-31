from __future__ import annotations

import csv
from pathlib import Path

from .charts import bar_chart_svg
from .metrics import MetricsReport


def print_console_report(report):
    start, end = report.date_range
    print(f"\nHelpdesk Ticket Analytics - {report.total_tickets} tickets, {start.date()} to {end.date()}\n")
    print(f"  Resolved: {report.resolved_count}   Open: {report.open_count}")
    if report.avg_resolution_hours is not None:
        print(f"  Avg resolution time:    {report.avg_resolution_hours} hours")
        print(f"  Median resolution time: {report.median_resolution_hours} hours")
    if report.sla_compliance_overall_pct is not None:
        print(f"  Overall SLA compliance: {report.sla_compliance_overall_pct}%")
    print("\n  SLA compliance by priority:")
    for priority, pct in report.sla_compliance_by_priority.items():
        pct_str = f"{pct}%" if pct is not None else "n/a (no resolved tickets)"
        print(f"    {priority:<10} {pct_str}")
    print("\n  Resolution time by priority:")
    for priority, stats in report.resolution_by_priority.items():
        avg = stats["avg_hours"]
        avg_str = f"{avg}h avg" if avg is not None else "n/a"
        print(f"    {priority:<10} {stats['count']:>4} tickets ({stats['resolved_count']} resolved) - {avg_str}")
    print("\n  Top categories:")
    for category, count in report.volume_by_category[:8]:
        print(f"    {category:<24} {count}")
    print("\n  Backlog aging (open tickets):")
    for bucket, count in report.backlog_aging.items():
        print(f"    {bucket:<10} {count}")
    print("\n  Volume by day of week:")
    for day, count in report.volume_by_day_of_week.items():
        print(f"    {day:<10} {count}")
    print()


def write_summary_csv(report, path):
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["metric", "value"])
        writer.writerow(["total_tickets", report.total_tickets])
        writer.writerow(["resolved_count", report.resolved_count])
        writer.writerow(["open_count", report.open_count])
        writer.writerow(["avg_resolution_hours", report.avg_resolution_hours])
        writer.writerow(["median_resolution_hours", report.median_resolution_hours])
        writer.writerow(["sla_compliance_overall_pct", report.sla_compliance_overall_pct])
        writer.writerow([])
        writer.writerow(["priority", "count", "resolved_count", "avg_hours", "median_hours", "sla_compliance_pct"])
        for priority, stats in report.resolution_by_priority.items():
            writer.writerow([priority, stats["count"], stats["resolved_count"], stats["avg_hours"], stats["median_hours"], report.sla_compliance_by_priority.get(priority)])
        writer.writerow([])
        writer.writerow(["category", "ticket_count"])
        for category, count in report.volume_by_category:
            writer.writerow([category, count])


def write_html_report(report, path):
    path = Path(path)
    start, end = report.date_range
    category_chart = bar_chart_svg(report.volume_by_category[:10], title="Ticket volume by category")
    sla_data = [(p, v) for p, v in report.sla_compliance_by_priority.items() if v is not None]
    sla_chart = bar_chart_svg(sla_data, title="SLA compliance by priority", value_suffix="%")
    dow_chart = bar_chart_svg(list(report.volume_by_day_of_week.items()), title="Ticket volume by day of week")
    backlog_chart = bar_chart_svg(list(report.backlog_aging.items()), title="Open-ticket backlog aging")
    priority_rows = "".join(
        f"<tr><td>{p}</td><td>{s['count']}</td><td>{s['resolved_count']}</td>"
        f"<td>{s['avg_hours'] if s['avg_hours'] is not None else '-'}</td>"
        f"<td>{report.sla_compliance_by_priority.get(p) if report.sla_compliance_by_priority.get(p) is not None else '-'}</td></tr>"
        for p, s in report.resolution_by_priority.items()
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Helpdesk Ticket Analytics Report</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; color: #111827; background: #f9fafb; }}
  h1 {{ font-size: 22px; }}
  h2 {{ font-size: 16px; margin-top: 36px; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; }}
  .stat-row {{ display: flex; gap: 16px; flex-wrap: wrap; margin: 16px 0; }}
  .stat {{ background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px 18px; min-width: 160px; }}
  .stat .value {{ font-size: 24px; font-weight: 700; }}
  .stat .label {{ font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: .03em; }}
  table {{ border-collapse: collapse; width: 100%; background: white; }}
  th, td {{ text-align: left; padding: 6px 10px; border-bottom: 1px solid #e5e7eb; font-size: 13px; }}
  th {{ background: #f3f4f6; }}
  .chart-card {{ background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin: 16px 0; }}
</style>
</head>
<body>
<h1>Helpdesk Ticket Analytics</h1>
<p>{report.total_tickets} tickets, {start.date()} to {end.date()}</p>
<div class="stat-row">
  <div class="stat"><div class="value">{report.total_tickets}</div><div class="label">Total tickets</div></div>
  <div class="stat"><div class="value">{report.resolved_count}</div><div class="label">Resolved</div></div>
  <div class="stat"><div class="value">{report.open_count}</div><div class="label">Open</div></div>
  <div class="stat"><div class="value">{report.avg_resolution_hours or '-'}h</div><div class="label">Avg resolution</div></div>
  <div class="stat"><div class="value">{report.sla_compliance_overall_pct or '-'}%</div><div class="label">SLA compliance</div></div>
</div>
<h2>Resolution time &amp; SLA by priority</h2>
<table>
<tr><th>Priority</th><th>Tickets</th><th>Resolved</th><th>Avg hours</th><th>SLA compliance</th></tr>
{priority_rows}
</table>
<h2>Ticket volume by category</h2>
<div class="chart-card">{category_chart}</div>
<h2>SLA compliance by priority</h2>
<div class="chart-card">{sla_chart}</div>
<h2>Ticket volume by day of week</h2>
<div class="chart-card">{dow_chart}</div>
<h2>Open-ticket backlog aging</h2>
<div class="chart-card">{backlog_chart}</div>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")
