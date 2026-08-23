"""
report_generator.py
===================
Generates:
  - SWOT-classified strategic insights for a single client
  - Excel report (multi-sheet) with correct hierarchy
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

import pandas as pd
import numpy as np

from modules.utils import OUTPUTS_REPORTS

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# SWOT CLASSIFICATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

# Which financial pillar each ratio belongs to
_RATIO_TO_PILLAR: Dict[str, str] = {
    # Profitability
    "gross_margin":        "Profitability",
    "operating_margin":    "Profitability",
    "net_margin":          "Profitability",
    "roe":                 "Profitability",
    "roa":                 "Profitability",
    "roce":                "Profitability",
    # Liquidity
    "current_ratio":       "Liquidity",
    "quick_ratio":         "Liquidity",
    "cash_ratio":          "Liquidity",
    # Solvency
    "debt_to_equity":      "Solvency",
    "debt_ratio":          "Solvency",
    "interest_coverage":   "Solvency",
    # Efficiency
    "asset_turnover":      "Efficiency",
    "inventory_turnover":  "Efficiency",
    "receivables_turnover":"Efficiency",
    # Growth
    "revenue_growth":      "Growth",
    "net_income_growth":   "Growth",
    "ocf_growth":          "Growth",
    # Cash Flow
    "operating_cf_ratio":  "CashFlow",
    "fcf_margin":          "CashFlow",
    "cash_conversion":     "CashFlow",
}

# Pillars whose strong performance → Strengths, weak → Weaknesses (internal)
_INTERNAL_PILLARS = {"Profitability", "Efficiency", "CashFlow"}

# Pillars whose strong performance → Opportunities, weak → Threats (external/risk)
_RISK_PILLARS = {"Solvency", "Liquidity"}

# Growth is hybrid: strong → Strength, weak → Threat
_GROWTH_PILLARS = {"Growth"}

# Health labels considered strong (top performance)
_STRONG_LABELS = {"Elite", "Strong", "Healthy"}

# Health labels considered weak (underperformance)
_WEAK_LABELS = {"Weak", "Critical"}

# ─────────────────────────────────────────────────────────────────────────────
# NARRATIVE TEMPLATES  (keyed by quadrant → pillar)
# ─────────────────────────────────────────────────────────────────────────────
_NARRATIVE_TEMPLATES: Dict[str, Dict[str, str]] = {
    "Strengths": {
        "Profitability": (
            "{label} {ratio_label} ({raw:.2f} vs Peer Median {med:.2f}, P{pct:.0f}) — "
            "demonstrates strong earnings power relative to the industry."
        ),
        "Efficiency": (
            "{label} {ratio_label} ({raw:.2f} vs Peer Median {med:.2f}, P{pct:.0f}) — "
            "indicates superior asset utilization and operational throughput."
        ),
        "CashFlow": (
            "{label} {ratio_label} ({raw:.2f} vs Peer Median {med:.2f}, P{pct:.0f}) — "
            "signals robust cash generation capability after capital requirements."
        ),
        "Growth": (
            "{label} {ratio_label} ({raw:.2f} vs Peer Median {med:.2f}, P{pct:.0f}) — "
            "suggests the business is scaling effectively and capturing market share."
        ),
    },
    "Weaknesses": {
        "Profitability": (
            "{label} {ratio_label} ({raw:.2f} vs Peer Median {med:.2f}, P{pct:.0f}) — "
            "margin compression may indicate cost structure inefficiencies or pricing pressure."
        ),
        "Efficiency": (
            "{label} {ratio_label} ({raw:.2f} vs Peer Median {med:.2f}, P{pct:.0f}) — "
            "lower turnover signals under-utilization of assets or slow collection/inventory cycles."
        ),
        "CashFlow": (
            "{label} {ratio_label} ({raw:.2f} vs Peer Median {med:.2f}, P{pct:.0f}) — "
            "weak cash conversion could constrain reinvestment and dividend capacity."
        ),
    },
    "Opportunities": {
        "Solvency": (
            "{label} {ratio_label} ({raw:.2f} vs Peer Median {med:.2f}, P{pct:.0f}) — "
            "conservative leverage provides untapped borrowing capacity for strategic expansion."
        ),
        "Liquidity": (
            "{label} {ratio_label} ({raw:.2f} vs Peer Median {med:.2f}, P{pct:.0f}) — "
            "excess liquidity buffer can be deployed for acquisitions or working capital optimization."
        ),
    },
    "Threats": {
        "Solvency": (
            "{label} {ratio_label} ({raw:.2f} vs Peer Median {med:.2f}, P{pct:.0f}) — "
            "elevated debt levels may constrain financial flexibility and increase default risk."
        ),
        "Liquidity": (
            "{label} {ratio_label} ({raw:.2f} vs Peer Median {med:.2f}, P{pct:.0f}) — "
            "insufficient liquid assets relative to near-term obligations — working capital gap risk."
        ),
        "Growth": (
            "{label} {ratio_label} ({raw:.2f} vs Peer Median {med:.2f}, P{pct:.0f}) — "
            "declining growth trajectory may signal market saturation or competitive displacement."
        ),
    },
}

# Fallback template for any pillar/quadrant not explicitly mapped
_FALLBACK_TEMPLATE = (
    "{label} {ratio_label} ({raw:.2f} vs Peer Median {med:.2f}, P{pct:.0f})."
)

# Human-readable ratio labels
_RATIO_DISPLAY: Dict[str, str] = {
    "gross_margin":        "Gross Margin",
    "operating_margin":    "Operating Margin",
    "net_margin":          "Net Margin",
    "roe":                 "Return on Equity",
    "roa":                 "Return on Assets",
    "roce":                "Return on Capital Employed",
    "current_ratio":       "Current Ratio",
    "quick_ratio":         "Quick Ratio",
    "cash_ratio":          "Cash Ratio",
    "debt_to_equity":      "Debt-to-Equity",
    "debt_ratio":          "Debt Ratio",
    "interest_coverage":   "Interest Coverage",
    "asset_turnover":      "Asset Turnover",
    "inventory_turnover":  "Inventory Turnover",
    "receivables_turnover":"Receivables Turnover",
    "revenue_growth":      "Revenue Growth",
    "net_income_growth":   "Net Income Growth",
    "ocf_growth":          "Operating Cash Flow Growth",
    "operating_cf_ratio":  "Operating CF Ratio",
    "fcf_margin":          "Free Cash Flow Margin",
    "cash_conversion":     "Cash Conversion",
}


def _build_narrative(quadrant: str, pillar: str, ratio: str,
                     raw: float, med: float, pct: float,
                     health_label: str) -> str:
    """Build a human-readable narrative sentence for a SWOT entry."""
    template = (
        _NARRATIVE_TEMPLATES
        .get(quadrant, {})
        .get(pillar, _FALLBACK_TEMPLATE)
    )
    ratio_label = _RATIO_DISPLAY.get(ratio, ratio.replace("_", " ").title())
    return template.format(
        label=health_label,
        ratio_label=ratio_label,
        raw=raw,
        med=med,
        pct=pct,
    )


def _classify_to_quadrant(pillar: str, health_label: str, position_label: str) -> Optional[str]:
    """
    Map a ratio to its SWOT quadrant based on pillar membership and health/position.
    Returns None if the ratio does not clearly belong to any quadrant (neutral zone).
    """
    is_strong = health_label in _STRONG_LABELS
    is_weak   = health_label in _WEAK_LABELS
    is_above  = "Above" in str(position_label)
    is_below  = "Below" in str(position_label)

    if pillar in _INTERNAL_PILLARS:
        if is_strong and is_above:
            return "Strengths"
        if is_weak and is_below:
            return "Weaknesses"

    elif pillar in _RISK_PILLARS:
        if is_strong:
            return "Opportunities"
        if is_weak:
            return "Threats"

    elif pillar in _GROWTH_PILLARS:
        if is_strong and is_above:
            return "Strengths"
        if is_weak and is_below:
            return "Threats"

    return None  # Moderate / At-Benchmark — not SWOT-material


class ReportGenerator:
    """Generates SWOT-classified strategic insights and Excel exports."""

    def generate_swot(
        self,
        client_scorecard: pd.DataFrame,
        client_name: str = "Client",
    ) -> Dict[str, List[Dict]]:
        """
        Classify each ratio in the client scorecard into a SWOT quadrant.

        Parameters
        ----------
        client_scorecard : pd.DataFrame
            The ratio_scorecard_df from ClientComparator (single client).
        client_name : str
            Display name of the client.

        Returns
        -------
        Dict with keys 'strengths', 'weaknesses', 'opportunities', 'threats',
        each containing a list of insight dicts.
        """
        swot: Dict[str, List[Dict]] = {
            "strengths":     [],
            "weaknesses":    [],
            "opportunities": [],
            "threats":       [],
        }

        if client_scorecard is None or client_scorecard.empty:
            return swot

        for _, row in client_scorecard.iterrows():
            ratio         = row.get("ratio", "")
            raw_val       = row.get("raw_value", np.nan)
            peer_med      = row.get("peer_median", np.nan)
            pct_rank      = row.get("percentile_rank", np.nan)
            health_label  = str(row.get("health_label", "No Data"))
            position_label = str(row.get("position_label", ""))

            # Skip if essential data is missing
            if pd.isna(raw_val) or pd.isna(peer_med) or pd.isna(pct_rank):
                continue
            if health_label == "No Data":
                continue

            pillar = _RATIO_TO_PILLAR.get(ratio)
            if pillar is None:
                continue

            quadrant = _classify_to_quadrant(pillar, health_label, position_label)
            if quadrant is None:
                continue  # Moderate zone — skip

            narrative = _build_narrative(
                quadrant, pillar, ratio,
                raw_val, peer_med, pct_rank, health_label,
            )

            swot[quadrant.lower()].append({
                "client":          client_name,
                "quadrant":        quadrant,
                "pillar":          pillar,
                "ratio":           ratio,
                "ratio_label":     _RATIO_DISPLAY.get(ratio, ratio),
                "raw_value":       raw_val,
                "peer_median":     peer_med,
                "percentile_rank": pct_rank,
                "health_label":    health_label,
                "position_label":  position_label,
                "narrative":       narrative,
            })

        # Sort each quadrant by percentile impact (most extreme first)
        for key in ("strengths", "opportunities"):
            swot[key].sort(key=lambda x: x["percentile_rank"], reverse=True)
        for key in ("weaknesses", "threats"):
            swot[key].sort(key=lambda x: x["percentile_rank"])

        logger.info(
            "SWOT generated for '%s': S=%d W=%d O=%d T=%d",
            client_name,
            len(swot["strengths"]),
            len(swot["weaknesses"]),
            len(swot["opportunities"]),
            len(swot["threats"]),
        )
        return swot

    def swot_to_dataframe(self, swot: Dict[str, List[Dict]]) -> pd.DataFrame:
        """Flatten the SWOT dict into a single DataFrame for export."""
        all_rows = []
        for quadrant_key in ("strengths", "weaknesses", "opportunities", "threats"):
            all_rows.extend(swot.get(quadrant_key, []))
        if not all_rows:
            return pd.DataFrame()
        return pd.DataFrame(all_rows)

    # ------------------------------------------------------------------
    # Legacy compatibility: explain_all still works for Phase-1 peer data
    # ------------------------------------------------------------------
    def explain_all(self, ratio_scorecard_df: pd.DataFrame) -> pd.DataFrame:
        """Generate per-company statistical explanations (legacy, used by Export)."""
        all_rows: List[Dict] = []
        if ratio_scorecard_df is None or ratio_scorecard_df.empty:
            return pd.DataFrame()

        for _, row in ratio_scorecard_df.iterrows():
            r_dict = row.to_dict()
            ratio = r_dict.get("ratio", "")
            raw_val = r_dict.get("raw_value", np.nan)
            peer_med = r_dict.get("peer_median", np.nan)
            pos_label = str(r_dict.get("position_label", ""))
            ticker = r_dict.get("ticker", "")

            if pd.notna(raw_val) and pd.notna(peer_med) and pos_label != "No Data":
                tag = "[OPPORTUNITY]" if "Above" in pos_label else "[RISK]" if "Below" in pos_label else "[INFO]"
                cat = "Opportunity" if "Above" in pos_label else "Risk" if "Below" in pos_label else "Neutral"

                explanation_str = f"{tag} {ratio} is {pos_label.lower()} (Value: {raw_val:.2f} vs Peer Median: {peer_med:.2f})."

                all_rows.append({
                    "ticker": ticker,
                    "ratio": ratio,
                    "explanation": explanation_str,
                    "category": cat,
                    "source": "Statistical",
                })

        return pd.DataFrame(all_rows) if all_rows else pd.DataFrame()

    # ------------------------------------------------------------------
    # Excel Export
    # ------------------------------------------------------------------
    def export_excel(
        self,
        ratio_scorecard_df: pd.DataFrame,
        peer_stats_df: pd.DataFrame,
        outlier_df: pd.DataFrame,
        pillar_summary_df: pd.DataFrame,
        explanation_df: pd.DataFrame,
        sector: str = "Sector",
        filename: Optional[str] = None,
    ) -> Path:
        if filename is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_report_{sector.replace(' ', '_')}_{ts}.xlsx"

        OUTPUTS_REPORTS.mkdir(parents=True, exist_ok=True)
        path = OUTPUTS_REPORTS / filename

        with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
            wb = writer.book

            hdr_fmt = wb.add_format({
                "bold": True, "bg_color": "#1a1a2e", "font_color": "#e0e0e0",
                "border": 1, "align": "center",
            })

            if not ratio_scorecard_df.empty:
                self._write_sheet(writer, ratio_scorecard_df, "Ratio Scorecard", hdr_fmt)
            if not peer_stats_df.empty:
                self._write_sheet(writer, peer_stats_df, "Peer Benchmark", hdr_fmt)
            if not outlier_df.empty:
                self._write_sheet(writer, outlier_df, "Outliers", hdr_fmt)
            if not pillar_summary_df.empty:
                self._write_sheet(writer, pillar_summary_df, "Composite Scores", hdr_fmt)
            if not explanation_df.empty:
                self._write_sheet(writer, explanation_df, "Business Report", hdr_fmt)

            summary_data = {
                "Report Generated": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                "Sector": [sector],
                "Companies Analysed": [len(pillar_summary_df) if not pillar_summary_df.empty else 0],
            }
            self._write_sheet(writer, pd.DataFrame(summary_data), "Summary", hdr_fmt)

        logger.info("Excel report saved: %s", path)
        return path

    @staticmethod
    def _write_sheet(writer, df: pd.DataFrame, sheet_name: str, header_fmt) -> None:
        df.to_excel(writer, sheet_name=sheet_name, index=True)
        ws = writer.sheets[sheet_name]
        for col_num, value in enumerate(["Index"] + list(df.columns)):
            ws.write(0, col_num, value, header_fmt)
        ws.set_column(0, 0, 18)
        ws.set_column(1, len(df.columns), 14)