"""
pptx_charts.py
==============
Matplotlib-based chart renderers for embedding publication-quality visuals
into FinMetrics Suite PPTX slides. Each function renders a chart to a
temporary PNG file and returns its path for insertion into a slide.

All charts use:
  - Transparent backgrounds (blend with dark slide canvas)
  - Abyss Teal color palette
  - 200 DPI resolution
  - Calibri font family
  - Minimal chart chrome
"""

import io
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.colors import LinearSegmentedColormap
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


# ── Abyss Teal Matplotlib Theme ─────────────────────────────────────────────

_HEX_BG = "#001F1E"
_HEX_CARD = "#002623"
_HEX_TEAL = "#00C4A7"
_HEX_TEAL_DIM = "#005F52"
_HEX_WHITE = "#D4F0EC"
_HEX_MUTED = "#7AB8B2"
_HEX_DIM = "#3D6E69"
_HEX_BORDER = "#1A3A37"
_HEX_GREEN = "#2ECC71"
_HEX_ORANGE = "#FF9F43"
_HEX_CORAL = "#FF5E57"
_HEX_PURPLE = "#A55EEA"
_HEX_YELLOW = "#D29922"
_HEX_SECONDARY = "#5A8A85"

_HEALTH_COLORS = [_HEX_CORAL, "#FFA657", _HEX_YELLOW, _HEX_SECONDARY, _HEX_TEAL]

_FONT_FAMILY = "Calibri"

# DPI for all rendered charts
_DPI = 200


def _apply_theme() -> None:
    """Apply the Abyss Teal dark theme to matplotlib."""
    if not HAS_MATPLOTLIB:
        return
    plt.rcParams.update({
        "font.family": _FONT_FAMILY,
        "font.size": 10,
        "text.color": _HEX_WHITE,
        "axes.facecolor": "none",
        "axes.edgecolor": _HEX_BORDER,
        "axes.labelcolor": _HEX_MUTED,
        "axes.grid": False,
        "figure.facecolor": "none",
        "xtick.color": _HEX_DIM,
        "ytick.color": _HEX_DIM,
        "grid.color": _HEX_BORDER,
        "grid.alpha": 0.3,
    })


def _save_chart(fig, dpi: int = _DPI) -> str:
    """Save a matplotlib figure to a temporary PNG and return its path."""
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    fig.savefig(tmp.name, dpi=dpi, bbox_inches="tight", transparent=True)
    plt.close(fig)
    return tmp.name


# ============================================================================
# PILLAR GAUGE CHART (Horizontal Progress Bars)
# ============================================================================

def render_pillar_gauge_chart(
    pillar_scores: Dict[str, float],
    pillar_weights: Dict[str, float],
    fig_width: float = 5.5,
    fig_height: float = 3.5,
) -> Optional[str]:
    """
    Render five horizontal progress bars showing pillar scores (0-100).

    Parameters
    ----------
    pillar_scores : Dict[str, float]
        Mapping of pillar name to score (0-100).
    pillar_weights : Dict[str, float]
        Mapping of pillar name to weight (e.g., 0.30).

    Returns
    -------
    str or None
        Path to the rendered PNG, or None if matplotlib is unavailable.
    """
    if not HAS_MATPLOTLIB:
        return None

    _apply_theme()

    pillars = list(pillar_scores.keys())
    scores = [pillar_scores[p] for p in pillars]
    weights = [pillar_weights.get(p, 0.2) for p in pillars]

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    y_positions = list(range(len(pillars)))
    bar_height = 0.45

    # Draw track bars (background)
    ax.barh(y_positions, [100] * len(pillars), height=bar_height,
            color=_HEX_TEAL_DIM, alpha=0.3, edgecolor="none")

    # Draw filled bars with health-gradient colors
    colors = []
    for s in scores:
        if s >= 80:
            colors.append(_HEX_TEAL)
        elif s >= 65:
            colors.append(_HEX_SECONDARY)
        elif s >= 50:
            colors.append(_HEX_YELLOW)
        elif s >= 35:
            colors.append(_HEX_ORANGE)
        else:
            colors.append(_HEX_CORAL)

    ax.barh(y_positions, scores, height=bar_height,
            color=colors, edgecolor="none")

    # Add score labels at bar ends
    for i, (s, p, w) in enumerate(zip(scores, pillars, weights)):
        # Score value at end of bar
        ax.text(s + 1.5, i, f"{s:.1f}",
                va="center", ha="left",
                fontsize=10, fontweight="bold", color=_HEX_WHITE)
        # Pillar label
        ax.text(-1, i, f"{p} ({int(w*100)}%)",
                va="center", ha="right",
                fontsize=9.5, fontweight="bold", color=_HEX_MUTED)

    ax.set_xlim(-2, 110)
    ax.set_ylim(-0.6, len(pillars) - 0.4)
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)

    fig.tight_layout(pad=0.3)
    return _save_chart(fig)


