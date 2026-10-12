"""
visualization.py
================
All chart-building functions using Plotly (interactive) and
Matplotlib/Seaborn (static exports).
"""

import logging
from typing import Dict, List, Optional

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns

from modules.outlier_engine import RATIO_LABELS, HIGH_IS_BAD
from modules.benchmark_core import PILLARS

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# THEME  —  Dark Abyss Palette (built from #003B38)
# ─────────────────────────────────────────────────────────────────────────────
DARK_BG   = "#001f1e"   # Abyss  — page / paper background
CARD_BG   = "#002623"   # Depths — plot area / card background
SURFACE   = "#0d2e2b"   # Surface — inputs, hover areas
ACCENT    = "#00c4a7"   # Primary accent — CTAs, highlights
SECONDARY = "#5a8a85"   # Secondary accent — icons, section text
GREEN     = "#00c4a7"   # Positive signals (same as accent)
RED       = "#f85149"   # Negative signals
YELLOW    = "#d29922"   # Warning / neutral signals
TEXT      = "#d4f0ec"   # Bright text — headings, values
BODY_TEXT = "#7ab8b2"   # Body text — nav, body copy
MUTED     = "#3d6e69"   # Muted text — labels, captions
GRID      = "#1a3a37"   # Border — dividers, gridlines
PRIMARY   = "#003b38"   # Primary brand — buttons, key UI

PLOTLY_TEMPLATE = dict(
    layout=go.Layout(
        paper_bgcolor=DARK_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=TEXT, family="Google Sans, sans-serif"),
        title_font=dict(color=TEXT, size=15),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
        legend=dict(bgcolor=CARD_BG, bordercolor=GRID),
        colorway=[ACCENT, SECONDARY, YELLOW, RED, "#5a8a85", "#7ab8b2"],
    )
)


def _apply_theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        paper_bgcolor=DARK_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=TEXT, family="Google Sans, sans-serif"),
        title_font=dict(color=TEXT, size=15),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID)
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# 1. RATIO DISTRIBUTION BOX PLOTS
# ─────────────────────────────────────────────────────────────────────────────

