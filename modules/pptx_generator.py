"""
pptx_generator.py
=================
Slim orchestrator for generating institutional-grade PowerPoint (.pptx)
presentations from FinMetrics Suite benchmark and diagnostic data.

This module coordinates the modular PPTX generation pipeline:
  - pptx_design_tokens.py  (color, font, spacing constants)
  - pptx_components.py     (reusable shape builders)
  - pptx_charts.py         (matplotlib chart renderers)
  - pptx_slides.py         (individual slide builder functions)

The public API (generate_presentation) remains backward-compatible with
the original monolithic implementation.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

try:
    from pptx import Presentation
    from pptx.util import Inches
except ImportError:
    raise ImportError(
        "The 'python-pptx' library is required to use this module. "
        "Install it via: pip install python-pptx"
    )

from modules.utils import OUTPUTS_REPORTS
from modules.pptx_design_tokens import SLIDE_WIDTH, SLIDE_HEIGHT
from modules.pptx_slides import (
    build_title_slide,
    build_executive_summary,
    build_pillar_scorecard,
    build_competitive_positioning,
    build_outlier_analysis,
    build_swot_matrix,
    build_action_plan,
    build_ratio_appendix,
    build_closing_slide,
    _cleanup_temp_charts,
)

logger = logging.getLogger(__name__)


class PPTXGenerator:
    """
    Generates institutional-grade widescreen (16:9) PowerPoint decks from
    benchmark and client scorecard results, matching the Abyss Teal dark theme.

    Usage:
        gen = PPTXGenerator()
        path = gen.generate_presentation(
            client_name="Acme Corp",
            sector_name="Technology",
            scorecard_df=result.ratio_scorecard_df,
            pillar_summary_df=result.pillar_summary_df,
            outlier_df=result.outlier_df,
            swot=swot_dict,
            recommendations=["Action 1", "Action 2", "Action 3", "Action 4"],
            anomaly_score=0.42,
        )
    """

    def __init__(self) -> None:
        pass

    def generate_presentation(
        self,
        client_name: str,
        sector_name: str,
        scorecard_df: pd.DataFrame,
        pillar_summary_df: pd.DataFrame,
        outlier_df: pd.DataFrame,
        swot: Dict[str, List[Dict]],
        recommendations: List[str],
        anomaly_score: float = np.nan,
        filename: Optional[str] = None,
        peer_stats_df: Optional[pd.DataFrame] = None,
    ) -> Path:
        """
        Main entry point. Compiles an 8-slide institutional-grade dark-mode
        executive briefing deck.

        Parameters
        ----------
        client_name : str
            Display name of the client company.
        sector_name : str
            Name of the benchmarking peer sector.
        scorecard_df : pd.DataFrame
            Client scorecard containing ratios and percentile ranks.
        pillar_summary_df : pd.DataFrame
            Pillar and composite scores for the client.
        outlier_df : pd.DataFrame
            Detailed sector outlier flags.
        swot : Dict[str, List[Dict]]
            SWOT quadrants containing structured insights.
        recommendations : List[str]
            AI strategic actions (exactly 4 items corresponding to the 4 lenses).
        anomaly_score : float
            Multivariate anomaly score from Isolation Forest.
        filename : Optional[str]
            Target output filename. Auto-generated if None.
        peer_stats_df : Optional[pd.DataFrame]
            Per-ratio peer statistics (median, q1, q3, etc.) for the appendix.

        Returns
        -------
        Path
            Absolute path to the created .pptx file.
        """
        OUTPUTS_REPORTS.mkdir(parents=True, exist_ok=True)

        if filename is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = client_name.replace(" ", "_").replace("/", "_")
            filename = f"executive_briefing_{safe_name}_{ts}.pptx"
        path = OUTPUTS_REPORTS / filename

        # Initialize presentation
        prs = Presentation()
        prs.slide_width = Inches(SLIDE_WIDTH)
        prs.slide_height = Inches(SLIDE_HEIGHT)

        try:
            # ── Slide 1: Title / Cover ────────────────────────────────────
            build_title_slide(prs, client_name, sector_name)

            # ── Slide 2: Executive Summary ────────────────────────────────
            build_executive_summary(prs, client_name, sector_name,
                                    pillar_summary_df, swot)

            # ── Slide 3: Pillar Performance Scorecard ─────────────────────
            build_pillar_scorecard(prs, client_name, sector_name,
                                   pillar_summary_df)

            # ── Slide 4: Competitive Positioning (Radar) ──────────────────
            build_competitive_positioning(prs, client_name, pillar_summary_df)

            # ── Slide 5: Outlier Analysis & Anomaly Detection ─────────────
            build_outlier_analysis(prs, client_name, scorecard_df,
                                   outlier_df, anomaly_score)

            # ── Slide 6: Strategic SWOT Matrix ────────────────────────────
            build_swot_matrix(prs, client_name, swot)

            # ── Slide 7: AI Strategic Action Plan ─────────────────────────
            build_action_plan(prs, client_name, recommendations)

            # ── Slide 8: Ratio Detail Appendix + Closing ──────────────────
            build_ratio_appendix(prs, client_name, scorecard_df, peer_stats_df)

            # ── Slide 9: Closing / Disclaimer ─────────────────────────────
            build_closing_slide(prs)

            # Save presentation
            prs.save(str(path))
            logger.info("PowerPoint Executive Briefing saved to: %s", path)

        finally:
            # Clean up temporary chart image files
            _cleanup_temp_charts()

        return path
