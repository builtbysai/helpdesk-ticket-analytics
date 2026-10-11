from __future__ import annotations

import csv
from datetime import datetime, timedelta
from pathlib import Path

from . import charts
from .charts import hbars, hour_strip, weekly_trend, sla_band
from .metrics import MetricsReport
from .models import DEFAULT_SLA_HOURS

PRIORITY_ORDER = ["Critical", "High", "Medium", "Low"]

CSS = """:root {
  --bg: #0b0e13;
  --panel: #12181f;
  --panel-2: #161e28;
  --ink: #e8eef4;
  --muted: #8b98a5;
  --faint: #5c6a77;
  --rule: #232c36;
  --green: #3fb950;
  --amber: #d29922;
  --red: #f85149;
  --accent: #6cb6ff;
  --sans: system-ui, -apple-system, 'Segoe UI', 'Liberation Sans', 'DejaVu Sans', Arial, sans-serif;
  --mono: ui-monospace, 'SFMono-Regular', Menlo, Consolas, monospace;
}
* { box-sizing: border-box; }
body {
  font-family: var(--sans);
  color: var(--ink);
  background: var(--bg);
  margin: 0;
  font-size: 15.5px;
  line-height: 1.55;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
.wrap { max-width: 920px; margin: 0 auto; padding: 56px 32px 80px; }

/* masthead */
.masthead { border-top: 4px solid var(--accent); padding-top: 18px; margin-bottom: 44px; }
.masthead .row { display: flex; align-items: center; gap: 16px; }
.mark { flex: 0 0 auto; }
.eyebrow {
  font-size: 11.5px; letter-spacing: 0.22em; color: var(--muted);
  text-transform: uppercase; margin: 0 0 10px;
}
h1 {
  font-weight: 800; font-size: 40px;
  line-height: 1.1; margin: 0 0 10px; letter-spacing: -0.02em;
}
.dek { font-size: 16.5px; color: var(--muted); margin: 0; max-width: 640px; }
.masthead .rule { border: 0; border-top: 1px solid var(--rule); margin: 22px 0 0; }

/* sections */
section { margin: 0 0 56px; }
.sec-label {
  font-size: 11.5px; letter-spacing: 0.22em; text-transform: uppercase;
  color: var(--faint); margin: 0 0 6px;
}
h2 {
  font-size: 26px; font-weight: 800;
  margin: 0 0 10px; letter-spacing: -0.02em;
}
.lede { font-size: 16px; color: #b6c2cd; max-width: 680px; margin: 0 0 22px; }
.sec-rule { border: 0; border-top: 2px solid var(--accent); width: 56px; margin: 0 0 26px; }

/* stat cards */
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 26px 0 8px; }
.stat {
  background: var(--panel); border: 1px solid var(--rule);
  padding: 18px 18px 16px;
}
.stat .num {
  font-size: 38px; font-weight: 800;
  line-height: 1; margin: 0 0 8px; letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}
.stat .num small { font-size: 20px; font-weight: 400; color: var(--muted); }
.stat .cap { font-size: 12.5px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); margin: 0 0 6px; }
.stat .sub { font-size: 13px; color: var(--muted); margin: 0; }
.num.good { color: var(--green); }
.num.bad { color: var(--red); }
.num.warn { color: var(--amber); }

/* tables */
table { border-collapse: collapse; width: 100%; background: var(--panel); }
caption { text-align: left; font-size: 12.5px; color: var(--muted); padding: 0 0 8px; caption-side: top; }
th, td { padding: 9px 14px; font-size: 14px; border-bottom: 1px solid var(--rule); }
th {
  font-size: 11.5px; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--muted); font-weight: 700; text-align: left;
  border-bottom: 2px solid #3a4654;
}
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
tr:last-child td { border-bottom: 0; }
tbody tr:hover { background: var(--panel-2); }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; vertical-align: baseline; }

/* chart frames */
.figure { background: var(--panel); border: 1px solid var(--rule); padding: 22px 22px 14px; margin: 0 0 26px; }
.figure figcaption { font-size: 13px; color: var(--muted); margin: 6px 0 4px; }
.figure h3 { font-size: 18px; font-weight: 700; margin: 0 0 12px; letter-spacing: -0.01em; }
.chart { width: 100%; height: auto; display: block; }
.nodata { color: var(--muted); font-style: italic; }

/* legend + callouts */
.legend { display: flex; gap: 22px; flex-wrap: wrap; font-size: 13px; color: var(--muted); margin: 2px 0 0; }
.legend .sw { display: inline-block; width: 12px; height: 12px; margin-right: 7px; vertical-align: -1px; }
.callout {
  border-left: 3px solid var(--amber); background: var(--panel-2);
  padding: 16px 20px; margin: 0 0 26px; font-size: 15px;
}
.callout strong { font-weight: 700; }
.callout.red { border-left-color: var(--red); background: rgba(248, 81, 73, 0.07); }
.callout.green { border-left-color: var(--green); background: rgba(63, 185, 80, 0.07); }

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; align-items: start; }
.rank { font-weight: 800; color: var(--faint); width: 34px; font-variant-numeric: tabular-nums; }

/* footer */
footer { border-top: 4px solid var(--rule); padding-top: 18px; margin-top: 20px; }
footer p { font-size: 12.5px; color: var(--muted); margin: 0 0 8px; max-width: 700px; }
footer strong { color: var(--ink); }
.meta { font-family: var(--mono); font-size: 12px; }

@media (max-width: 720px) {
  .stats { grid-template-columns: 1fr 1fr; }
  .grid-2 { grid-template-columns: 1fr; }
  h1 { font-size: 32px; }
  .wrap { padding: 36px 18px 60px; }
}
@media print {
  body { background: #fff; color: #111; }
  .wrap { max-width: none; padding: 0; }
  .stat, .figure, table, .callout { background: #fff; border-color: #ddd; }
  th, td { border-color: #ddd; }
  tbody tr:hover { background: #fff; }
  h1, h2, .figure h3, footer strong { color: #111; }
  .lede, .dek, .stat .cap, .stat .sub, caption, .figure figcaption, footer p { color: #444; }
  .chart { filter: invert(1) hue-rotate(180deg); }
  .masthead { border-top-color: #111; }
  .sec-rule { border-top-color: #111; }
  footer { border-top-color: #111; }
  section, .figure, .callout { break-inside: avoid; }
  .stats { grid-template-columns: repeat(4, 1fr); }
}"""


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


