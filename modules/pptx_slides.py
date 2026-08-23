"""
pptx_slides.py
==============
Individual slide builder functions for the FinMetrics Suite institutional-grade
PPTX export. Each function constructs one complete slide by composing design
tokens, components, and embedded charts.

Slide Architecture (8 slides):
  1. Title / Cover Page
  2. Executive Summary Dashboard
  3. Pillar Performance Scorecard
  4. Competitive Positioning (Radar)
  5. Outlier Analysis & Anomaly Detection
  6. Strategic SWOT Matrix
  7. AI Strategic Action Plan
  8. Ratio Detail Appendix + Closing
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

from modules.pptx_design_tokens import (
    SLIDE_WIDTH, SLIDE_HEIGHT,
    COLOR_BG, COLOR_CARD, COLOR_SURFACE, COLOR_BORDER,
    COLOR_TEAL, COLOR_TEAL_DIM, COLOR_SECONDARY,
    COLOR_WHITE, COLOR_MUTED, COLOR_DIM,
    COLOR_GREEN, COLOR_ORANGE, COLOR_CORAL, COLOR_PURPLE, COLOR_YELLOW,
    FONT_PRIMARY, FONT_H1, FONT_H2, FONT_H3, FONT_BODY, FONT_CAPTION,
    FONT_KPI_LARGE, FONT_KPI_MEDIUM, FONT_TITLE_COVER, FONT_SUBTITLE,
    FONT_ACTION_NUMBER,
    MARGIN_SLIDE, MARGIN_CARD, GAP_CARDS, CONTENT_TOP, CONTENT_WIDTH,
    STRIPE_HEIGHT, DIVIDER_HEIGHT, CARD_ACCENT_WIDTH,
    FOOTER_TOP, FOOTER_HEIGHT,
    PILLAR_CONFIG, SWOT_CONFIG, ACTION_PLAN_CONFIG,
    health_color, health_label, category_color,
    is_percentage_ratio, format_ratio_value,
)

from modules.pptx_components import (
    set_slide_bg, add_slide_header, add_slide_footer,
    add_card, add_kpi_block, add_badge,
    add_progress_bar, add_data_table, add_bullet_list,
    add_divider, add_text_block, add_multiline_text,
)

from modules.pptx_charts import (
    render_pillar_gauge_chart,
    render_pillar_radar,
    render_outlier_lollipop,
    render_anomaly_gauge,
    render_score_distribution,
)

logger = logging.getLogger(__name__)

TOTAL_SLIDES = 8

# Temporary chart file paths for cleanup
_temp_chart_files: List[str] = []


def _cleanup_temp_charts() -> None:
    """Remove temporary chart PNG files."""
    for f in _temp_chart_files:
        try:
            if os.path.exists(f):
                os.remove(f)
        except OSError:
            pass
    _temp_chart_files.clear()


def _embed_chart(slide, chart_path: Optional[str],
                 left: float, top: float, width: float, height: float) -> None:
    """Embed a chart image into a slide if the path is valid, preserving its aspect ratio and centering it."""
    if chart_path and os.path.exists(chart_path):
        try:
            from PIL import Image
            with Image.open(chart_path) as img:
                img_w, img_h = img.size
            
            img_aspect = img_w / img_h
            target_aspect = width / height
            
            if img_aspect > target_aspect:
                # Image is wider than the target box. Fit width, scale down height.
                fit_w = width
                fit_h = width / img_aspect
            else:
                # Image is taller than the target box. Fit height, scale down width.
                fit_h = height
                fit_w = height * img_aspect
                
            # Center the image inside the designated bounding box
            left_offset = (width - fit_w) / 2.0
            top_offset = (height - fit_h) / 2.0
            
            slide.shapes.add_picture(
                chart_path,
                Inches(left + left_offset), Inches(top + top_offset),
                Inches(fit_w), Inches(fit_h)
            )
        except Exception as e:
            # Fallback to default stretching behavior if PIL fails or other error occurs
            slide.shapes.add_picture(
                chart_path,
                Inches(left), Inches(top),
                Inches(width), Inches(height)
            )
        _temp_chart_files.append(chart_path)


# ============================================================================
# SLIDE 1: TITLE / COVER PAGE
# ============================================================================

def build_title_slide(prs, client_name: str, sector_name: str) -> None:
    """Build the cover page with centered branding."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide)

    # Top accent stripe
    top_bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0), Inches(0), Inches(SLIDE_WIDTH), Inches(STRIPE_HEIGHT)
    )
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = COLOR_TEAL
    top_bar.line.fill.background()

    # Bottom accent stripe
    bot_bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0), Inches(7.44), Inches(SLIDE_WIDTH), Inches(STRIPE_HEIGHT)
    )
    bot_bar.fill.solid()
    bot_bar.fill.fore_color.rgb = COLOR_TEAL
    bot_bar.line.fill.background()

    # Main title block (centered)
    add_multiline_text(
        slide, 1.5, 2.0, 10.333, 1.2,
        lines=[
            ("FINMETRICS SUITE", FONT_TITLE_COVER, COLOR_WHITE, True),
        ],
        alignment=PP_ALIGN.CENTER,
    )

    # Decorative divider
    add_divider(slide, 4.5, 3.3, 4.333, COLOR_TEAL)

    # Subtitle
    add_multiline_text(
        slide, 1.5, 3.6, 10.333, 0.8,
        lines=[
            ("Executive Financial Diagnostic", FONT_SUBTITLE, COLOR_TEAL, True),
            ("& Benchmark Report", FONT_SUBTITLE, COLOR_TEAL, True),
        ],
        alignment=PP_ALIGN.CENTER,
    )

    # Metadata block
    add_multiline_text(
        slide, 1.5, 4.8, 10.333, 1.6,
        lines=[
            (f"Client: {client_name}", Pt(13), COLOR_WHITE, True),
            (f"Sector Benchmark: {sector_name}", Pt(11), COLOR_MUTED, False),
            (f"Generated: {datetime.now().strftime('%B %Y')}", Pt(11), COLOR_MUTED, False),
            ("", Pt(6), COLOR_DIM, False),
            ("CONFIDENTIAL  --  BOARD REVIEW", Pt(9), COLOR_CORAL, True),
        ],
        alignment=PP_ALIGN.CENTER,
    )


