"""Hand-rolled inline-SVG charts styled for the printed operations review.

Thin rules, ink-on-paper type, data colors reserved for meaning.
No third-party libraries, no CDN assets.
"""

from __future__ import annotations

INK = "#241e14"
MUTED = "#7c7261"
RULE = "#ded4ba"
GREEN = "#2a7a44"
AMBER = "#b07508"
RED = "#b23427"
NEUTRAL = "#4a4136"

SANS = "'Liberation Sans','DejaVu Sans',Arial,sans-serif"


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _truncate(s, n):
    s = str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def hbars(items, *, colors=None, suffix="", ticks=None, width=680, label_w=200,
          bar_h=18, gap=14, label_size=13, value_bold=False, show_values=True):
    """Horizontal bar chart: labels left, thin gridlines, value labels right of bars."""
    if not items:
        return '<p class="nodata">No data</p>'
    values = [v for _, v in items]
    max_value = max(values) or 1
    if colors is None:
        colors = NEUTRAL
    if isinstance(colors, str):
        colors = [colors] * len(items)
    if ticks is None:
        ticks = [max_value]
    plot_w = width - label_w - 64
    top = 26
    height = top + len(items) * (bar_h + gap) + 6
    parts = [f'<svg viewBox="0 0 {width} {height}" class="chart" role="img" xmlns="http://www.w3.org/2000/svg">']
    for t in ticks:
        x = label_w + (t / max_value) * plot_w
        parts.append(f'<line x1="{x:.1f}" y1="{top - 10}" x2="{x:.1f}" y2="{height - 4}" stroke="{RULE}" stroke-width="1"/>')
        parts.append(f'<text x="{x:.1f}" y="{top - 16}" text-anchor="middle" font-size="10.5" fill="{MUTED}" font-family={SANS}>{t:g}</text>')
    for i, (label, value) in enumerate(items):
        y = top + i * (bar_h + gap)
        bar_len = max((value / max_value) * plot_w, 2) if value else 0
        parts.append(
            f'<text x="{label_w - 12}" y="{y + bar_h * 0.72:.1f}" text-anchor="end" '
            f'font-size="{label_size}" fill="{INK}" font-family={SANS}>{_esc(_truncate(label, 26))}</text>')
        if bar_len:
            parts.append(
                f'<rect x="{label_w}" y="{y}" width="{bar_len:.1f}" height="{bar_h}" '
                f'fill="{colors[i % len(colors)]}"/>')
        if show_values:
            fw = "700" if value_bold else "400"
            parts.append(
                f'<text x="{label_w + bar_len + 10:.1f}" y="{y + bar_h * 0.72:.1f}" '
                f'font-size="12.5" font-weight="{fw}" fill="{INK}" font-family={SANS}>{value:g}{suffix}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def weekly_trend(weeks, counts, *, width=680, height=260):
    """Thin line + washed area over weekly ticket counts."""
    if not weeks:
        return '<p class="nodata">No data</p>'
    n = len(weeks)
    ml, mr, mt, mb = 44, 16, 22, 34
    pw, ph = width - ml - mr, height - mt - mb
    vmax = max(counts) or 1
    step = (vmax + 3) // 4 or 1
    ticks = [i * step for i in range(1, 5) if i * step <= vmax * 1.08]
    if not ticks:
        ticks = [vmax]
    y_max = max(ticks) * 1.08
    xs = [ml + (i / (n - 1)) * pw if n > 1 else ml + pw / 2 for i in range(n)]
    ys = [mt + ph - (c / y_max) * ph for c in counts]
    parts = [f'<svg viewBox="0 0 {width} {height}" class="chart" role="img" xmlns="http://www.w3.org/2000/svg">']
    for t in ticks:
        y = mt + ph - (t / y_max) * ph
        parts.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{width - mr}" y2="{y:.1f}" stroke="{RULE}" stroke-width="1"/>')
        parts.append(f'<text x="{ml - 10}" y="{y + 4:.1f}" text-anchor="end" font-size="10.5" fill="{MUTED}" font-family={SANS}>{t:g}</text>')
    line = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    parts.append(f'<path d="{line} L{xs[-1]:.1f},{mt + ph:.1f} L{xs[0]:.1f},{mt + ph:.1f} Z" fill="{INK}" opacity="0.07"/>')
    parts.append(f'<path d="{line}" fill="none" stroke="{INK}" stroke-width="2"/>')
    for x, y, c in zip(xs, ys, counts):
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{INK}"><title>{c:g} tickets</title></circle>')
    every = max(1, -(-n // 7))
    for i, w in enumerate(weeks):
        if i % every == 0 or i == n - 1:
            anchor = "end" if i == n - 1 and i % every != 0 else ("start" if i == 0 else "middle")
            x = xs[i]
            parts.append(f'<text x="{x:.1f}" y="{height - 10}" text-anchor="{anchor}" font-size="10.5" fill="{MUTED}" font-family={SANS}>{_esc(w)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def hour_strip(hours, *, width=680, height=200, peak_label=None):
    """24 thin vertical bars: ticket volume by hour of day, for staffing reads."""
    counts = [hours.get(h, 0) for h in range(24)]
    vmax = max(counts) or 1
    ml, mr, mt, mb = 44, 12, 18, 30
    pw, ph = width - ml - mr, height - mt - mb
    slot = pw / 24
    bw = max(slot - 5, 2)
    peak = max(range(24), key=lambda h: counts[h])
    labels = {0: "12a", 6: "6a", 12: "12p", 18: "6p", 23: "11p"}
    parts = [f'<svg viewBox="0 0 {width} {height}" class="chart" role="img" xmlns="http://www.w3.org/2000/svg">']
    for t in (0, vmax // 2, vmax):
        y = mt + ph - (t / vmax) * ph if vmax else mt + ph
        parts.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{width - mr}" y2="{y:.1f}" stroke="{RULE}" stroke-width="1"/>')
        parts.append(f'<text x="{ml - 10}" y="{y + 4:.1f}" text-anchor="end" font-size="10.5" fill="{MUTED}" font-family={SANS}>{t:g}</text>')
    for h, c in enumerate(counts):
        bh = (c / vmax) * ph
        x = ml + h * slot + (slot - bw) / 2
        fill = INK if h == peak else NEUTRAL
        opacity = "1" if h == peak else "0.55"
        parts.append(
            f'<rect x="{x:.1f}" y="{mt + ph - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
            f'fill="{fill}" opacity="{opacity}"><title>{h}:00, {c:g} tickets</title></rect>')
    for h, lab in labels.items():
        x = ml + h * slot + slot / 2
        anchor = "start" if h == 0 else ("end" if h == 23 else "middle")
        parts.append(f'<text x="{x:.1f}" y="{height - 10}" text-anchor="{anchor}" font-size="10.5" fill="{MUTED}" font-family={SANS}>{lab}</text>')
    parts.append(f'<text x="{ml + peak * slot + slot / 2:.1f}" y="{mt + ph - (counts[peak] / vmax) * ph - 8:.1f}" '
                 f'text-anchor="middle" font-size="11" font-weight="700" fill="{INK}" font-family={SANS}>{_esc(peak_label or f"{counts[peak]:g} at {peak}:00")}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def sla_band(pct):
    if pct is None:
        return "#9a917e"
    if pct >= 95:
        return GREEN
    if pct >= 85:
        return AMBER
    return RED