def ratio_boxplot(
    ratio_df: pd.DataFrame,
    ratios: Optional[List[str]] = None,
    outlier_tickers: Optional[List[str]] = None,
) -> go.Figure:
    """Box plots for ratio distributions across the peer group."""
    if ratios is None:
        ratios = [c for c in ratio_df.columns if c in RATIO_LABELS][:8]

    fig = make_subplots(
        rows=2, cols=4,
        subplot_titles=[RATIO_LABELS.get(r, r) for r in ratios],
        vertical_spacing=0.15,
        horizontal_spacing=0.08,
    )

    for i, ratio in enumerate(ratios):
        row, col = divmod(i, 4)
        row += 1; col += 1
        if ratio not in ratio_df.columns:
            continue
        series = ratio_df[ratio].dropna()

        # Box trace
        fig.add_trace(
            go.Box(
                y=series.values,
                name=RATIO_LABELS.get(ratio, ratio),
                boxpoints="all",
                jitter=0.4,
                pointpos=-1.6,
                marker=dict(size=6, color=ACCENT, opacity=0.7),
                line=dict(color=ACCENT),
                fillcolor=CARD_BG,
                showlegend=False,
            ),
            row=row, col=col,
        )

        # Highlight outlier tickers
        if outlier_tickers:
            out_vals = ratio_df.loc[ratio_df.index.isin(outlier_tickers), ratio].dropna()
            if not out_vals.empty:
                fig.add_trace(
                    go.Scatter(
                        y=out_vals.values,
                        x=[0] * len(out_vals),
                        mode="markers+text",
                        text=out_vals.index.tolist(),
                        textposition="top center",
                        marker=dict(color=RED, size=9, symbol="x"),
                        showlegend=False,
                    ),
                    row=row, col=col,
                )

    fig.update_layout(
        title="Ratio Distribution — Peer Group",
        height=550,
    )
    return _apply_theme(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 2. HEATMAP — RATIO MATRIX
# ─────────────────────────────────────────────────────────────────────────────

def ratio_heatmap(ratio_df: pd.DataFrame, ratios: Optional[List[str]] = None) -> go.Figure:
    """Heatmap of ratio values (rows = tickers, cols = ratios), z-scored."""
    from modules.outlier_engine import HIGH_IS_BAD

    if ratios is None:
        ratios = [c for c in ratio_df.columns if c in RATIO_LABELS]

    sub = ratio_df[ratios].copy()
    # Z-score each column for comparable colouring
    z_df = (sub - sub.mean()) / sub.std().replace(0, 1)
    # Flip sign for "lower is better" ratios so green always = good
    for col in z_df.columns:
        if col in HIGH_IS_BAD:
            z_df[col] = -z_df[col]
    z_df = z_df.clip(-3, 3)

    labels = [RATIO_LABELS.get(r, r) for r in ratios]

    fig = go.Figure(
        data=go.Heatmap(
            z=z_df.values,
            x=labels,
            y=z_df.index.tolist(),
            colorscale=[
                [0.0, RED],
                [0.5, CARD_BG],
                [1.0, GREEN],
            ],
            zmid=0,
            text=sub.round(2).values,
            texttemplate="%{text}",
            colorbar=dict(
                title=dict(text="Z-Score", font=dict(color=TEXT)),
                tickfont=dict(color=TEXT),
            ),
        )
    )
    fig.update_layout(
        title="Ratio Heatmap (Latest Quarter Z-Score Normalised)",
        xaxis=dict(tickangle=-35),
        height=max(400, 40 * len(z_df)),
    )
    return _apply_theme(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 3. RADAR CHART — COMPANY PROFILE
# ─────────────────────────────────────────────────────────────────────────────

def radar_chart(
    ratio_df: pd.DataFrame,
    tickers: List[str],
    ratios: Optional[List[str]] = None,
) -> go.Figure:
    """Radar/spider chart comparing selected companies."""
    if ratios is None:
        ratios = [
            "gross_margin", "operating_margin", "net_margin",
            "roe", "current_ratio", "debt_to_equity",
            "asset_turnover", "fcf_margin",
        ]
    ratios = [r for r in ratios if r in ratio_df.columns]
    if not ratios:
        return go.Figure()

    # Percentile-rank each ratio for radar (0-100)
    ranks = ratio_df[ratios].rank(pct=True) * 100
    labels = [RATIO_LABELS.get(r, r) for r in ratios]

    colors = [ACCENT, SECONDARY, YELLOW, RED, "#7ab8b2"]
    fig = go.Figure()

    for i, ticker in enumerate(tickers):
        if ticker not in ranks.index:
            continue
        vals = ranks.loc[ticker, ratios].tolist()
        vals += vals[:1]   # close polygon
        lbl = labels + labels[:1]
        fig.add_trace(
            go.Scatterpolar(
                r=vals,
                theta=lbl,
                fill="toself",
                name=ticker,
                line=dict(color=colors[i % len(colors)], width=2),
                fillcolor=colors[i % len(colors)],
                opacity=0.25,
            )
        )

    fig.update_layout(
        polar=dict(
            bgcolor=CARD_BG,
            angularaxis=dict(gridcolor=GRID, tickfont=dict(color=TEXT, size=10)),
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor=GRID,
                tickfont=dict(color=TEXT, size=8),
            ),
        ),
        showlegend=True,
        title="Financial Profile — Percentile Radar",
        height=480,
    )
    return _apply_theme(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 4. OUTLIER SCATTER PLOT
# ─────────────────────────────────────────────────────────────────────────────

def outlier_scatter(outlier_df: pd.DataFrame) -> go.Figure:
    """Bubble scatter: severity_score vs deviation_pct, coloured by direction."""
    if outlier_df.empty:
        return go.Figure()

    df = outlier_df.copy()
    df["color"] = df["is_positive_outlier"].map({True: GREEN, False: RED})
    df["symbol"] = df["is_positive_outlier"].map({True: "triangle-up", False: "triangle-down"})
    df["hover"] = (
        df["ticker"] + "<br>" +
        df["ratio_label"] + "<br>" +
        "Value: " + df["value"].astype(str) + "<br>" +
        "Severity: " + df["severity_score"].astype(str)
    )

    fig = go.Figure()
    for positive, group in df.groupby("is_positive_outlier"):
        label = "Positive Outlier" if positive else "Negative Outlier"
        color = GREEN if positive else RED
        fig.add_trace(
            go.Scatter(
                x=group["deviation_pct"],
                y=group["severity_score"],
                mode="markers+text",
                text=group["ticker"],
                textposition="top center",
                textfont=dict(size=9, color=TEXT),
                marker=dict(
                    size=group["severity_score"].clip(5, 25) * 5,
                    color=color,
                    opacity=0.8,
                    line=dict(color=TEXT, width=1),
                ),
                name=label,
                hovertext=group["hover"],
                hoverinfo="text",
            )
        )

    fig.update_layout(
        title="Outlier Map — Deviation vs Severity",
        xaxis_title="Deviation from Sector Median (%)",
        yaxis_title="Severity Score",
        height=480,
    )
    return _apply_theme(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 5. CORRELATION MATRIX
# ─────────────────────────────────────────────────────────────────────────────

def correlation_heatmap(ratio_df: pd.DataFrame) -> go.Figure:
    """Interactive correlation matrix of financial ratios."""
    ratio_cols = [c for c in ratio_df.columns if c in RATIO_LABELS]
    if not ratio_cols:
        return go.Figure()

    corr = ratio_df[ratio_cols].corr()
    labels = [RATIO_LABELS.get(c, c) for c in ratio_cols]

    fig = go.Figure(
        data=go.Heatmap(
            z=corr.values,
            x=labels,
            y=labels,
            colorscale=[
                [0.0, RED], [0.5, CARD_BG], [1.0, GREEN],
            ],
            zmid=0,
            zmin=-1, zmax=1,
            text=corr.round(2).values,
            texttemplate="%{text}",
            colorbar=dict(title=dict(text="r", font=dict(color=TEXT)), tickfont=dict(color=TEXT)),
        )
    )
    fig.update_layout(
        title="Ratio Correlation Matrix",
        xaxis=dict(tickangle=-40),
        height=600,
    )
    return _apply_theme(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 6. HEALTH SCORE BAR CHART
# ─────────────────────────────────────────────────────────────────────────────

def health_score_bars(score_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of overall health scores."""
    if score_df.empty or "overall_score" not in score_df.columns:
        return go.Figure()

    df = score_df.sort_values("overall_score", ascending=True)
    ticker_col = "ticker" if "ticker" in df.columns else df.index.name or "index"

    height = max(380, 30 * len(df))
    y_offset = -110 / height # Constant pixel gap
    
    fig = go.Figure(
        go.Bar(
            x=df["overall_score"],
            y=df[ticker_col] if ticker_col in df.columns else df.index,
            orientation="h",
            marker=dict(
                color=df["overall_score"],
                colorscale="Plasma_r",
                cmin=0, cmax=100,
                showscale=True,
                colorbar=dict(
                    title=dict(text="Score", side="top"),
                    tickfont=dict(color=TEXT), 
                    title_font=dict(color=TEXT), 
                    orientation="h",
                    yanchor="top", y=y_offset,
                    xanchor="center", x=0.5,
                    len=0.9, 
                    thickness=15,
                    outlinewidth=0
                )
            ),
            text=df["overall_score"].round(1).astype(str) + " pts",
            textposition="outside",
            textfont=dict(color=TEXT, size=10),
        )
    )
    fig.update_layout(
        title="Financial Health Score — Sector Ranking",
        xaxis=dict(range=[0, 105], title="Score (0–100)"),
        height=height,
        margin=dict(b=120)
    )
    return _apply_theme(fig)







# ─────────────────────────────────────────────────────────────────────────────
# 7. TREND LINE — RATIO OVER TIME
# ─────────────────────────────────────────────────────────────────────────────

def ratio_trend(
    ratio_history: pd.DataFrame,
    ratios: Optional[List[str]] = None,
    ticker: str = "",
) -> go.Figure:
    """Line chart of ratio history for one company."""
    if ratio_history.empty:
        return go.Figure()

    if ratios is None:
        ratios = [c for c in ratio_history.columns if c in RATIO_LABELS][:4]

    colors = [ACCENT, GREEN, YELLOW, RED]
    fig = go.Figure()
    for i, ratio in enumerate(ratios):
        if ratio not in ratio_history.columns:
            continue
        fig.add_trace(
            go.Scatter(
                x=ratio_history.index,
                y=ratio_history[ratio],
                name=RATIO_LABELS.get(ratio, ratio),
                line=dict(color=colors[i % len(colors)], width=2),
                mode="lines+markers",
                marker=dict(size=5),
            )
        )

    fig.update_layout(
        title=f"Ratio Trend — {ticker}",
        xaxis_title="Quarter",
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return _apply_theme(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 8. OUTLIER SUMMARY TABLE (Plotly)
# ─────────────────────────────────────────────────────────────────────────────

def outlier_table(outlier_df: pd.DataFrame) -> go.Figure:
    """Formatted Plotly table of top outliers."""
    if outlier_df.empty:
        return go.Figure()

    display_cols = [
        "ticker", "ratio_label", "value", "sector_median",
        "deviation_pct", "severity_score", "label",
    ]
    present = [c for c in display_cols if c in outlier_df.columns]
    df = outlier_df[present].head(30)

    cell_colors = []
    for _, row in df.iterrows():
        is_pos = row.get("label", "").startswith("Positive")
        cell_colors.append(["#0d2e2b" if is_pos else "#2f1a1a"] * len(present))

    fig = go.Figure(
        go.Table(
            header=dict(
                values=[c.replace("_", " ").title() for c in present],
                fill_color=DARK_BG,
                font=dict(color=ACCENT, size=11, family="Google Sans, sans-serif"),
                align="center",
                height=32,
            ),
            cells=dict(
                values=[df[c].tolist() for c in present],
                fill_color=list(zip(*cell_colors)) if cell_colors else CARD_BG,
                font=dict(color=TEXT, size=10, family="Google Sans, sans-serif"),
                align=["center"] * len(present),
                height=28,
            ),
        )
    )
    fig.update_layout(
        title="Top Outliers",
        paper_bgcolor=DARK_BG,
        height=min(900, 100 + 30 * len(df)),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# 8. BENCHMARK VISUALIZATIONS
# ─────────────────────────────────────────────────────────────────────────────

# Category-to-color mapping for benchmarks
_CAT_COLORS = {
    "Elite":    "#00c4a7",   # accent teal
    "Strong":   "#5a8a85",   # secondary
    "Healthy":  "#7ab8b2",   # body text
    "Moderate": "#d29922",   # yellow
    "Weak":     "#ffa657",   # orange
    "Critical": "#f85149",   # red
}


def _cat_color(category_str: str) -> str:
    """Extract color from a benchmark category string like 'Strong'."""
    for key, color in _CAT_COLORS.items():
        if key in str(category_str):
            return color
    return TEXT


def benchmark_leaderboard(summary_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart ranking companies by composite benchmark score."""
    df = summary_df.sort_values("benchmark_score", ascending=True).copy()
    colors = [_cat_color(c) for c in df["benchmark_category"]]

    fig = go.Figure(go.Bar(
        x=df["benchmark_score"],
        y=df["ticker"],
        orientation="h",
        marker=dict(
            color=colors,
            line=dict(width=0.5, color=GRID),
        ),
        text=df["benchmark_score"].apply(lambda v: f"{v:.1f}"),
        textposition="outside",
        textfont=dict(size=11, color=TEXT),
    ))

    # Add category labels at the end of bars
    for i, (_, row) in enumerate(df.iterrows()):
        fig.add_annotation(
            x=row["benchmark_score"] + 3,
            y=row["ticker"],
            text=row["benchmark_category"],
            showarrow=False,
            font=dict(size=9, color=TEXT),
            xanchor="left",
        )

    fig.update_layout(
        title="Benchmark Leaderboard",
        xaxis_title="Benchmark Score (0-100)",
        yaxis_title="",
        xaxis=dict(range=[0, 110]),
        height=max(300, 60 * len(df)),
        showlegend=False,
    )
    return _apply_theme(fig)


def benchmark_heatmap(ratio_scores_df: pd.DataFrame) -> go.Figure:
    """Heatmap of ratio-level benchmark scores (0-100) per company."""
    # Use readable labels
    display_cols = [c for c in ratio_scores_df.columns if c in RATIO_LABELS]
    if not display_cols:
        display_cols = list(ratio_scores_df.columns)

    sub = ratio_scores_df[display_cols].copy()
    col_labels = [RATIO_LABELS.get(c, c) for c in sub.columns]

    fig = go.Figure(go.Heatmap(
        z=sub.values,
        x=col_labels,
        y=sub.index.tolist(),
        colorscale="Plasma_r",
        zmin=0,
        zmax=100,
        text=sub.round(0).astype(str).replace("nan", "---").values,
        texttemplate="%{text}",
        textfont=dict(size=9),
        colorbar=dict(
            title="Score",
            tickvals=[0, 25, 50, 75, 100],
            ticktext=["0", "25", "50", "75", "100"],
        ),
        hoverongaps=False,
    ))

    fig.update_layout(
        title="Ratio-Level Benchmark Scores",
        xaxis=dict(tickangle=-45),
        height=max(350, 70 * len(sub)),
    )
    return _apply_theme(fig)


def benchmark_radar(summary_df: pd.DataFrame, ticker: str) -> go.Figure:
    """Spider/radar chart of pillar scores for a single company vs sector median."""
    pillar_cols = [c for c in summary_df.columns
                   if c.endswith("_score") and c != "benchmark_score"]

    company_row = summary_df[summary_df["ticker"] == ticker]
    if company_row.empty:
        return _apply_theme(go.Figure())

    labels = [c.replace("_score", "").title() for c in pillar_cols]
    company_vals = [float(company_row[c].iloc[0]) for c in pillar_cols]
    median_vals = [float(summary_df[c].median()) for c in pillar_cols]

    # Close the radar loop
    labels_closed = labels + [labels[0]]
    company_closed = company_vals + [company_vals[0]]
    median_closed = median_vals + [median_vals[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=company_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(0,196,167,0.15)",
        line=dict(color=ACCENT, width=2),
        name=ticker,
    ))
    fig.add_trace(go.Scatterpolar(
        r=median_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(90,138,133,0.10)",
        line=dict(color=ACCENT, width=1.5, dash="dot"),
        name="Sector Median",
    ))

    fig.update_layout(
        title=f"Benchmark Radar - {ticker}",
        polar=dict(
            bgcolor=CARD_BG,
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor=GRID, linecolor=GRID,
                tickfont=dict(size=8, color=TEXT),
            ),
            angularaxis=dict(
                gridcolor=GRID, linecolor=GRID,
                tickfont=dict(size=10, color=TEXT),
            ),
        ),
        height=450,
        showlegend=True,
        legend=dict(bgcolor=CARD_BG, bordercolor=GRID,
                    font=dict(size=10, color=TEXT)),
    )
    return _apply_theme(fig)


def benchmark_distribution(summary_df: pd.DataFrame) -> go.Figure:
    """Bar chart of benchmark score distribution by category."""
    scores = summary_df["benchmark_score"].dropna()

    # Use fixed category bins aligned with benchmark categories
    bins = [0, 20, 40, 60, 75, 90, 100]
    labels = ["Critical\n(0-20)", "Weak\n(20-40)", "Moderate\n(40-60)",
              "Healthy\n(60-75)", "Strong\n(75-90)", "Elite\n(90-100)"]
    bin_colors = ["#f85149", "#ffa657", "#d29922", "#7ab8b2", "#5a8a85", "#00c4a7"]

    counts = pd.cut(scores, bins=bins, labels=labels, right=True,
                    include_lowest=True).value_counts().reindex(labels, fill_value=0)

    fig = go.Figure(go.Bar(
        x=counts.index.tolist(),
        y=counts.values,
        marker=dict(
            color=bin_colors,
            line=dict(width=1, color=CARD_BG),
        ),
        text=counts.values,
        textposition="outside",
        textfont=dict(size=12, color=TEXT),
    ))

    # Add median annotation
    median_val = scores.median()
    fig.add_annotation(
        text=f"Median: {median_val:.1f}",
        xref="paper", yref="paper",
        x=0.98, y=0.95,
        showarrow=False,
        font=dict(color=GREEN, size=11),
        bgcolor=CARD_BG,
        bordercolor=GRID,
        borderpad=4,
    )

    fig.update_layout(
        title="Benchmark Score Distribution",
        xaxis_title="Category",
        yaxis_title="Number of Companies",
        yaxis=dict(dtick=1),
        height=350,
        showlegend=False,
    )
    return _apply_theme(fig)


def benchmark_pillar_comparison(summary_df: pd.DataFrame) -> go.Figure:
    """Grouped bar chart comparing pillar scores across all companies."""
    pillar_cols = [c for c in summary_df.columns
                   if c.endswith("_score") and c != "benchmark_score"]

    colors = [ACCENT, SECONDARY, "#7ab8b2", YELLOW, "#3d6e69"]
    fig = go.Figure()

    for i, col in enumerate(pillar_cols):
        fig.add_trace(go.Bar(
            name=col.replace("_score", "").title(),
            x=summary_df["ticker"],
            y=summary_df[col],
            marker_color=colors[i % len(colors)],
        ))

    fig.update_layout(
        title="Pillar Score Comparison",
        xaxis_title="",
        yaxis_title="Score (0-100)",
        yaxis=dict(range=[0, 105]),
        barmode="group",
        height=450,
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="center", x=0.5,
            bgcolor=CARD_BG, bordercolor=GRID,
            font=dict(size=10, color=TEXT),
        ),
    )
    return _apply_theme(fig)


def benchmark_top_performers(summary_df: pd.DataFrame, n: int = 10) -> go.Figure:
    """Plotly table of top N companies by benchmark score."""
    top = summary_df.nlargest(n, "benchmark_score")
    pillar_cols = [c for c in top.columns
                   if c.endswith("_score") and c != "benchmark_score"]

    display_cols = ["benchmark_rank", "ticker", "benchmark_score",
                    "benchmark_category"] + pillar_cols
    present = [c for c in display_cols if c in top.columns]
    df = top[present].copy()

    headers = [c.replace("_", " ").replace("benchmark ", "").title()
               for c in present]

    # Color rows by category
    row_colors = []
    for _, row in df.iterrows():
        cat = row.get("benchmark_category", "")
        c = _cat_color(cat)
        # Slightly transparent background
        row_colors.append([f"rgba({int(c[1:3],16)},{int(c[3:5],16)},{int(c[5:7],16)},0.12)"] * len(present))

    fig = go.Figure(go.Table(
        header=dict(
            values=headers,
            fill_color=DARK_BG,
            font=dict(color=ACCENT, size=10, family="Google Sans, sans-serif"),
            align="center",
            height=30,
        ),
        cells=dict(
            values=[df[c].tolist() for c in present],
            fill_color=list(zip(*row_colors)) if row_colors else CARD_BG,
            font=dict(color=TEXT, size=9, family="Google Sans, sans-serif"),
            align="center",
            height=26,
            format=[None if df[c].dtype == object else ".1f" for c in present],
        ),
    ))

    fig.update_layout(
        title=f"Top {n} Benchmark Performers",
        paper_bgcolor=DARK_BG,
        height=min(600, 80 + 30 * len(df)),
    )
    return fig


def benchmark_sunburst(hierarchical_df: pd.DataFrame) -> go.Figure:
    """Sunburst chart: Benchmark -> Pillar -> Ratio with avg scores."""
    df = hierarchical_df.copy()

    fig = px.sunburst(
        df,
        path=["level_0", "pillar", "ratio"],
        values="weight",
        color="ratio_avg_score",
        color_continuous_scale="Plasma_r",
        range_color=[0, 100],
    )
    fig.update_traces(
        textinfo="label+value",
        insidetextorientation="radial",
        hovertemplate="<b>%{label}</b><br>Avg Score: %{color:.1f}<br>Weight: %{value:.2f}<extra></extra>",
    )
    fig.update_layout(
        title="Benchmark Hierarchy (Pillar -> Ratio)",
        paper_bgcolor=DARK_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=TEXT, family="Google Sans, sans-serif"),
        height=500,
        coloraxis_colorbar=dict(title="Score"),
    )
    return fig


def benchmark_ratio_contribution(
    contribution_df: pd.DataFrame, ticker: str,
) -> go.Figure:
    """Horizontal bar chart showing each ratio's contribution for one company."""
    df = contribution_df[contribution_df["ticker"] == ticker].copy()
    df = df[df["contribution"] > 0].sort_values("contribution", ascending=True)

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No contribution data", showarrow=False,
                           font=dict(color=TEXT, size=14))
        return _apply_theme(fig)

    status_colors = {
        "strong": GREEN, "weak": RED, "neutral": YELLOW,
        "outlier-excluded": MUTED, "no-data": "#1a3a37",
    }
    colors = [status_colors.get(s, TEXT) for s in df["status"]]

    fig = go.Figure(go.Bar(
        x=df["contribution"],
        y=df["ratio_label"],
        orientation="h",
        marker=dict(color=colors, line=dict(width=0.5, color=GRID)),
        text=df.apply(
            lambda r: f"{r['benchmark_score']:.0f} x {r['weight']:.2f} = {r['contribution']:.1f}"
            if pd.notna(r['benchmark_score']) else "excluded",
            axis=1,
        ),
        textposition="outside",
        textfont=dict(size=9, color=TEXT),
        customdata=df[["pillar", "status", "raw_value"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Pillar: %{customdata[0]}<br>"
            "Raw Value: %{customdata[2]}<br>"
            "Status: %{customdata[1]}<br>"
            "Contribution: %{x:.1f}<extra></extra>"
        ),
    ))

    fig.update_layout(
        title=f"Ratio Contributions - {ticker}",
        xaxis_title="Weighted Contribution",
        yaxis_title="",
        height=max(350, 28 * len(df)),
        showlegend=False,
    )
    return _apply_theme(fig)

def plot_ratio_scorecard(ratio_scorecard_df: pd.DataFrame, ticker: str) -> go.Figure:
    df = ratio_scorecard_df[ratio_scorecard_df["ticker"] == ticker].copy()
    if df.empty: return _apply_theme(go.Figure())
    df = df.dropna(subset=["percentile_rank"]).sort_values("percentile_rank", ascending=True)
    if df.empty: return _apply_theme(go.Figure())
    
    pillars = ["Profitability", "Liquidity", "Solvency", "Efficiency", "Growth", "Other"]
    present_pillars = [p for p in pillars if p in df["pillar"].unique()]
    if not present_pillars:
        present_pillars = df["pillar"].unique().tolist()
        
    # Calculate proportional heights so each bar has the same visual thickness
    row_counts = [len(df[df["pillar"] == p]) for p in present_pillars]
    
    fig = make_subplots(
        rows=len(present_pillars), cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.04,
        subplot_titles=present_pillars,
        row_heights=row_counts
    )
    
    row_idx = 1
    total_height = 100
    for pillar in present_pillars:
        sub_df = df[df["pillar"] == pillar]
        if sub_df.empty:
            continue
            
        labels = [RATIO_LABELS.get(r, r) for r in sub_df["ratio"]]
        
        fig.add_trace(go.Bar(
            x=sub_df["percentile_rank"], y=labels, orientation="h",
            marker=dict(
                color=sub_df["percentile_rank"], 
                colorscale="RdYlGn",
                cmin=0, cmax=100,
                showscale=True if row_idx == 1 else False,
                colorbar=dict(title="Percentile", tickfont=dict(color=TEXT), title_font=dict(color=TEXT), len=0.8, y=0.5) if row_idx == 1 else None,
                line=dict(width=0.5, color=GRID)
            ),
            showlegend=False,
            text=sub_df.apply(lambda r: f"{r['raw_value']:.2f} ({r['position_label']})" if pd.notna(r['raw_value']) else f"N/A ({r['position_label']})", axis=1),
            textposition="outside", textfont=dict(size=10, color=TEXT),
            customdata=sub_df[["raw_value", "peer_median", "position_label", "health_label"]].values,
            hovertemplate="<b>%{y}</b><br>Percentile: %{x:.1f}<br>Raw Value: %{customdata[0]:.2f}<br>Peer Median: %{customdata[1]:.2f}<br>Position: %{customdata[2]}<br>Health: %{customdata[3]}<extra></extra>",
        ), row=row_idx, col=1)
        
        fig.add_vline(x=25, line_dash="dot", line_color=YELLOW, opacity=0.5, row=row_idx, col=1)
        fig.add_vline(x=50, line_dash="dash", line_color=TEXT, opacity=0.8, row=row_idx, col=1)
        fig.add_vline(x=75, line_dash="dot", line_color=GREEN, opacity=0.5, row=row_idx, col=1)
        
        total_height += len(sub_df) * 40 + 35
        row_idx += 1
        
    fig.update_layout(
        title=f"Ratio Scorecard - {ticker}",
        height=max(450, total_height),
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    
    fig.update_xaxes(range=[0, 110], title_text="Percentile Rank (0-100)", row=len(present_pillars), col=1)
    
    return _apply_theme(fig)

def plot_peer_stats_heatmap(peer_stats_df: pd.DataFrame) -> go.Figure:
    if peer_stats_df.empty: return _apply_theme(go.Figure())
    stats_cols = ["p10", "q1", "median", "mean", "q3", "p90"]
    available_cols = [c for c in stats_cols if c in peer_stats_df.columns]
    
    # Map ratios to pillars
    ratio_to_pillar = {}
    for pillar, metrics in PILLARS.items():
        for ratio, _, _ in metrics:
            ratio_to_pillar[ratio] = pillar
            
    df = peer_stats_df[available_cols].copy()
    df["pillar"] = df.index.map(lambda r: ratio_to_pillar.get(r, "Other"))
    
    pillars = ["Profitability", "Liquidity", "Solvency", "Efficiency", "Growth", "Other"]
    present_pillars = [p for p in pillars if p in df["pillar"].unique()]
    
    # Calculate proportional heights so each row has the same visual thickness
    row_counts = [len(df[df["pillar"] == p]) for p in present_pillars]
    
    fig = make_subplots(
        rows=len(present_pillars), cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        subplot_titles=present_pillars,
        row_heights=row_counts
    )
    
    row_idx = 1
    total_height = 100
    for pillar in present_pillars:
        sub = df[df["pillar"] == pillar].drop(columns=["pillar"])
        if sub.empty:
            continue
            
        labels = [RATIO_LABELS.get(r, r) for r in sub.index]
        
        # Flip percentiles so "Top 10% Performance" is always on the right
        for ratio in sub.index:
            if ratio in HIGH_IS_BAD:
                p10_val, p90_val = sub.loc[ratio, "p10"], sub.loc[ratio, "p90"]
                q1_val, q3_val = sub.loc[ratio, "q1"], sub.loc[ratio, "q3"]
                sub.loc[ratio, "p10"], sub.loc[ratio, "p90"] = p90_val, p10_val
                sub.loc[ratio, "q1"], sub.loc[ratio, "q3"] = q3_val, q1_val

        z_df = sub.sub(sub.mean(axis=1), axis=0).div(sub.std(axis=1).replace(0, 1), axis=0)
        
        # Apply polarity flip for ratios where Lower is Better so Z-score colors match
        for ratio in sub.index:
            if ratio in HIGH_IS_BAD:
                z_df.loc[ratio] = z_df.loc[ratio] * -1
                
        z_df = z_df.clip(-3, 3)
        
        x_label_map = {
            "p10": "Bottom 10%", "q1": "Bottom 25%", 
            "median": "Median", "mean": "Mean", 
            "q3": "Top 25%", "p90": "Top 10%"
        }
        x_labels = [x_label_map.get(c, c.upper()) for c in available_cols]
        
        fig.add_trace(go.Heatmap(
            z=z_df.values, x=x_labels, y=labels,
            colorscale="Viridis", text=sub.round(2).values, texttemplate="%{text}",
            colorbar=dict(title="Z-Score", tickfont=dict(color=TEXT), title_font=dict(color=TEXT), len=0.8, y=0.5) if row_idx == 1 else None,
            showscale=True if row_idx == 1 else False
        ), row=row_idx, col=1)
        
        total_height += len(sub) * 40 + 35
        row_idx += 1
        
    fig.update_layout(
        title="Peer Group Statistics", 
        height=max(450, total_height),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    
    fig.update_xaxes(title_text="Statistic", row=len(present_pillars), col=1)
    
    return _apply_theme(fig)