# ============================================================================
# SLIDE 2: EXECUTIVE SUMMARY DASHBOARD
# ============================================================================

def build_executive_summary(
    prs,
    client_name: str,
    sector_name: str,
    pillar_df: pd.DataFrame,
    swot: Dict[str, List[Dict]],
) -> None:
    """Build the executive summary with KPI strip and key insights."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide)
    add_slide_header(slide, "EXECUTIVE SUMMARY", f"Performance overview for {client_name}")
    add_slide_footer(slide, 1, TOTAL_SLIDES)

    # Extract data
    comp_score = 50.0
    risk_cat = "Moderate"
    sector_rank = "--"
    peer_count = "--"

    if pillar_df is not None and not pillar_df.empty:
        if "composite_score" in pillar_df.columns:
            comp_score = float(pillar_df["composite_score"].values[0])
        if "risk_category" in pillar_df.columns:
            risk_cat = str(pillar_df["risk_category"].values[0])
        if "sector_rank" in pillar_df.columns:
            sector_rank = str(int(pillar_df["sector_rank"].values[0]))
        if "percentile" in pillar_df.columns:
            pctl = float(pillar_df["percentile"].values[0])
            # Approximate peer count from percentile
            peer_count = str(max(1, int(100 / max(1, pctl) * int(sector_rank) if sector_rank != "--" else 15)))

    cat_color = category_color(risk_cat)

    # ── KPI Strip (3 cards across the top) ────────────────────────────────
    kpi_y = 1.4
    kpi_h = 1.7
    kpi_w = 3.8
    gap = 0.3

    # Card 1: Composite Score
    x1 = 0.6
    add_card(slide, x1, kpi_y, kpi_w, kpi_h, COLOR_BORDER)
    add_kpi_block(
        slide, x1 + 0.35, kpi_y + 0.2, kpi_w - 0.7, kpi_h - 0.4,
        value=f"{comp_score:.1f}",
        label="COMPOSITE SCORE",
        sublabel="/ 100",
        value_color=COLOR_WHITE,
        alignment=PP_ALIGN.CENTER,
    )

    # Card 2: Sector Rank
    x2 = x1 + kpi_w + gap
    add_card(slide, x2, kpi_y, kpi_w, kpi_h, COLOR_BORDER)

    # Build rank display
    rank_str = f"#{sector_rank}" if sector_rank != "--" else "--"
    add_kpi_block(
        slide, x2 + 0.35, kpi_y + 0.2, kpi_w - 0.7, kpi_h - 0.4,
        value=rank_str,
        label="SECTOR RANK",
        sublabel=f"in {sector_name}",
        value_color=COLOR_TEAL,
        alignment=PP_ALIGN.CENTER,
    )

    # Card 3: Health Status
    x3 = x2 + kpi_w + gap
    add_card(slide, x3, kpi_y, kpi_w, kpi_h, cat_color)
    add_kpi_block(
        slide, x3 + 0.35, kpi_y + 0.2, kpi_w - 0.7, kpi_h - 0.4,
        value=risk_cat.upper(),
        label="HEALTH STATUS",
        sublabel="Overall financial health classification",
        value_color=cat_color,
        value_size=FONT_KPI_MEDIUM,
        alignment=PP_ALIGN.CENTER,
    )

    # ── Key Strengths / Key Risks (2-column layout below KPI strip) ───────
    insight_y = 3.5
    insight_h = 3.2
    insight_w = 5.8

    # Left: Key Strengths
    left_x = 0.6
    add_card(slide, left_x, insight_y, insight_w, insight_h, COLOR_GREEN,
             accent_side=True, accent_color=COLOR_GREEN)

    add_text_block(
        slide, left_x + 0.25, insight_y + 0.2, insight_w - 0.5, 0.3,
        "KEY STRENGTHS", font_size=FONT_H3, font_color=COLOR_GREEN, bold=True
    )
    add_divider(slide, left_x + 0.25, insight_y + 0.55, insight_w - 0.5, COLOR_GREEN)

    strengths = swot.get("strengths", [])[:3]
    if strengths:
        s_items = []
        for s in strengths:
            val = format_ratio_value(float(s["raw_value"]), s["ratio"])
            med = format_ratio_value(float(s["peer_median"]), s["ratio"])
            s_label = s["ratio_label"].replace("Roa", "ROA").replace("Roe", "ROE").replace("Roce", "ROCE").replace("Ocf", "OCF")
            s_items.append((
                s_label,
                f"{val} vs peer {med}",
                COLOR_GREEN,
            ))
        
        # Dynamic sizing for strengths
        s_len = len(s_items)
        if s_len == 3:
            s_size, s_space = Pt(12.0), Pt(12)
        elif s_len == 2:
            s_size, s_space = Pt(13.5), Pt(20)
        else:
            s_size, s_space = Pt(15.0), Pt(0)

        add_bullet_list(
            slide, left_x + 0.25, insight_y + 0.72, insight_w - 0.5, insight_h - 1.0,
            items=s_items, bullet_char="+", font_size=s_size, space_after=s_space
        )
    else:
        add_text_block(
            slide, left_x + 0.25, insight_y + 0.8, insight_w - 0.5, 0.5,
            "No significant strengths flagged in current scorecard.",
            font_color=COLOR_MUTED, italic=True, font_size=Pt(12.5)
        )

    # Right: Key Risks
    right_x = left_x + insight_w + gap
    add_card(slide, right_x, insight_y, insight_w, insight_h, COLOR_CORAL,
             accent_side=True, accent_color=COLOR_CORAL)

    add_text_block(
        slide, right_x + 0.25, insight_y + 0.2, insight_w - 0.5, 0.3,
        "KEY RISKS", font_size=FONT_H3, font_color=COLOR_CORAL, bold=True
    )
    add_divider(slide, right_x + 0.25, insight_y + 0.55, insight_w - 0.5, COLOR_CORAL)

    # Combine weaknesses and threats for risks
    risks = (swot.get("weaknesses", []) + swot.get("threats", []))[:3]
    if risks:
        r_items = []
        for r in risks:
            val = format_ratio_value(float(r["raw_value"]), r["ratio"])
            med = format_ratio_value(float(r["peer_median"]), r["ratio"])
            r_label = r["ratio_label"].replace("Roa", "ROA").replace("Roe", "ROE").replace("Roce", "ROCE").replace("Ocf", "OCF")
            r_items.append((
                r_label,
                f"{val} vs peer {med}",
                COLOR_CORAL,
            ))

        # Dynamic sizing for risks
        r_len = len(r_items)
        if r_len == 3:
            r_size, r_space = Pt(12.0), Pt(12)
        elif r_len == 2:
            r_size, r_space = Pt(13.5), Pt(20)
        else:
            r_size, r_space = Pt(15.0), Pt(0)

        add_bullet_list(
            slide, right_x + 0.25, insight_y + 0.72, insight_w - 0.5, insight_h - 1.0,
            items=r_items, bullet_char="!", font_size=r_size, space_after=r_space
        )
    else:
        add_text_block(
            slide, right_x + 0.25, insight_y + 0.8, insight_w - 0.5, 0.5,
            "No significant risks flagged in current scorecard.",
            font_color=COLOR_MUTED, italic=True, font_size=Pt(12.5)
        )


# ============================================================================
# SLIDE 3: PILLAR PERFORMANCE SCORECARD
# ============================================================================

def build_pillar_scorecard(
    prs,
    client_name: str,
    sector_name: str,
    pillar_df: pd.DataFrame,
) -> None:
    """Build the pillar scorecard with progress bars and distribution chart."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide)
    add_slide_header(slide, "PILLAR PERFORMANCE SCORECARD")
    add_slide_footer(slide, 2, TOTAL_SLIDES)

    # Extract pillar scores
    pillar_scores = {}
    pillar_weights = {}
    comp_score = 50.0
    risk_cat = "Moderate"

    if pillar_df is not None and not pillar_df.empty:
        if "composite_score" in pillar_df.columns:
            comp_score = float(pillar_df["composite_score"].values[0])
        if "risk_category" in pillar_df.columns:
            risk_cat = str(pillar_df["risk_category"].values[0])

        for p_name, p_col, p_weight in PILLAR_CONFIG:
            if p_col in pillar_df.columns:
                pillar_scores[p_name] = float(pillar_df[p_col].values[0])
            else:
                pillar_scores[p_name] = 50.0
            pillar_weights[p_name] = p_weight
    else:
        for p_name, _, p_weight in PILLAR_CONFIG:
            pillar_scores[p_name] = 50.0
            pillar_weights[p_name] = p_weight

    # ── Left Panel: Composite Score + Distribution ────────────────────────
    left_x = 0.6
    panel_w = 5.0
    panel_h = 5.3
    add_card(slide, left_x, CONTENT_TOP + 0.1, panel_w, panel_h, COLOR_BORDER)

    # Composite score KPI
    add_kpi_block(
        slide, left_x + 0.4, CONTENT_TOP + 0.3, panel_w - 0.8, 2.0,
        value=f"{comp_score:.1f}",
        label="COMPOSITE HEALTH SCORE",
        sublabel="/ 100",
        value_color=COLOR_WHITE,
        alignment=PP_ALIGN.CENTER,
    )

    # Health status badge
    cat_color = category_color(risk_cat)
    add_badge(
        slide, left_x + 1.5, CONTENT_TOP + 2.5,
        risk_cat.upper(), cat_color, width=2.0, height=0.35
    )

    # Distribution chart (if scores available from all peers)
    # Extract all composite scores from pillar_df
    all_scores = []
    if pillar_df is not None and not pillar_df.empty and "composite_score" in pillar_df.columns:
        all_scores = pillar_df["composite_score"].dropna().tolist()

    if len(all_scores) > 3:
        chart_path = render_score_distribution(all_scores, comp_score, client_name, fig_width=4.4, fig_height=2.2)
        _embed_chart(slide, chart_path, left_x + 0.3, CONTENT_TOP + 3.0, 4.4, 2.2)
    else:
        # Show text info instead
        add_multiline_text(
            slide, left_x + 0.4, CONTENT_TOP + 3.2, panel_w - 0.8, 2.0,
            lines=[
                (f"Sector: {sector_name}", FONT_BODY, COLOR_MUTED, False),
                ("", Pt(4), COLOR_DIM, False),
                ("Weight Basis:", FONT_CAPTION, COLOR_DIM, True),
                ("Profitability 30% | Solvency 20%", FONT_CAPTION, COLOR_DIM, False),
                ("Liquidity 15% | Efficiency 15%", FONT_CAPTION, COLOR_DIM, False),
                ("Growth 20%", FONT_CAPTION, COLOR_DIM, False),
            ]
        )

    # ── Right Panel: Pillar Progress Bars ─────────────────────────────────
    right_x = left_x + panel_w + 0.3
    right_w = 6.8
    add_card(slide, right_x, CONTENT_TOP + 0.1, right_w, panel_h, COLOR_BORDER)

    add_text_block(
        slide, right_x + 0.35, CONTENT_TOP + 0.3, right_w - 0.7, 0.3,
        "PILLAR BREAKDOWN", font_size=FONT_H3, font_color=COLOR_MUTED, bold=True
    )

    # Render progress bars for each pillar
    bar_start_y = CONTENT_TOP + 0.8
    bar_width = 3.5
    bar_x = right_x + 1.8

    for i, (p_name, p_col, p_weight) in enumerate(PILLAR_CONFIG):
        score = pillar_scores.get(p_name, 50.0)
        sc = health_color(score)
        label_text = health_label(score)
        y = bar_start_y + i * 0.95

        # Pillar name + weight
        add_text_block(
            slide, right_x + 0.35, y, 1.4, 0.25,
            f"{p_name}", font_size=Pt(10), font_color=COLOR_WHITE, bold=True
        )
        add_text_block(
            slide, right_x + 0.35, y + 0.22, 1.4, 0.2,
            f"{int(p_weight * 100)}% weight", font_size=FONT_CAPTION, font_color=COLOR_DIM
        )

        # Progress bar
        add_progress_bar(
            slide, bar_x, y + 0.08, bar_width, 0.16,
            value=score, fill_color=sc
        )

        # Score value
        add_text_block(
            slide, bar_x + bar_width + 0.15, y + 0.02, 0.7, 0.25,
            f"{score:.1f}", font_size=Pt(11), font_color=COLOR_WHITE, bold=True
        )

        # Status badge (small)
        add_badge(
            slide, bar_x + bar_width + 0.15, y + 0.3,
            label_text, sc, width=0.85, height=0.25
        )


