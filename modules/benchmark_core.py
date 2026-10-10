import logging
from typing import Dict, List, NamedTuple, Optional

import numpy as np
import pandas as pd

from modules.benchmark_classifier import BenchmarkClassifier
from modules.benchmark_store import BenchmarkStore

logger = logging.getLogger(__name__)

# Reusing PILLARS and PILLAR_WEIGHTS from old scoring engine
PILLARS: Dict[str, List[tuple]] = {
    "Profitability": [
        ("gross_margin",     0.20, True),
        ("operating_margin", 0.25, True),
        ("net_margin",       0.25, True),
        ("roe",              0.15, True),
        ("roa",              0.15, True),
    ],
    "Liquidity": [
        ("current_ratio",  0.40, True),
        ("quick_ratio",    0.35, True),
        ("cash_ratio",     0.25, True),
    ],
    "Solvency": [
        ("debt_to_equity",    0.40, False),
        ("debt_ratio",        0.35, False),
        ("interest_coverage", 0.25, True),
    ],
    "Efficiency": [
        ("asset_turnover",       0.40, True),
        ("inventory_turnover",   0.30, True),
        ("receivables_turnover", 0.30, True),
    ],
    "Growth": [
        ("revenue_growth",     0.35, True),
        ("net_income_growth",  0.35, True),
        ("ocf_growth",         0.30, True),
    ],
}

PILLAR_WEIGHTS = {
    "Profitability": 0.30,
    "Liquidity":     0.15,
    "Solvency":      0.20,
    "Efficiency":    0.15,
    "Growth":        0.20,
}

RISK_CATEGORIES = [
    (80, "Excellent"),
    (65, "Strong"),
    (50, "Moderate"),
    (35, "Weak"),
    (0,  "Distressed"),
]

# Ratios that are raw monetary values (excluded from benchmarking)
_RAW_VALUE_COLS = {
    "total_revenue", "net_income", "ebitda",
    "operating_cashflow", "free_cashflow",
    "total_debt", "total_equity", "total_assets",
    "market_cap", "eps",
}


class BenchmarkCoreResult(NamedTuple):
    peer_stats_df: pd.DataFrame
    ratio_scorecard_df: pd.DataFrame
    pillar_summary_df: pd.DataFrame
    outlier_df: pd.DataFrame
    clean_matrix: pd.DataFrame


