"""Tiny, dependency-free SVG bar-chart renderer."""

from __future__ import annotations

_PALETTE = ["#2563eb", "#7c3aed", "#059669", "#d97706", "#dc2626", "#0891b2", "#4338ca", "#65a30d"]


def bar_chart_svg(data, *, width=640, bar_height=26, gap=10, title="", value_suffix=""):
    if not data:
        return "<p><em>No data</em></p>"
    max_value = max(v for _, v in data) or 1
    label_col = 180
    chart_width = width - label_col - 60
    top_margin = 36 if title else 8
    height = top_margin + len(data) * (bar_height + gap)
    parts = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" font-family="Segoe UI, Arial, sans-serif">']
    if title:
        parts.append(f'<text x="0" y="20" font-size="15" font-weight="600" fill="#111827">{_esc(title)}</text>')
    for i, (label, value) in enumerate(data):
        y = top_margin + i * (bar_height + gap)
        bar_len = (value / max_value) * chart_width if max_value else 0
        color = _PALETTE[i % len(_PALETTE)]
        parts.append(f'<text x="0" y="{y + bar_height * 0.7:.0f}" font-size="13" fill="#374151">{_esc(_truncate(label, 24))}</text>')
        parts.append(f'<rect x="{label_col}" y="{y}" width="{bar_len:.1f}" height="{bar_height}" rx="4" fill="{color}" />')
        value_label = f"{value:g}{value_suffix}"
        parts.append(f'<text x="{label_col + bar_len + 8:.1f}" y="{y + bar_height * 0.7:.0f}" font-size="12" fill="#111827">{_esc(value_label)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def _truncate(s, n):
    return s if len(s) <= n else s[: n - 1] + "…"


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
