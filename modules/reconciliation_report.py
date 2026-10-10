"""
reconciliation_report.py
========================
Generates audit trail artifacts (Excel exception sheets, JSON summaries)
from ReconciliationResult outputs.
"""

from pathlib import Path
import json
import logging
from typing import Optional, Union

import pandas as pd

from modules.reconciliation_engine import ReconciliationResult

logger = logging.getLogger(__name__)


class ReconciliationReporter:
    """
    Exports reconciliation results to Excel workbooks and JSON audit logs.
    """

    @staticmethod
    def export_excel(
        result: ReconciliationResult,
        output_path: Union[str, Path] = "outputs/reports/Reconciliation_Exception_Report.xlsx",
    ) -> Path:
        """
        Creates an executive Excel workbook with Summary, Matched Items, and Severity-Ranked Exceptions.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            # 1. Summary Sheet
            summary_rows = [
                {"Metric": "Total Records in System of Record (Source A)", "Value": result.total_records_a},
                {"Metric": "Total Records in Comparator (Source B)", "Value": result.total_records_b},
                {"Metric": "Overall Match Rate (%)", "Value": f"{result.match_rate:.2f}%"},
                {"Metric": "Auto-Resolved Rate (%)", "Value": f"{result.auto_resolved_rate:.2f}%"},
                {"Metric": "Review-Required Rate (%)", "Value": f"{result.review_required_rate:.2f}%"},
                {"Metric": "Exception Rate (%)", "Value": f"{result.exception_rate:.2f}%"},
                {"Metric": "Tier 1: Exact Matches", "Value": result.metrics_summary.get("tier_1_exact_count", 0)},
                {"Metric": "Tier 2: Fuzzy Matches", "Value": result.metrics_summary.get("tier_2_fuzzy_count", 0)},
                {"Metric": "Tier 3: Split Matches", "Value": result.metrics_summary.get("tier_3_split_count", 0)},
                {"Metric": "Partial Matches (Manual Review)", "Value": result.metrics_summary.get("partial_match_count", 0)},
                {"Metric": "Unresolved Exceptions", "Value": result.metrics_summary.get("unresolved_exceptions_count", 0)},
            ]
            pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Reconciliation Summary", index=False)

            # 2. Exceptions Sheet (Prioritized by Severity)
            if not result.exceptions_df.empty:
                exc_df = result.exceptions_df.copy()
                # Sort HIGH, MEDIUM, LOW
                sev_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "NONE": 3}
                exc_df["_sort"] = exc_df["severity"].map(lambda s: sev_order.get(s, 4))
                exc_df = exc_df.sort_values(by=["_sort", "amount_diff"], ascending=[True, False]).drop(columns=["_sort"])
                exc_df.to_excel(writer, sheet_name="Exceptions & Review", index=False)
            else:
                pd.DataFrame([{"Message": "Zero exceptions detected. 100% matched."}]).to_excel(
                    writer, sheet_name="Exceptions & Review", index=False
                )

            # 3. Matches Sheet
            if not result.matches_df.empty:
                result.matches_df.to_excel(writer, sheet_name="Matched Records", index=False)
            else:
                pd.DataFrame([{"Message": "No matched records."}]).to_excel(
                    writer, sheet_name="Matched Records", index=False
                )

        logger.info(f"Reconciliation Excel report exported: {path}")
        return path

    @staticmethod
    def export_json(
        result: ReconciliationResult,
        output_path: Union[str, Path] = "outputs/reports/reconciliation_result.json",
    ) -> Path:
        """
        Exports machine-readable audit trail JSON.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "metrics": result.metrics_summary,
            "matches": [m.to_dict() for m in result.matches],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        logger.info(f"Reconciliation JSON audit trail exported: {path}")
        return path