# ============================================================================
# PILLAR RADAR / SPIDER CHART
# ============================================================================

def render_pillar_radar(
    client_scores: Dict[str, float],
    sector_medians: Dict[str, float],
    client_name: str = "Client",
    fig_width: float = 5.5,
    fig_height: float = 5.0,
) -> Optional[str]:
    """
    Render a spider/radar chart comparing client pillar scores vs sector median.

    Returns
    -------
    str or None
        Path to rendered PNG.
    """
    if not HAS_MATPLOTLIB:
        return None

    _apply_theme()

    labels = list(client_scores.keys())
    n = len(labels)
    if n < 3:
        return None

    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    client_vals = [client_scores[l] for l in labels] + [client_scores[labels[0]]]
    sector_vals = [sector_medians.get(l, 50) for l in labels] + [sector_medians.get(labels[0], 50)]

    fig, ax = plt.subplots(figsize=(fig_width, fig_height), subplot_kw=dict(polar=True))
    ax.set_aspect("equal")

    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80])
    ax.set_yticklabels(["20", "40", "60", "80"],
                       fontsize=7, color=_HEX_DIM)

    # Sector median (filled area)
    ax.fill(angles, sector_vals, alpha=0.08, color=_HEX_MUTED)
    ax.plot(angles, sector_vals, linewidth=1.5, linestyle="--",
            color=_HEX_MUTED, alpha=0.7, label="Sector Median")

    # Client (filled area)
    ax.fill(angles, client_vals, alpha=0.15, color=_HEX_TEAL)
    ax.plot(angles, client_vals, linewidth=2.5,
            color=_HEX_TEAL, label=client_name)

    # Client data points
    ax.scatter(angles[:-1], client_vals[:-1], s=40, color=_HEX_TEAL,
               zorder=5, edgecolors=_HEX_WHITE, linewidths=0.5)

    # Labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9, fontweight="bold", color=_HEX_WHITE)

    # Grid styling
    ax.spines["polar"].set_color(_HEX_BORDER)
    ax.grid(color=_HEX_BORDER, alpha=0.3, linewidth=0.5)

    fig.tight_layout(pad=0.5)
    return _save_chart(fig)


# ============================================================================
# OUTLIER DEVIATION LOLLIPOP CHART
# ============================================================================

def render_outlier_lollipop(
    deviations: List[Dict],
    fig_width: float = 6.0,
    fig_height: float = 4.0,
    max_items: int = 6,
) -> Optional[str]:
    """
    Render a horizontal lollipop chart showing top deviations from peer median.

    Parameters
    ----------
    deviations : List[Dict]
        Each dict has keys: 'label', 'client_value', 'peer_median',
        'deviation_pct', 'is_positive'.

    Returns
    -------
    str or None
        Path to rendered PNG.
    """
    if not HAS_MATPLOTLIB or not deviations:
        return None

    _apply_theme()

    items = deviations[:max_items]
    items.reverse()  # Bottom to top for display

    labels = [d["label"] for d in items]
    devs = [d["deviation_pct"] for d in items]
    colors = [_HEX_GREEN if d.get("is_positive", False) else _HEX_CORAL for d in items]

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    y_pos = range(len(labels))

    # Lollipop stems
    for i, (dev, c) in enumerate(zip(devs, colors)):
        ax.plot([0, dev], [i, i], color=c, linewidth=2, alpha=0.7)
        ax.scatter([dev], [i], color=c, s=70, zorder=5,
                   edgecolors=_HEX_WHITE, linewidths=0.5)

    # Zero reference line
    ax.axvline(x=0, color=_HEX_BORDER, linewidth=1, linestyle="-")

    # Labels
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(labels, fontsize=8.5, color=_HEX_WHITE, fontweight="bold")

    # Value annotations
    for i, dev in enumerate(devs):
        sign = "+" if dev >= 0 else ""
        ax.text(dev + (2 if dev >= 0 else -2), i, f"{sign}{dev:.0f}%",
                va="center", ha="left" if dev >= 0 else "right",
                fontsize=8.5, fontweight="bold", color=_HEX_WHITE)

    ax.set_xlabel("Deviation from Peer Median (%)", fontsize=8, color=_HEX_DIM)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(_HEX_BORDER)
    ax.tick_params(axis="x", colors=_HEX_DIM, labelsize=7)

    fig.tight_layout(pad=0.5)
    return _save_chart(fig)


# ============================================================================
# ANOMALY GAUGE (Semicircular)
# ============================================================================

