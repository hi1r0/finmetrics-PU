import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from scipy import stats

from modules.outlier_engine import HIGH_IS_BAD

logger = logging.getLogger(__name__)

class BenchmarkClassifier:
    """
    Classifies raw ratios into business-readable positions and health labels
    based on peer group statistics and percentile rankings.
    """

    HEALTH_THRESHOLDS = {
        # High is Better
        "gross_margin": [(75, "Elite"), (60, "Strong"), (40, "Healthy"), (25, "Moderate"), (10, "Weak"), (0, "Critical")],
        "operating_margin": [(75, "Elite"), (60, "Strong"), (40, "Healthy"), (25, "Moderate"), (10, "Weak"), (0, "Critical")],
        "net_margin": [(75, "Elite"), (60, "Strong"), (40, "Healthy"), (25, "Moderate"), (10, "Weak"), (0, "Critical")],
        "roe": [(75, "Elite"), (60, "Strong"), (40, "Healthy"), (25, "Moderate"), (10, "Weak"), (0, "Critical")],
        "roa": [(75, "Elite"), (60, "Strong"), (40, "Healthy"), (25, "Moderate"), (10, "Weak"), (0, "Critical")],
        "current_ratio": [(75, "Elite"), (60, "Strong"), (40, "Healthy"), (25, "Moderate"), (10, "Weak"), (0, "Critical")],
        "quick_ratio": [(75, "Elite"), (60, "Strong"), (40, "Healthy"), (25, "Moderate"), (10, "Weak"), (0, "Critical")],
        "cash_ratio": [(75, "Elite"), (60, "Strong"), (40, "Healthy"), (25, "Moderate"), (10, "Weak"), (0, "Critical")],
        "interest_coverage": [(75, "Elite"), (60, "Strong"), (40, "Healthy"), (25, "Moderate"), (10, "Weak"), (0, "Critical")],
        "asset_turnover": [(75, "Elite"), (60, "Strong"), (40, "Healthy"), (25, "Moderate"), (10, "Weak"), (0, "Critical")],
        "inventory_turnover": [(75, "Elite"), (60, "Strong"), (40, "Healthy"), (25, "Moderate"), (10, "Weak"), (0, "Critical")],
        "receivables_turnover": [(75, "Elite"), (60, "Strong"), (40, "Healthy"), (25, "Moderate"), (10, "Weak"), (0, "Critical")],
        "revenue_growth": [(75, "Elite"), (60, "Strong"), (40, "Healthy"), (25, "Moderate"), (10, "Weak"), (0, "Critical")],
        "net_income_growth": [(75, "Elite"), (60, "Strong"), (40, "Healthy"), (25, "Moderate"), (10, "Weak"), (0, "Critical")],
        "ocf_growth": [(75, "Elite"), (60, "Strong"), (40, "Healthy"), (25, "Moderate"), (10, "Weak"), (0, "Critical")],
        # Default for missing
        "default": [(75, "Elite"), (60, "Strong"), (40, "Healthy"), (25, "Moderate"), (10, "Weak"), (0, "Critical")]
    }

    POSITION_BANDS = [
        (80, "Above Benchmark", "positive"),
        (60, "Near Benchmark (High)", "positive"),
        (40, "At Benchmark", "neutral"),
        (20, "Near Benchmark (Low)", "warning"),
        (0, "Below Benchmark", "negative")
    ]

    @staticmethod
    def compute_percentile_rank(raw_value: float, peer_values: pd.Series, higher_is_better: bool = True) -> float:
        if pd.isna(raw_value) or peer_values.empty:
            return np.nan
        # Use rank logic or percentileofscore
        pct = stats.percentileofscore(peer_values.dropna(), raw_value, kind="rank")
        if not higher_is_better:
            pct = 100.0 - pct
        return pct

    @classmethod
    def health_label(cls, ratio: str, percentile_rank: float) -> str:
        if pd.isna(percentile_rank):
            return "No Data"
        thresholds = cls.HEALTH_THRESHOLDS.get(ratio, cls.HEALTH_THRESHOLDS["default"])
        for thresh, label in thresholds:
            if percentile_rank >= thresh:
                return label
        return "Critical"

    @classmethod
    def classify_ratio(cls, ratio: str, raw_value: float, peer_stats_row: pd.Series, peer_values: Optional[pd.Series] = None) -> dict:
        if pd.isna(raw_value):
            return {
                "ratio": ratio,
                "raw_value": np.nan,
                "peer_median": peer_stats_row.get("median", np.nan),
                "peer_q1": peer_stats_row.get("q1", np.nan),
                "peer_q3": peer_stats_row.get("q3", np.nan),
                "peer_p10": peer_stats_row.get("p10", np.nan),
                "peer_p90": peer_stats_row.get("p90", np.nan),
                "percentile_rank": np.nan,
                "position_label": "No Data",
                "health_label": "No Data",
                "signal": "neutral",
            }
            
        higher_is_better = ratio not in HIGH_IS_BAD
        
        if peer_values is not None and len(peer_values.dropna()) > 0:
            pct = cls.compute_percentile_rank(raw_value, peer_values, higher_is_better)
        else:
            # Approximate percentile if no raw peer values available
            med = peer_stats_row.get("median", raw_value)
            if pd.isna(med):
                pct = np.nan
            else:
                pct = 50.0 if raw_value == med else (75.0 if raw_value > med else 25.0)
                if not higher_is_better:
                    pct = 100.0 - pct

        health = cls.health_label(ratio, pct)
        
        pos_label = "Below Benchmark"
        signal = "negative"
        for thresh, label, sig in cls.POSITION_BANDS:
            if pct >= thresh:
                pos_label = label
                signal = sig
                break
                
        return {
            "ratio": ratio,
            "raw_value": raw_value,
            "peer_median": peer_stats_row.get("median", np.nan),
            "peer_q1": peer_stats_row.get("q1", np.nan),
            "peer_q3": peer_stats_row.get("q3", np.nan),
            "peer_p10": peer_stats_row.get("p10", np.nan),
            "peer_p90": peer_stats_row.get("p90", np.nan),
            "percentile_rank": pct,
            "position_label": pos_label,
            "health_label": health,
            "signal": signal,
        }

    @classmethod
    def classify_all(
        cls,
        target_matrix: pd.DataFrame,
        peer_stats_df: pd.DataFrame,
        is_outlier_df: Optional[pd.DataFrame] = None,
        peer_pool_matrix: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        if peer_pool_matrix is None:
            peer_pool_matrix = target_matrix

        results = []
        for ticker in target_matrix.index:
            for ratio in target_matrix.columns:
                if ratio not in peer_stats_df.index:
                    continue
                raw_val = target_matrix.at[ticker, ratio]
                peer_row = peer_stats_df.loc[ratio]
                
                # Check if this cell was excluded as an outlier in the original matrix
                is_excluded = False
                if is_outlier_df is not None and not is_outlier_df.empty:
                    # is_outlier_df contains rows with ticker, ratio
                    outliers = is_outlier_df[(is_outlier_df["ticker"] == ticker) & (is_outlier_df["ratio"] == ratio)]
                    is_excluded = len(outliers) > 0
                
                # For classification, we need the peer pool values to compute exact percentile
                peer_vals = peer_pool_matrix[ratio].dropna() if ratio in peer_pool_matrix.columns else target_matrix[ratio].dropna()
                res = cls.classify_ratio(ratio, raw_val, peer_row, peer_vals)
                res["ticker"] = ticker
                res["is_outlier_excluded"] = is_excluded
                results.append(res)
                
        if not results:
            return pd.DataFrame()
        return pd.DataFrame(results)