# ============================================================================
# SLIDE 4: COMPETITIVE POSITIONING (RADAR)
# ============================================================================

def build_competitive_positioning(
    prs,
    client_name: str,
    pillar_df: pd.DataFrame,
) -> None:
    """Build the radar chart slide for competitive positioning."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide)
    add_slide_header(slide, "COMPETITIVE POSITIONING",
                     f"{client_name} pillar profile vs sector median")
    add_slide_footer(slide, 3, TOTAL_SLIDES)

    # Extract pillar scores
    client_scores = {}
    sector_medians = {}

    if pillar_df is not None and not pillar_df.empty:
        for p_name, p_col, _ in PILLAR_CONFIG:
            if p_col in pillar_df.columns:
                vals = pillar_df[p_col].dropna()
                if len(vals) > 0:
                    client_scores[p_name] = float(vals.values[0])
                    sector_medians[p_name] = float(vals.median())
                else:
                    client_scores[p_name] = 50.0
                    sector_medians[p_name] = 50.0
            else:
                client_scores[p_name] = 50.0
                sector_medians[p_name] = 50.0
    else:
        for p_name, _, _ in PILLAR_CONFIG:
            client_scores[p_name] = 50.0
            sector_medians[p_name] = 50.0

    # ── Main radar chart (left, perfectly square to prevent oval stretching) ─────────────────
    chart_path = render_pillar_radar(
        client_scores, sector_medians, client_name,
        fig_width=5.5, fig_height=5.5
    )
    _embed_chart(slide, chart_path, 1.0, 1.2, 5.5, 5.5)

    # ── Insight panel (right side) ────────────────────────────────────────
    panel_x = 8.5
    panel_w = 4.2
    add_card(slide, panel_x, CONTENT_TOP + 0.1, panel_w, 5.3, COLOR_BORDER)

    add_text_block(
        slide, panel_x + 0.3, CONTENT_TOP + 0.3, panel_w - 0.6, 0.3,
        "POSITIONING INSIGHTS", font_size=FONT_H3, font_color=COLOR_MUTED, bold=True
    )
    add_divider(slide, panel_x + 0.3, CONTENT_TOP + 0.65, panel_w - 0.6, COLOR_BORDER)

    # Find strongest and weakest pillars
    sorted_pillars = sorted(client_scores.items(), key=lambda x: x[1], reverse=True)
    strongest = sorted_pillars[0]
    weakest = sorted_pillars[-1]

    insight_y = CONTENT_TOP + 0.85

    # Strongest pillar
    add_text_block(
        slide, panel_x + 0.3, insight_y, panel_w - 0.6, 0.25,
        "STRONGEST PILLAR", font_size=Pt(9.0), font_color=COLOR_GREEN, bold=True
    )
    add_text_block(
        slide, panel_x + 0.3, insight_y + 0.25, panel_w - 0.6, 0.3,
        f"{strongest[0]}: {strongest[1]:.1f} / 100",
        font_size=Pt(12.5), font_color=COLOR_WHITE, bold=True
    )

    # Weakest pillar
    add_text_block(
        slide, panel_x + 0.3, insight_y + 0.8, panel_w - 0.6, 0.25,
        "WEAKEST PILLAR", font_size=Pt(9.0), font_color=COLOR_CORAL, bold=True
    )
    add_text_block(
        slide, panel_x + 0.3, insight_y + 1.05, panel_w - 0.6, 0.3,
        f"{weakest[0]}: {weakest[1]:.1f} / 100",
        font_size=Pt(12.5), font_color=COLOR_WHITE, bold=True
    )

    add_divider(slide, panel_x + 0.3, insight_y + 1.6, panel_w - 0.6, COLOR_BORDER)

    # Performance vs median summary
    add_text_block(
        slide, panel_x + 0.3, insight_y + 1.8, panel_w - 0.6, 0.25,
        "VS SECTOR MEDIAN", font_size=Pt(9.0), font_color=COLOR_TEAL, bold=True
    )

    above_count = sum(1 for p in client_scores if client_scores[p] > sector_medians.get(p, 50))
    below_count = len(client_scores) - above_count

    add_text_block(
        slide, panel_x + 0.3, insight_y + 2.1, panel_w - 0.6, 0.5,
        f"Above median: {above_count} pillars\nBelow median: {below_count} pillars",
        font_size=Pt(11.5), font_color=COLOR_WHITE
    )

    # Legend
    add_text_block(
        slide, panel_x + 0.3, insight_y + 3.0, panel_w - 0.6, 0.3,
        "LEGEND", font_size=Pt(8.5), font_color=COLOR_DIM, bold=True
    )
    add_text_block(
        slide, panel_x + 0.3, insight_y + 3.25, panel_w - 0.6, 0.5,
        f"-- Solid line: {client_name}\n-- Dashed line: Sector Median",
        font_size=Pt(9.0), font_color=COLOR_DIM
    )


# ============================================================================
# SLIDE 5: OUTLIER ANALYSIS & ANOMALY DETECTION
# ============================================================================

def build_outlier_analysis(
    prs,
    client_name: str,
    scorecard_df: pd.DataFrame,
    outlier_df: pd.DataFrame,
    anomaly_score: float,
) -> None:
    """Build the outlier analysis slide with lollipop chart and anomaly gauge."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide)
    add_slide_header(slide, "OUTLIER ANALYSIS & ANOMALY DETECTION")
    add_slide_footer(slide, 4, TOTAL_SLIDES)

    # ── Left Panel: Peer Deviations ───────────────────────────────────────
    left_x = 0.6
    left_w = 7.5
    panel_h = 5.3
    add_card(slide, left_x, CONTENT_TOP + 0.1, left_w, panel_h, COLOR_BORDER)

    add_text_block(
        slide, left_x + 0.35, CONTENT_TOP + 0.3, left_w - 0.7, 0.3,
        "CRITICAL PEER DEVIATIONS", font_size=FONT_H3, font_color=COLOR_MUTED, bold=True
    )
    add_divider(slide, left_x + 0.35, CONTENT_TOP + 0.6, left_w - 0.7, COLOR_BORDER)

    # Build deviation data for lollipop chart
    deviations = []
    if scorecard_df is not None and not scorecard_df.empty:
        extreme = scorecard_df[scorecard_df["position_label"].isin([
            "Below Benchmark", "Above Benchmark",
            "Near Benchmark (Low)", "Near Benchmark (High)"
        ])].copy()

        if "percentile_rank" in extreme.columns and not extreme.empty:
            extreme["abs_dist"] = (extreme["percentile_rank"] - 50.0).abs()
            extreme = extreme.sort_values("abs_dist", ascending=False)

            for _, row in extreme.head(6).iterrows():
                ratio_name = row["ratio"]
                label = row.get("ratio_label", ratio_name.replace("_", " ").title())
                label = label.replace("Roa", "ROA").replace("Roe", "ROE").replace("Roce", "ROCE").replace("Ocf", "OCF")
                raw_val = float(row["raw_value"])
                med_val = float(row["peer_median"])

                if med_val != 0:
                    dev_pct = ((raw_val - med_val) / abs(med_val)) * 100
                else:
                    dev_pct = 0.0

                pos_lbl = str(row.get("position_label", ""))
                is_below = "Below" in pos_lbl or "Low" in pos_lbl

                # Determine if deviation is positive for the company
                # The BenchmarkClassifier already inverts percentile ranks for ratios where high is bad (HIGH_IS_BAD),
                # meaning "Below Benchmark" (is_below = True) is always a negative/warning deviation,
                # and "Above/Near Benchmark" is always a positive deviation.
                is_positive = not is_below

                deviations.append({
                    "label": label,
                    "client_value": raw_val,
                    "peer_median": med_val,
                    "deviation_pct": dev_pct,
                    "is_positive": is_positive,
                })

    # Render lollipop chart (matching aspect ratio to prevent distortion)
    chart_path = render_outlier_lollipop(deviations, fig_width=7.1, fig_height=4.3)
    if chart_path:
        _embed_chart(slide, chart_path, left_x + 0.2, CONTENT_TOP + 0.8, 7.1, 4.3)
    else:
        # Fallback: text-based outlier list
        if deviations:
            items = []
            for d in deviations[:4]:
                symbol = "+" if d["is_positive"] else "!"
                sign = "+" if d["deviation_pct"] >= 0 else ""
                items.append((
                    d["label"],
                    f"{sign}{d['deviation_pct']:.0f}% vs peer median",
                    COLOR_GREEN if d["is_positive"] else COLOR_CORAL,
                ))
            add_bullet_list(
                slide, left_x + 0.35, CONTENT_TOP + 0.8, left_w - 0.7, 4.0,
                items=items
            )
        else:
            add_text_block(
                slide, left_x + 0.35, CONTENT_TOP + 1.0, left_w - 0.7, 0.5,
                f"No significant statistical outliers detected for {client_name}.",
                font_color=COLOR_MUTED, italic=True
            )

    # ── Right Panel: Anomaly Detector ─────────────────────────────────────
    right_x = left_x + left_w + 0.3
    right_w = 4.3
    add_card(slide, right_x, CONTENT_TOP + 0.1, right_w, panel_h, COLOR_BORDER)

    add_text_block(
        slide, right_x + 0.3, CONTENT_TOP + 0.3, right_w - 0.6, 0.3,
        "ISOLATION FOREST", font_size=FONT_H3, font_color=COLOR_MUTED, bold=True
    )
    add_text_block(
        slide, right_x + 0.3, CONTENT_TOP + 0.5, right_w - 0.6, 0.2,
        "ANOMALY DETECTOR", font_size=FONT_CAPTION, font_color=COLOR_DIM, bold=True
    )
    add_divider(slide, right_x + 0.3, CONTENT_TOP + 0.75, right_w - 0.6, COLOR_BORDER)

    # Anomaly gauge (matching aspect ratio to prevent dial compression)
    gauge_path = render_anomaly_gauge(anomaly_score, fig_width=3.5, fig_height=2.2)
    if gauge_path:
        _embed_chart(slide, gauge_path, right_x + 0.4, CONTENT_TOP + 0.9, 3.5, 2.2)
    else:
        # Fallback: text display
        score_str = f"{anomaly_score:.2f}" if not pd.isna(anomaly_score) else "N/A"
        add_kpi_block(
            slide, right_x + 0.3, CONTENT_TOP + 1.0, right_w - 0.6, 1.5,
            value=score_str,
            label="ANOMALY SCORE",
            value_color=COLOR_WHITE,
            alignment=PP_ALIGN.CENTER,
        )

    # Status badge
    if not pd.isna(anomaly_score):
        flag_text = "NORMAL PEER PATTERN"
        flag_color = COLOR_GREEN
        if anomaly_score >= 0.55:
            flag_text = "ANOMALOUS PATTERN"
            flag_color = COLOR_CORAL

        add_badge(
            slide, right_x + 0.8, CONTENT_TOP + 3.3,
            flag_text, flag_color, width=2.5, height=0.3
        )

    # Methodology note
    add_text_block(
        slide, right_x + 0.3, CONTENT_TOP + 3.85, right_w - 0.6, 0.2,
        "METHODOLOGY", font_size=FONT_CAPTION, font_color=COLOR_TEAL, bold=True
    )
    add_text_block(
        slide, right_x + 0.3, CONTENT_TOP + 4.1, right_w - 0.6, 1.0,
        "scikit-learn Isolation Forest isolates anomalous data points by "
        "randomly partitioning features. Scores closer to 1.0 indicate "
        "high multi-ratio deviation from peer norms.",
        font_size=FONT_CAPTION, font_color=COLOR_DIM, line_spacing=1.3
    )