def render_anomaly_gauge(
    score: float,
    fig_width: float = 3.5,
    fig_height: float = 2.5,
) -> Optional[str]:
    """
    Render a semicircular gauge dial for the Isolation Forest anomaly score.

    Parameters
    ----------
    score : float
        Anomaly score (typically 0 to 1, higher = more anomalous).

    Returns
    -------
    str or None
        Path to rendered PNG.
    """
    if not HAS_MATPLOTLIB or np.isnan(score):
        return None

    _apply_theme()

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.set_aspect("equal")

    # Gauge arc parameters
    center = (0, 0)
    radius = 1.0
    inner_radius = 0.65

    # Draw gradient arc segments (green -> yellow -> orange -> red)
    n_segments = 100
    theta_range = np.linspace(np.pi, 0, n_segments)

    cmap = LinearSegmentedColormap.from_list(
        "anomaly", [_HEX_TEAL, _HEX_GREEN, _HEX_YELLOW, _HEX_ORANGE, _HEX_CORAL]
    )

    for i in range(n_segments - 1):
        t1, t2 = theta_range[i], theta_range[i + 1]
        frac = i / (n_segments - 1)
        color = cmap(frac)

        # Outer arc wedge
        wedge = mpatches.Wedge(
            center, radius, np.degrees(t2), np.degrees(t1),
            width=radius - inner_radius,
            facecolor=color, edgecolor="none", alpha=0.7
        )
        ax.add_patch(wedge)

    # Needle
    clamped = max(0, min(score, 1.0))
    needle_angle = np.pi * (1 - clamped)
    needle_x = 0.85 * np.cos(needle_angle)
    needle_y = 0.85 * np.sin(needle_angle)
    ax.plot([0, needle_x], [0, needle_y], color=_HEX_WHITE,
            linewidth=2.5, solid_capstyle="round")
    ax.scatter([0], [0], s=60, color=_HEX_WHITE, zorder=10)

    # Score text below center
    ax.text(0, -0.25, f"{score:.2f}", ha="center", va="center",
            fontsize=20, fontweight="bold", color=_HEX_WHITE)

    # Min/Max labels
    ax.text(-1.1, -0.08, "0.0", ha="center", fontsize=7, color=_HEX_DIM)
    ax.text(1.1, -0.08, "1.0", ha="center", fontsize=7, color=_HEX_DIM)

    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(-0.5, 1.2)
    ax.axis("off")

    fig.tight_layout(pad=0.1)
    return _save_chart(fig)


# ============================================================================
# SCORE DISTRIBUTION HISTOGRAM
# ============================================================================

def render_score_distribution(
    all_scores: List[float],
    client_score: float,
    client_name: str = "Client",
    fig_width: float = 4.0,
    fig_height: float = 2.5,
) -> Optional[str]:
    """
    Render a small histogram showing where the client falls in the sector
    score distribution.

    Returns
    -------
    str or None
        Path to rendered PNG.
    """
    if not HAS_MATPLOTLIB or not all_scores:
        return None

    _apply_theme()

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    # Histogram
    bins = np.linspace(0, 100, 15)
    ax.hist(all_scores, bins=bins, color=_HEX_TEAL_DIM, alpha=0.5,
            edgecolor=_HEX_BORDER, linewidth=0.5)

    # Force Y-axis ticks to be integers (no float company counts)
    try:
        from matplotlib.ticker import MaxNLocator
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    except ImportError:
        pass

    # Enforce clear 0-100 scale for composite score
    ax.set_xlim(0, 100)

    # Client marker (dashed elegant guide)
    ax.axvline(x=client_score, color=_HEX_TEAL, linewidth=1.5,
               linestyle="--", label=client_name)

    # Dynamic annotation placement to prevent clipping at borders
    max_y = ax.get_ylim()[1]
    if client_score > 50:
        xytext = (client_score - 8, max_y * 0.65)
        ha = "right"
    else:
        xytext = (client_score + 8, max_y * 0.65)
        ha = "left"

    ax.annotate(
        f"{client_name}\n{client_score:.1f}",
        xy=(client_score, max_y * 0.5), 
        xytext=xytext,
        fontsize=8, fontweight="bold", color=_HEX_TEAL,
        arrowprops=dict(arrowstyle="->", color=_HEX_TEAL, lw=1),
        bbox=dict(boxstyle="round,pad=0.4", fc=_HEX_CARD, ec=_HEX_TEAL, lw=1, alpha=0.9),
        ha=ha
    )

    ax.set_xlabel("Composite Score", fontsize=8, color=_HEX_DIM)
    ax.set_ylabel("Peers", fontsize=8, color=_HEX_DIM)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(_HEX_BORDER)
    ax.spines["bottom"].set_color(_HEX_BORDER)

    fig.tight_layout(pad=0.3)
    return _save_chart(fig)