class BenchmarkCore:
    """
    Core Benchmark pipeline replacing BenchmarkEngine and ScoringEngine.
    Focuses on a ratio-first scorecard approach.
    """

    def __init__(
        self,
        pillars: Optional[Dict] = None,
        pillar_weights: Optional[Dict] = None,
    ) -> None:
        self.pillars = pillars or PILLARS
        self.pillar_weights = pillar_weights or PILLAR_WEIGHTS
        self.classifier = BenchmarkClassifier()

    def run(
        self,
        ratio_df: pd.DataFrame,
        outlier_df: pd.DataFrame,
    ) -> BenchmarkCoreResult:
        """
        Execute the full benchmark pipeline.
        """
        logger.info("BenchmarkCore pipeline: starting")

        # 1. Mask outliers (for peer benchmark calculation only)
        clean = self._mask_outliers(ratio_df, outlier_df)

        # 2. Compute canonical peer benchmark stats (outliers excluded)
        peer_stats = self._compute_peer_stats(clean)

        # 3. Classify raw ratios to create primary scorecard (raw values unmasked, peer pool masked)
        scorecard = self._build_ratio_scorecard(ratio_df, peer_stats, outlier_df, peer_pool_matrix=clean)

        # 4. Score pillars using percentiles
        pillar_summary = self._score_pillars(scorecard)

        # 5. Composite score, ranking, categorization
        pillar_summary = self._rank_categorize(pillar_summary)

        logger.info("BenchmarkCore pipeline: finished")

        return BenchmarkCoreResult(
            peer_stats_df=peer_stats,
            ratio_scorecard_df=scorecard,
            pillar_summary_df=pillar_summary,
            outlier_df=outlier_df,
            clean_matrix=clean,
        )

    @staticmethod
    def _mask_outliers(
        ratio_df: pd.DataFrame,
        outlier_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Replace outlier cells with NaN.
        """
        clean = ratio_df.copy()

        # Drop raw monetary columns
        ratio_cols = [c for c in clean.columns if c not in _RAW_VALUE_COLS]
        clean = clean[ratio_cols]

        # Replace inf with NaN
        clean = clean.replace([np.inf, -np.inf], np.nan)

        if outlier_df is None or outlier_df.empty:
            return clean

        # Mask each outlier cell
        for _, row in outlier_df.iterrows():
            ticker = row.get("ticker")
            ratio = row.get("ratio")
            if ticker in clean.index and ratio in clean.columns:
                clean.at[ticker, ratio] = np.nan

        clean.attrs = dict(ratio_df.attrs)
        return clean

    def _compute_peer_stats(self, clean_matrix: pd.DataFrame) -> pd.DataFrame:
        """
        For each ratio column, compute canonical stats.
        This represents the frozen benchmark for client ingestion.
        """
        stats_list = []
        for col in clean_matrix.columns:
            series = clean_matrix[col].dropna()
            
            n_peers = len(series)
            if n_peers == 0:
                continue

            stats_list.append({
                "ratio": col,
                "median": series.median(),
                "q1": series.quantile(0.25),
                "q3": series.quantile(0.75),
                "p10": series.quantile(0.10),
                "p90": series.quantile(0.90),
                "mean": series.mean(),
                "std": series.std(),
                "n_peers": n_peers,
                "n_excluded": 0,
            })
            
        stats_df = pd.DataFrame(stats_list)
        if not stats_df.empty:
            stats_df = stats_df.set_index("ratio")
            
        return stats_df

    def _build_ratio_scorecard(
        self,
        raw_matrix: pd.DataFrame,
        peer_stats_df: pd.DataFrame,
        outlier_df: pd.DataFrame,
        peer_pool_matrix: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Uses BenchmarkClassifier to create the primary scorecard.
        """
        if peer_pool_matrix is None:
            peer_pool_matrix = raw_matrix

        # Filter monetary/raw columns for target matrix
        ratio_cols = [c for c in raw_matrix.columns if c not in _RAW_VALUE_COLS]
        target_df = raw_matrix[ratio_cols]

        scorecard = self.classifier.classify_all(
            target_matrix=target_df,
            peer_stats_df=peer_stats_df,
            is_outlier_df=outlier_df,
            peer_pool_matrix=peer_pool_matrix,
        )
        if scorecard.empty:
            return scorecard
            
        # Attach pillar labels
        ratio_to_pillar = {}
        for pillar, metrics in self.pillars.items():
            for ratio, _, _ in metrics:
                ratio_to_pillar[ratio] = pillar
                
        scorecard["pillar"] = scorecard["ratio"].map(lambda r: ratio_to_pillar.get(r, "Other"))
        
        # Reorder columns
        cols = [
            "ticker", "pillar", "ratio", "raw_value",
            "peer_median", "peer_q1", "peer_q3", "peer_p10", "peer_p90",
            "percentile_rank", "position_label", "health_label", "signal",
            "is_outlier_excluded"
        ]
        return scorecard[cols]

    def _score_pillars(self, ratio_scorecard_df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate ratio percentile ranks into pillar scores (0-100)."""
        return score_pillars(ratio_scorecard_df, self.pillars)

    def _rank_categorize(self, pillar_summary_df: pd.DataFrame) -> pd.DataFrame:
        """Compute composite score, sector rank, percentile and risk category."""
        return rank_and_categorize(pillar_summary_df, self.pillar_weights)


# ---------------------------------------------------------------------------
# Module-level pure scoring functions (Shared between Core and Comparator)
# ---------------------------------------------------------------------------

def score_pillars(
    ratio_scorecard_df: pd.DataFrame,
    pillars: Optional[Dict] = None,
) -> pd.DataFrame:
    """
    Pure function: Aggregate ratio percentile ranks into pillar scores (0-100).
    """
    if ratio_scorecard_df.empty:
        return pd.DataFrame()

    pillars = pillars or PILLARS
    pct_df = ratio_scorecard_df.pivot(index="ticker", columns="ratio", values="percentile_rank")
    result = pd.DataFrame(index=pct_df.index)

    for pillar, metrics in pillars.items():
        col_name = f"{pillar.lower()}_score"
        available = [(col, w) for col, w, _ in metrics if col in pct_df.columns]
        if not available:
            result[col_name] = 50.0
            continue

        weighted_sum = pd.Series(0.0, index=pct_df.index)
        total_weight = pd.Series(0.0, index=pct_df.index)

        for col, weight in available:
            vals = pct_df[col]
            mask = vals.notna()
            weighted_sum += vals.fillna(0) * weight * mask.astype(float)
            total_weight += mask.astype(float) * weight

        result[col_name] = (weighted_sum / total_weight.replace(0, np.nan)).fillna(50.0).round(2)

    return result


def rank_and_categorize(
    pillar_summary_df: pd.DataFrame,
    pillar_weights: Optional[Dict[str, float]] = None,
) -> pd.DataFrame:
    """
    Pure function: Compute composite score, sector rank, percentile and risk category.
    """
    if pillar_summary_df.empty:
        return pillar_summary_df

    pillar_weights = pillar_weights or PILLAR_WEIGHTS
    df = pillar_summary_df.copy()

    composite = pd.Series(0.0, index=df.index)
    total_weight = 0.0

    for pillar, weight in pillar_weights.items():
        col_name = f"{pillar.lower()}_score"
        if col_name in df.columns:
            composite += df[col_name] * weight
            total_weight += weight

    if total_weight > 0:
        composite = composite / total_weight

    df["composite_score"] = composite.round(2)
    df["sector_rank"] = df["composite_score"].rank(ascending=False, method="min").astype(int)

    n = len(df)
    df["percentile"] = (((n - df["sector_rank"]) / max(n - 1, 1)) * 100).round(1)

    def get_risk(score):
        for threshold, label in RISK_CATEGORIES:
            if score >= threshold:
                return label
        return "Distressed"

    df["risk_category"] = df["composite_score"].apply(get_risk)

    lead_cols = ["composite_score", "sector_rank", "percentile", "risk_category"]
    pillar_cols = [c for c in df.columns if c.endswith("_score") and c != "composite_score"]

    df = df[lead_cols + sorted(pillar_cols)]
    df = df.reset_index()
    if "index" in df.columns:
        df = df.rename(columns={"index": "ticker"})

    return df