# ============================================================================
# SLIDE 6: STRATEGIC SWOT MATRIX
# ============================================================================

def build_swot_matrix(
    prs,
    client_name: str,
    swot: Dict[str, List[Dict]],
) -> None:
    """Build the 2x2 SWOT matrix slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide)
    add_slide_header(slide, "STRATEGIC SWOT MATRIX",
                     f"Peer-benchmarked strategic assessment for {client_name}")
    add_slide_footer(slide, 5, TOTAL_SLIDES)

    # Grid layout
    card_w = 5.85
    card_h = 2.55
    row1_y = CONTENT_TOP + 0.15
    row2_y = row1_y + card_h + 0.2
    col1_x = 0.6
    col2_x = col1_x + card_w + 0.3

    quadrant_positions = [
        ("strengths",     col1_x, row1_y),
        ("weaknesses",    col2_x, row1_y),
        ("opportunities", col1_x, row2_y),
        ("threats",       col2_x, row2_y),
    ]

    for q_key, x, y in quadrant_positions:
        cfg = SWOT_CONFIG[q_key]
        color = cfg["color"]

        # Card with accent stripe
        add_card(slide, x, y, card_w, card_h, color,
                 accent_side=True, accent_color=color)

        # Quadrant header
        add_text_block(
            slide, x + 0.2, y + 0.12, card_w - 0.4, 0.25,
            cfg["title"], font_size=Pt(12), font_color=color, bold=True
        )
        add_text_block(
            slide, x + 0.2, y + 0.35, card_w - 0.4, 0.2,
            cfg["subtitle"], font_size=FONT_CAPTION, font_color=COLOR_DIM, italic=True
        )
        add_divider(slide, x + 0.2, y + 0.58, card_w - 0.4, color)

        # Items
        items = swot.get(q_key, [])[:3]
        n_items = len(items)
        if n_items == 0:
            add_text_block(
                slide, x + 0.2, y + 0.9, card_w - 0.4, 0.4,
                f"No active {cfg['title'].lower()} flagged in current scorecard.",
                font_color=COLOR_DIM, italic=True, font_size=Pt(12.5),
                alignment=PP_ALIGN.CENTER
            )
        else:
            # Dynamic configurations based on item count
            if n_items == 3:
                font_size_name = Pt(10.5)
                font_size_val = Pt(10.5)
                font_size_delta = Pt(9.5)
                item_spacing = 0.54
                start_y = y + 0.72
            elif n_items == 2:
                font_size_name = Pt(11.5)
                font_size_val = Pt(11.5)
                font_size_delta = Pt(10.5)
                item_spacing = 0.68
                start_y = y + 0.8
            else: # n_items == 1
                font_size_name = Pt(13.0)
                font_size_val = Pt(13.0)
                font_size_delta = Pt(11.5)
                item_spacing = 0.0
                start_y = y + 0.95

            item_y = start_y
            for item in items:
                # Ratio label + values
                raw_val = float(item["raw_value"])
                med_val = float(item["peer_median"])
                val_str = format_ratio_value(raw_val, item["ratio"])
                med_str = format_ratio_value(med_val, item["ratio"])

                # Delta percentage
                if med_val != 0:
                    delta = ((raw_val - med_val) / abs(med_val)) * 100
                    delta_str = f"  ({'+' if delta >= 0 else ''}{delta:.0f}% vs peer)"
                else:
                    delta_str = ""

                # Title line
                tx_box = slide.shapes.add_textbox(
                    Inches(x + 0.2), Inches(item_y),
                    Inches(card_w - 0.4), Inches(0.28)
                )
                tf = tx_box.text_frame
                tf.word_wrap = True
                tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

                p = tf.paragraphs[0]
                run_name = p.add_run()
                swot_label = item['ratio_label'].replace("Roa", "ROA").replace("Roe", "ROE").replace("Roce", "ROCE").replace("Ocf", "OCF")
                run_name.text = f"{swot_label}: "
                run_name.font.name = FONT_PRIMARY
                run_name.font.size = font_size_name
                run_name.font.bold = True
                run_name.font.color.rgb = COLOR_WHITE

                run_val = p.add_run()
                run_val.text = f"{val_str} vs {med_str}"
                run_val.font.name = FONT_PRIMARY
                run_val.font.size = font_size_val
                run_val.font.bold = False
                run_val.font.color.rgb = COLOR_TEAL

                run_delta = p.add_run()
                run_delta.text = delta_str
                run_delta.font.name = FONT_PRIMARY
                run_delta.font.size = font_size_delta
                run_delta.font.bold = True
                run_delta.font.color.rgb = color

                item_y += item_spacing


# ============================================================================
# SLIDE 7: AI STRATEGIC ACTION PLAN
# ============================================================================

def build_action_plan(
    prs,
    client_name: str,
    recommendations: List[str],
) -> None:
    """Build the 2x2 consulting-grade action plan grid."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide)
    add_slide_header(slide, "AI STRATEGIC ACTION PLAN",
                     f"Targeted recommendations for {client_name}")
    add_slide_footer(slide, 6, TOTAL_SLIDES)

    # Ensure exactly 4 recommendations
    recs = list(recommendations)
    while len(recs) < 4:
        recs.append("Conduct an internal strategic operational audit to identify efficiency improvements.")
    recs = recs[:4]

    # Grid layout
    card_w = 5.85
    card_h = 2.55
    row1_y = CONTENT_TOP + 0.15
    row2_y = row1_y + card_h + 0.2
    col1_x = 0.6
    col2_x = col1_x + card_w + 0.3

    positions = [
        (col1_x, row1_y),
        (col2_x, row1_y),
        (col1_x, row2_y),
        (col2_x, row2_y),
    ]

    for i, ((x, y), cfg) in enumerate(zip(positions, ACTION_PLAN_CONFIG)):
        color = cfg["color"]

        # Card with accent stripe
        add_card(slide, x, y, card_w, card_h, color,
                 accent_side=True, accent_color=color)

        # Large action number
        add_text_block(
            slide, x + 0.2, y + 0.1, 0.6, 0.4,
            cfg["number"], font_size=FONT_ACTION_NUMBER,
            font_color=color, bold=True
        )

        # Title
        add_text_block(
            slide, x + 0.8, y + 0.12, card_w - 1.0, 0.25,
            cfg["title"], font_size=Pt(11.5), font_color=color, bold=True
        )

        # Subtitle (lens)
        add_text_block(
            slide, x + 0.8, y + 0.35, card_w - 1.0, 0.2,
            cfg["subtitle"], font_size=FONT_CAPTION, font_color=COLOR_DIM, italic=True
        )

        # Thin divider
        add_divider(slide, x + 0.2, y + 0.6, card_w - 0.4, color)

        # Action text (clean markdown brackets and parse bold title)
        rec_text = recs[i]
        text = rec_text.strip()
        if text.startswith("[ ]"):
            text = text[3:].strip()
        elif text.startswith("[x]"):
            text = text[3:].strip()
            
        text = text.lstrip("*").lstrip("-").strip()
        
        bold_title = ""
        normal_desc = text
        
        if "**" in text:
            parts = text.split("**", 2)
            if len(parts) >= 3:
                bold_title = parts[1].strip()
                normal_desc = parts[2].strip()
                normal_desc = normal_desc.lstrip(":").lstrip(";").strip()
        elif ":" in text:
            parts = text.split(":", 1)
            if len(parts[0]) < 45:
                bold_title = parts[0].strip()
                normal_desc = parts[1].strip()
                
        rec_len = len(bold_title) + len(normal_desc) if bold_title else len(text)

        if rec_len < 90:
            rec_font_size = Pt(13.0)
            rec_line_spacing = 1.35
            rec_y = y + 0.85
        elif rec_len < 140:
            rec_font_size = Pt(11.5)
            rec_line_spacing = 1.28
            rec_y = y + 0.78
        elif rec_len < 190:
            rec_font_size = Pt(10.5)
            rec_line_spacing = 1.22
            rec_y = y + 0.73
        else:
            rec_font_size = Pt(9.5)
            rec_line_spacing = 1.16
            rec_y = y + 0.68

        # Create text box directly for multi-run formatting support
        tx_box = slide.shapes.add_textbox(
            Inches(x + 0.2), Inches(rec_y),
            Inches(card_w - 0.4), Inches(card_h - 0.9)
        )
        tf = tx_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        p.line_spacing = rec_line_spacing
        
        if bold_title:
            run_bold = p.add_run()
            run_bold.text = f"{bold_title}: "
            run_bold.font.name = FONT_PRIMARY
            run_bold.font.size = rec_font_size
            run_bold.font.bold = True
            run_bold.font.color.rgb = color
            
            run_normal = p.add_run()
            run_normal.text = normal_desc
            run_normal.font.name = FONT_PRIMARY
            run_normal.font.size = rec_font_size
            run_normal.font.bold = False
            run_normal.font.color.rgb = COLOR_WHITE
        else:
            run_normal = p.add_run()
            run_normal.text = text
            run_normal.font.name = FONT_PRIMARY
            run_normal.font.size = rec_font_size
            run_normal.font.bold = False
            run_normal.font.color.rgb = COLOR_WHITE


