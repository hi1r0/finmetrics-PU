"""
report_generator.py
===================
Generates:
  - Statistical ratio explanations
  - Excel benchmark report (multi-sheet) with sector quartile stats and outlier summaries
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

import pandas as pd
import numpy as np

from modules.utils import OUTPUTS_REPORTS

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates statistical ratio explanations and Excel benchmark exports."""

    def explain_all(self, ratio_scorecard_df: pd.DataFrame) -> pd.DataFrame:
        """Generate per-company statistical explanations for ratios."""
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
        """Export comprehensive benchmark analysis to a multi-sheet Excel file."""
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