# ---------- helpers for the HTML report ----------

def _fmt_hours(h):
    return f"{h:g}" if h is not None else "-"


def _breaches(resolved, pct):
    if pct is None or resolved is None:
        return "-"
    met = round(resolved * pct / 100)
    return resolved - met


def _sla_target_label(priority):
    hours = DEFAULT_SLA_HOURS.get(priority)
    return f"{hours:g}h" if hours is not None else "-"


def _hour_name(h):
    if h == 0:
        return "midnight"
    if h == 12:
        return "noon"
    if h < 12:
        return f"{h} am"
    return f"{h - 12} pm"


def _week_label(tag):
    return _week_start(tag).strftime("%b %d")


def _week_start(tag):
    year, week = tag.split("-W")
    return datetime.fromisocalendar(int(year), int(week), 1).date()


def _ordered_priorities(report):
    present = [p for p in PRIORITY_ORDER if p in report.resolution_by_priority]
    present += [p for p in report.resolution_by_priority if p not in PRIORITY_ORDER]
    return present


def write_html_report(report, path):
    path = Path(path)
    start, end = report.date_range
    date_title = f"{start:%B} {start.day} to {end:%B} {end.day}, {end.year}"
    generated = datetime.now().strftime("%B %d, %Y")

    priorities = _ordered_priorities(report)
    sla_items = [(p, report.sla_compliance_by_priority.get(p)) for p in priorities]
    sla_colors = [sla_band(pct) for _, pct in sla_items]
    sla_chart = hbars(
        [(p, pct if pct is not None else 0) for p, pct in sla_items],
        colors=sla_colors, suffix="%", ticks=[0, 25, 50, 75, 100], value_bold=True)

    sla_rows = []
    for p, pct in sla_items:
        stats = report.resolution_by_priority[p]
        met = round(stats["resolved_count"] * pct / 100) if pct is not None else "-"
        pct_str = f"{pct:g}%" if pct is not None else "-"
        sla_rows.append(
            f'<tr><td><span class="dot" style="background:{sla_band(pct)}"></span>{p}</td>'
            f'<td class="num">{_sla_target_label(p)}</td>'
            f'<td class="num">{stats["resolved_count"]}</td>'
            f'<td class="num">{met}</td>'
            f'<td class="num">{_breaches(stats["resolved_count"], pct)}</td>'
            f'<td class="num"><strong>{pct_str}</strong></td></tr>')
    sla_rows_html = "\n".join(sla_rows)

    avg_items = [(p, report.resolution_by_priority[p]["avg_hours"] or 0) for p in priorities]
    res_chart = hbars(avg_items, suffix="h", ticks=[0, 2, 4, 6, 8], value_bold=True)

    res_rows = []
    for p in priorities:
        s = report.resolution_by_priority[p]
        res_rows.append(
            f"<tr><td>{p}</td><td class=\"num\">{s['count']}</td>"
            f"<td class=\"num\">{s['resolved_count']}</td>"
            f"<td class=\"num\">{_fmt_hours(s['avg_hours'])}h</td>"
            f"<td class=\"num\">{_fmt_hours(s['median_hours'])}h</td></tr>")
    res_rows_html = "\n".join(res_rows)

    full_weeks = [
        (tag, count) for tag, count in report.tickets_per_week
        if _week_start(tag) >= start.date()
        and _week_start(tag) + timedelta(days=6) <= end.date()
    ] or list(report.tickets_per_week)
    weeks = [_week_label(w) for w, _ in full_weeks]
    week_counts = [c for _, c in full_weeks]
    trend_chart = weekly_trend(weeks, week_counts)
    peak_idx = max(range(len(week_counts)), key=lambda i: week_counts[i])
    peak_week = weeks[peak_idx]
    peak_week_count = week_counts[peak_idx]

    top_cats = report.volume_by_category[:8]
    cat_rows = []
    for i, (cat, count) in enumerate(top_cats, 1):
        share = 100.0 * count / report.total_tickets if report.total_tickets else 0
        cat_rows.append(
            f'<tr><td class="rank">{i}</td><td>{charts._esc(cat)}</td>'
            f'<td class="num">{count}</td><td class="num">{share:.1f}%</td></tr>')
    cat_rows_html = "\n".join(cat_rows)

    dow_short = [("Mon", report.volume_by_day_of_week["Monday"]),
                 ("Tue", report.volume_by_day_of_week["Tuesday"]),
                 ("Wed", report.volume_by_day_of_week["Wednesday"]),
                 ("Thu", report.volume_by_day_of_week["Thursday"]),
                 ("Fri", report.volume_by_day_of_week["Friday"]),
                 ("Sat", report.volume_by_day_of_week["Saturday"]),
                 ("Sun", report.volume_by_day_of_week["Sunday"])]
    dow_chart = hbars(dow_short, label_w=64, ticks=[0, 60, 120], show_values=False)
    busiest_day = max(dow_short, key=lambda kv: kv[1])[0]
    busiest_day_count = max(dow_short, key=lambda kv: kv[1])[1]
    busiest_day_full = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday",
                        "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"}[busiest_day]

    peak_hour = max(range(24), key=lambda h: report.volume_by_hour.get(h, 0))
    hour_chart = hour_strip(report.volume_by_hour,
                            peak_label=f"{report.volume_by_hour.get(peak_hour, 0):g} at {_hour_name(peak_hour)}")

    aging_items = list(report.backlog_aging.items())
    aging_colors = ["#3a4654", "#4d5b6e", charts.AMBER, charts.RED]
    aging_chart = hbars(aging_items, colors=aging_colors, value_bold=True,
                        ticks=[0, aging_items[-1][1] // 3, 2 * aging_items[-1][1] // 3, aging_items[-1][1]])
    old7 = report.backlog_aging.get("7+ days", 0)

    # headline numbers
    sla_overall = report.sla_compliance_overall_pct
    sla_num = f"{sla_overall:g}<small>%</small>" if sla_overall is not None else "-"
    sla_class = "good" if (sla_overall or 0) >= 95 else ("warn" if (sla_overall or 0) >= 85 else "bad")
    med = report.median_resolution_hours
    med_num = f"{med:g}<small>h</small>" if med is not None else "-"
    avg = report.avg_resolution_hours
    med_sub = f"Average {avg:g}h across resolved tickets" if avg is not None else ""
    high_stats = report.resolution_by_priority.get("High", {})
    high_pct = report.sla_compliance_by_priority.get("High")
    high_breaches = _breaches(high_stats.get("resolved_count"), high_pct)
    high_sub = f"{high_pct:g}% compliance on High priority" if high_pct is not None else ""
    backlog_sub = f"{old7} older than a week" if old7 else ""

    sla_targets_note = ", ".join(f"{p} {_sla_target_label(p)}" for p in priorities)

    body = f"""
<div class="wrap">

  <header class="masthead">
    <div class="row">
      <svg class="mark" width="44" height="44" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <rect x="4" y="8" width="36" height="28" rx="3" fill="none" stroke="#e8eef4" stroke-width="2.5"/>
        <line x1="26" y1="8" x2="26" y2="36" stroke="#e8eef4" stroke-width="2" stroke-dasharray="4 3"/>
        <line x1="11" y1="16" x2="21" y2="16" stroke="#e8eef4" stroke-width="2.5"/>
        <line x1="11" y1="22" x2="21" y2="22" stroke="#e8eef4" stroke-width="2.5"/>
        <line x1="11" y1="28" x2="18" y2="28" stroke="#e8eef4" stroke-width="2.5"/>
      </svg>
      <div>
        <p class="eyebrow">Helpdesk Operations Review</p>
        <h1>Ticket Report, {date_title}</h1>
      </div>
    </div>
    <p class="dek">{report.total_tickets} tickets opened or carried through the period. Prepared for the weekly ops review: what we met, where it hurt, and what needs staffing.</p>
    <hr class="rule">
  </header>

  <section>
    <p class="sec-label">The short version</p>
    <h2>We are meeting SLA, except where it matters most.</h2>
    <hr class="sec-rule">
    <p class="lede">Of {report.total_tickets} tickets, {report.resolved_count} were resolved and {sla_overall:g}% beat their SLA target. High priority work is the weak spot at {high_pct:g}% compliance, and {old7} open tickets have been waiting more than a week.</p>
    <div class="stats">
      <div class="stat">
        <p class="num {sla_class}">{sla_num}</p>
        <p class="cap">SLA compliance</p>
        <p class="sub">Across all resolved tickets</p>
      </div>
      <div class="stat">
        <p class="num">{med_num}</p>
        <p class="cap">Median resolution</p>
        <p class="sub">{med_sub}</p>
      </div>
      <div class="stat">
        <p class="num {'warn' if old7 > 10 else ''}">{report.open_count}</p>
        <p class="cap">Open tickets</p>
        <p class="sub">{backlog_sub}</p>
      </div>
      <div class="stat">
        <p class="num {'bad' if isinstance(high_breaches, int) and high_breaches > 5 else ''}">{high_breaches}</p>
        <p class="cap">High priority breaches</p>
        <p class="sub">{high_sub}</p>
      </div>
    </div>
  </section>

  <section>
    <p class="sec-label">Performance</p>
    <h2>SLA, priority by priority</h2>
    <hr class="sec-rule">
    <p class="lede">Low and Medium tickets never missed. Critical slipped once, to 92.9%. High is the problem: {high_breaches} of {high_stats.get('resolved_count')} resolved High tickets breached the {_sla_target_label('High')} target.</p>
    <figure class="figure">
      <h3>SLA compliance by priority</h3>
      {sla_chart}
      <figcaption>Share of resolved tickets closed inside the SLA target for their priority.</figcaption>
    </figure>
    <div class="legend" style="margin-bottom: 18px;">
      <span><span class="sw" style="background:{charts.GREEN}"></span>95% or better</span>
      <span><span class="sw" style="background:{charts.AMBER}"></span>85 to 94%</span>
      <span><span class="sw" style="background:{charts.RED}"></span>below 85%</span>
    </div>
    <table>
      <caption>Resolved, met, and breached counts per priority.</caption>
      <tr><th>Priority</th><th class="num">SLA target</th><th class="num">Resolved</th><th class="num">Met</th><th class="num">Breached</th><th class="num">Compliance</th></tr>
      {sla_rows_html}
    </table>
  </section>

  <section>
    <p class="sec-label">Speed</p>
    <h2>How long tickets take</h2>
    <hr class="sec-rule">
    <p class="lede">Median resolution across the queue is {med:g} hours. High priority tickets average {report.resolution_by_priority.get('High', {}).get('avg_hours')} hours, which is where the breaches come from.</p>
    <figure class="figure">
      <h3>Average resolution time by priority</h3>
      {res_chart}
      <figcaption>Average hours from creation to resolution, resolved tickets only.</figcaption>
    </figure>
    <table>
      <caption>Ticket counts and resolution times by priority.</caption>
      <tr><th>Priority</th><th class="num">Tickets</th><th class="num">Resolved</th><th class="num">Avg hours</th><th class="num">Median hours</th></tr>
      {res_rows_html}
    </table>
  </section>

  <section>
    <p class="sec-label">Demand</p>
    <h2>Where the volume comes from</h2>
    <hr class="sec-rule">
    <p class="lede">The busiest week started {peak_week}, with {peak_week_count} tickets. {top_cats[0][0]} leads every category with {top_cats[0][1]} tickets, close to one in five of everything that came in.</p>
    <figure class="figure">
      <h3>Tickets per week</h3>
      {trend_chart}
      <figcaption>Tickets created per ISO week across the period. Partial weeks at the edges are excluded.</figcaption>
    </figure>
    <div class="grid-2">
      <div>
        <table>
          <caption>Top categories by ticket count.</caption>
          <tr><th></th><th>Category</th><th class="num">Tickets</th><th class="num">Share</th></tr>
          {cat_rows_html}
        </table>
      </div>
      <figure class="figure" style="margin:0;">
        <h3>Tickets by day of week</h3>
        {dow_chart}
        <figcaption>Weekday load is even; weekends are near zero.</figcaption>
      </figure>
    </div>
    <div class="callout green" style="margin-top: 18px;">
      <strong>Staffing read.</strong> {busiest_day_full} was the busiest day with {busiest_day_count} tickets, and almost nothing lands on weekends. Volume peaks at {_hour_name(peak_hour)}, which is where coverage has to be.
    </div>
    <figure class="figure">
      <h3>Tickets by hour of day</h3>
      {hour_chart}
      <figcaption>When tickets arrive, in the local timezone of the export. The highlighted bar marks the peak hour.</figcaption>
    </figure>
  </section>

  <section>
    <p class="sec-label">Backlog</p>
    <h2>What is still open</h2>
    <hr class="sec-rule">
    <p class="lede">{report.open_count} tickets are open. The {old7} that are older than a week deserve a triage pass: they are the ones the director will ask about.</p>
    <figure class="figure">
      <h3>Open tickets by age</h3>
      {aging_chart}
      <figcaption>Age of every open ticket, measured from creation to the end of the period.</figcaption>
    </figure>
    <div class="callout red">
      <strong>Watch item.</strong> {old7} tickets have been open longer than a week. Assign an owner and a date to each before the next review.
    </div>
  </section>

  <footer>
    <p><strong>Methodology.</strong> SLA targets: {sla_targets_note}. Compliance is measured on resolved tickets only; a ticket meets SLA when its resolution time is within the target for its priority. Backlog age is measured to the end of the period.</p>
    <p>Report generated {generated} from the ticket export. Charts are inline SVG; this file works offline.</p>
  </footer>

</div>
"""

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Helpdesk Operations Review - {date_title}</title>
<style>{CSS}</style>
</head>
<body>
{body}
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")