# ============================================================================
# SLIDE 8: RATIO DETAIL APPENDIX + CLOSING
# ============================================================================

def build_ratio_appendix(
    prs,
    client_name: str,
    scorecard_df: pd.DataFrame,
    peer_stats_df: pd.DataFrame = None,
) -> None:
    """Build the data appendix slide with formatted ratio table."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide)
    add_slide_header(slide, "APPENDIX: RATIO DETAIL TABLE",
                     "Complete peer benchmark data for due diligence")
    add_slide_footer(slide, 7, TOTAL_SLIDES)

    if scorecard_df is None or scorecard_df.empty:
        add_text_block(
            slide, 0.6, CONTENT_TOP + 0.5, 12.0, 0.5,
            "No ratio data available for this analysis.",
            font_color=COLOR_MUTED, italic=True
        )
        return

    # Prepare table data from scorecard
    headers = ["Ratio", "Client", "Median", "P25", "P75", "Pctl", "Status"]
    col_widths = [4.1, 1.3, 1.3, 1.3, 1.3, 1.2, 1.63]

    rows = []
    row_colors_list = []

    # Sort by pillar for grouping
    sorted_df = scorecard_df.copy()
    if "pillar" in sorted_df.columns:
        pillar_order = {"Profitability": 0, "Solvency": 1, "Liquidity": 2, "Efficiency": 3, "Growth": 4}
        sorted_df["_sort"] = sorted_df["pillar"].map(pillar_order).fillna(5)
        sorted_df = sorted_df.sort_values("_sort")

    for _, row in sorted_df.iterrows():
        ratio_name = row["ratio"]
        label = row.get("ratio_label", ratio_name.replace("_", " ").title())
        label = label.replace("Roa", "ROA").replace("Roe", "ROE").replace("Roce", "ROCE").replace("Ocf", "OCF")
        raw = float(row["raw_value"])
        med = float(row["peer_median"])
        q1 = float(row.get("peer_q1", np.nan))
        q3 = float(row.get("peer_q3", np.nan))
        pctl = float(row.get("percentile_rank", np.nan))
        pos = str(row.get("position_label", ""))

        suffix = "%" if is_percentage_ratio(ratio_name) else "x"

        # Format values with strict NaN checks
        if pd.isna(raw) or np.isnan(raw):
            raw_str = "N/A"
        else:
            raw_str = f"{raw:.1f}{suffix}"

        if pd.isna(med) or np.isnan(med):
            med_str = "N/A"
        else:
            med_str = f"{med:.1f}{suffix}"

        if pd.isna(q1) or np.isnan(q1):
            q1_str = "N/A"
        else:
            q1_str = f"{q1:.1f}"

        if pd.isna(q3) or np.isnan(q3):
            q3_str = "N/A"
        else:
            q3_str = f"{q3:.1f}"

        if pd.isna(pctl) or np.isnan(pctl):
            pctl_str = "N/A"
        else:
            pctl_str = f"P{pctl:.0f}"

        # Status indicator with professional descriptive labels
        if pd.isna(raw) or pd.isna(med):
            status = "N/A"
            status_color = COLOR_DIM
        elif "Above" in pos or "High" in pos:
            status = "Above Peer"
            status_color = COLOR_GREEN
        elif "Below" in pos or "Low" in pos:
            status = "Below Peer"
            status_color = COLOR_CORAL
        else:
            status = "In Line"
            status_color = COLOR_YELLOW

        rows.append([
            label,
            raw_str,
            med_str,
            q1_str,
            q3_str,
            pctl_str,
            status,
        ])

        # Color for each cell
        row_colors_list.append([
            COLOR_WHITE,      # Ratio name
            COLOR_WHITE,      # Client value
            COLOR_MUTED,      # Median
            COLOR_DIM,        # P25
            COLOR_DIM,        # P75
            COLOR_TEAL,       # Percentile
            status_color,     # Status
        ])

    table_bottom_y = add_data_table(
        slide, 0.6, CONTENT_TOP + 0.2,
        col_widths=col_widths,
        headers=headers,
        rows=rows,
        row_colors=row_colors_list,
        max_rows=14,
    )

    # Explanatory Legend Panel (3-column layout below data table)
    legend_y = table_bottom_y + 0.15
    add_divider(slide, 0.6, legend_y, 11.833, COLOR_BORDER)
    
    # Legend Col 1: Client Values
    add_multiline_text(
        slide, 0.6, legend_y + 0.15, 4.3, 0.75,
        lines=[
            ("CLIENT COLUMN VALUES", Pt(8.5), COLOR_TEAL, True),
            ("Margins & returns (Profitability, ROA, ROE) are shown as percentage (%) of sales/assets/equity. Leverage, liquidity, and speed are shown as multipliers (x).", Pt(8.0), COLOR_DIM, False)
        ]
    )
    
    # Legend Col 2: Percentile Rank
    add_multiline_text(
        slide, 5.1, legend_y + 0.15, 3.8, 0.75,
        lines=[
            ("PERCENTILE RANK (PCTL)", Pt(8.5), COLOR_TEAL, True),
            ("Indicates rank in peer group. For example, P75 means client performs better than 75% of peers, while P25 means client performs better than 25% of peers.", Pt(8.0), COLOR_DIM, False)
        ]
    )
    
    # Legend Col 3: Status Labels
    add_multiline_text(
        slide, 9.1, legend_y + 0.15, 3.3, 0.75,
        lines=[
            ("STATUS CLASSIFICATION", Pt(8.5), COLOR_TEAL, True),
            ("Above Peer: exceptional relative to median.\nBelow Peer: potential area of concern or elevated risk.\nIn Line: benchmark-aligned performance.", Pt(8.0), COLOR_DIM, False)
        ]
    )

    # Source attribution (shifted down safely to avoid overlap)
    add_text_block(
        slide, 0.6, 6.8, 12.0, 0.25,
        "Source: FinMetrics Suite analytical engine  |  Methodology: Peer benchmark with IQR/Z-score outlier detection",
        font_size=FONT_CAPTION, font_color=COLOR_DIM, italic=True
    )


def build_closing_slide(prs) -> None:
    """Build the closing/disclaimer slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide)

    # Top accent stripe
    top_bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0), Inches(0), Inches(SLIDE_WIDTH), Inches(STRIPE_HEIGHT)
    )
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = COLOR_TEAL
    top_bar.line.fill.background()

    # Bottom accent stripe
    bot_bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0), Inches(7.44), Inches(SLIDE_WIDTH), Inches(STRIPE_HEIGHT)
    )
    bot_bar.fill.solid()
    bot_bar.fill.fore_color.rgb = COLOR_TEAL
    bot_bar.line.fill.background()

    # Title
    add_multiline_text(
        slide, 2.0, 2.0, 9.333, 0.8,
        lines=[
            ("FINMETRICS SUITE", Pt(32), COLOR_WHITE, True),
        ],
        alignment=PP_ALIGN.CENTER,
    )
    add_divider(slide, 4.5, 2.9, 4.333, COLOR_TEAL)

    # Thank you message
    add_multiline_text(
        slide, 2.0, 3.2, 9.333, 1.2,
        lines=[
            ("Thank you for reviewing this", Pt(14), COLOR_MUTED, False),
            ("executive diagnostic briefing.", Pt(14), COLOR_MUTED, False),
            ("", Pt(8), COLOR_DIM, False),
            ("For questions or follow-up analysis,", Pt(11), COLOR_DIM, False),
            ("contact your FinMetrics Suite administrator.", Pt(11), COLOR_DIM, False),
        ],
        alignment=PP_ALIGN.CENTER,
    )

    # Disclaimer
    add_divider(slide, 2.5, 5.0, 8.333, COLOR_BORDER)
    add_text_block(
        slide, 2.0, 5.2, 9.333, 1.5,
        "DISCLAIMER: This report is generated by automated financial analytics. "
        "All ratios are computed from publicly available or client-provided data. "
        "This does not constitute financial advice. Past performance is not "
        "indicative of future results.",
        font_size=FONT_CAPTION, font_color=COLOR_DIM, italic=True,
        alignment=PP_ALIGN.CENTER, line_spacing=1.4
    )

    add_slide_footer(slide, 8, TOTAL_SLIDES)
