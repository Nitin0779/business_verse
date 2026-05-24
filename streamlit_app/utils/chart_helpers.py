"""
BusinessVerse - Chart Helper Utilities
Plotly chart factory functions with consistent business styling.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ─── Theme Colors ─────────────────────────────────────────────────────────────
COLORS = {
    "primary":    "#2563EB",   # Blue
    "secondary":  "#0EA5E9",   # Sky blue
    "success":    "#10B981",   # Green
    "warning":    "#F59E0B",   # Amber
    "danger":     "#EF4444",   # Red
    "neutral":    "#6B7280",   # Gray
    "background": "#F8FAFC",   # Light background
    "card":       "#FFFFFF",
    "text":       "#1E293B",
    "border":     "#E2E8F0",
}

PALETTE = [
    "#2563EB", "#0EA5E9", "#10B981", "#F59E0B",
    "#EF4444", "#8B5CF6", "#EC4899", "#14B8A6",
    "#F97316", "#06B6D4"
]

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, Segoe UI, sans-serif", color="#1E293B", size=13),
    margin=dict(l=10, r=10, t=40, b=10),
    hoverlabel=dict(bgcolor="white", bordercolor="#E2E8F0", font_size=13),
)

LEGEND_H = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=12))
LEGEND_V = dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.01, font=dict(size=12))


def apply_layout(fig, title="", height=380):
    """Apply consistent layout to any Plotly figure."""
    fig.update_layout(
        **CHART_LAYOUT,
        legend=LEGEND_H,
        title=dict(text=title, font=dict(size=16, color="#1E293B"), x=0),
        height=height,
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=12)),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", zeroline=False, tickfont=dict(size=12)),
    )
    return fig


def line_chart(df, x, y, title="", color=None, color_col=None, height=380):
    """Smooth line chart with optional multi-series."""
    if color_col:
        fig = px.line(df, x=x, y=y, color=color_col, color_discrete_sequence=PALETTE)
    else:
        fig = px.line(df, x=x, y=y, color_discrete_sequence=[color or COLORS["primary"]])
    fig.update_traces(line=dict(width=2.5), mode="lines+markers",
                      marker=dict(size=5, opacity=0.8))
    return apply_layout(fig, title, height)


def bar_chart(df, x, y, title="", color=None, orientation="v", height=380, text=None):
    """Clean bar chart."""
    kwargs = dict(x=x, y=y, orientation=orientation,
                  color_discrete_sequence=[color or COLORS["primary"]])
    if text:
        kwargs["text"] = text
    fig = px.bar(df, **kwargs)
    fig.update_traces(marker_line_width=0, textposition="outside" if text else None)
    return apply_layout(fig, title, height)


def multi_bar_chart(df, x, y_list, names, title="", height=380):
    """Grouped bar chart with multiple series."""
    fig = go.Figure()
    for y, name, color in zip(y_list, names, PALETTE):
        fig.add_trace(go.Bar(x=df[x], y=df[y], name=name,
                              marker_color=color, marker_line_width=0))
    fig.update_layout(barmode="group")
    return apply_layout(fig, title, height)


def area_chart(df, x, y, title="", color=None, height=380):
    """Filled area chart for trends."""
    fig = px.area(df, x=x, y=y, color_discrete_sequence=[color or COLORS["primary"]])
    fig.update_traces(line=dict(width=2), fillcolor=f"rgba(37,99,235,0.12)")
    return apply_layout(fig, title, height)


def pie_chart(df, names, values, title="", height=360, hole=0.45):
    """Donut pie chart."""
    fig = px.pie(df, names=names, values=values,
                 color_discrete_sequence=PALETTE, hole=hole)
    fig.update_traces(
        textposition="inside", textinfo="percent+label",
        marker=dict(line=dict(color="white", width=2))
    )
    fig.update_layout(
        **CHART_LAYOUT,
        legend=LEGEND_V,
        title=dict(text=title, font=dict(size=16, color="#1E293B"), x=0),
        height=height,
        showlegend=True,
    )
    return fig


def scatter_chart(df, x, y, color_col=None, size_col=None, title="", height=400):
    """Scatter plot with optional color and size encoding."""
    kwargs = dict(x=x, y=y, color_discrete_sequence=PALETTE,
                  opacity=0.75)
    if color_col:
        kwargs["color"] = color_col
    if size_col:
        kwargs["size"] = size_col
    fig = px.scatter(df, **kwargs)
    return apply_layout(fig, title, height)


def heatmap_chart(z, x, y, title="", height=400):
    """Heatmap chart."""
    fig = go.Figure(go.Heatmap(
        z=z, x=x, y=y,
        colorscale=[[0, "#EFF6FF"], [1, "#1D4ED8"]],
        showscale=True
    ))
    return apply_layout(fig, title, height)


def kpi_delta_indicator(value, reference, title, prefix="$", suffix=""):
    """Small indicator figure for KPI delta visualization."""
    fig = go.Figure(go.Indicator(
        mode="number+delta",
        value=value,
        delta=dict(reference=reference, valueformat=".1f",
                   increasing=dict(color=COLORS["success"]),
                   decreasing=dict(color=COLORS["danger"])),
        number=dict(prefix=prefix, suffix=suffix, font=dict(size=34, color=COLORS["text"])),
        title=dict(text=title, font=dict(size=14, color=COLORS["neutral"])),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=30, b=10),
        height=120,
    )
    return fig
