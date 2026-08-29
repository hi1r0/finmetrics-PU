"""
outlier_engine.py
=================
Statistical outlier detection using IQR, Z-score, and Isolation Forest.
Returns structured results with severity scores and directional flags.
"""

import logging
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

logger = logging.getLogger(__name__)

# Ratios where a HIGH value is BAD (negative outlier = red flag)
HIGH_IS_BAD = {
    "debt_to_equity", "debt_ratio", "total_debt",
    "pe_ratio", "pb_ratio", "ev_ebitda",
}

# Ratios where a LOW value is BAD
LOW_IS_BAD = {
    "current_ratio", "quick_ratio", "cash_ratio",
    "interest_coverage", "gross_margin", "operating_margin",
    "net_margin", "roe", "roa", "roce",
    "operating_cf_ratio", "fcf_margin",
    "revenue_growth", "net_income_growth",
}

# Human-readable ratio labels
RATIO_LABELS: Dict[str, str] = {
    "current_ratio": "Current Ratio",
    "quick_ratio": "Quick Ratio",
    "cash_ratio": "Cash Ratio",
    "debt_to_equity": "Debt / Equity",
    "debt_ratio": "Debt Ratio",
    "interest_coverage": "Interest Coverage",
    "gross_margin": "Gross Margin (%)",
    "operating_margin": "Operating Margin (%)",
    "net_margin": "Net Margin (%)",
    "roe": "ROE (%)",
    "roa": "ROA (%)",
    "roce": "ROCE (%)",
    "asset_turnover": "Asset Turnover",
    "inventory_turnover": "Inventory Turnover",
    "receivables_turnover": "Receivables Turnover",
    "operating_cf_ratio": "Operating CF Ratio",
    "fcf_margin": "FCF Margin (%)",
    "cash_conversion": "Cash Conversion Ratio",
    "pe_ratio": "P/E Ratio",
    "pb_ratio": "P/B Ratio",
    "ev_ebitda": "EV/EBITDA",
    "revenue_growth": "Revenue Growth (%)",
    "net_income_growth": "Net Income Growth (%)",
    "ebitda_growth": "EBITDA Growth (%)",
    "ocf_growth": "OCF Growth (%)",
}


class OutlierEngine:
    """
    Detects outliers across a peer-group ratio matrix.

    Parameters
    ----------
    iqr_multiplier : float
        Tukey fence multiplier (default 1.5).
    zscore_threshold : float
        |Z-score| beyond which a value is flagged (default 2.5).
    min_peers : int
        Minimum peers needed to run cross-sectional analysis.
    """

    def __init__(
        self,
        iqr_multiplier: float = 1.5,
        zscore_threshold: float = 2.5,
        min_peers: int = 3,
    ) -> None:
        self.iqr_multiplier = iqr_multiplier
        self.zscore_threshold = zscore_threshold
        self.min_peers = min_peers

    # ── Public API ────────────────────────────────────────────────────────────

    def detect(self, ratio_matrix: pd.DataFrame) -> pd.DataFrame:
        """
        Run full outlier detection on a ratio matrix.

        Parameters
        ----------
        ratio_matrix : DataFrame
            rows = tickers, columns = ratio names

        Returns
        -------
        DataFrame of outlier records with columns:
          ticker, ratio, value, sector_median, sector_mean,
          q1, q3, lower_bound, upper_bound,
          zscore, iqr_flag, zscore_flag,
          deviation_pct, severity_score,
          direction, is_positive_outlier, label
        """
        records: List[Dict] = []

        # Work only on numeric ratio columns (exclude raw monetary values)
        ratio_cols = [
            c for c in ratio_matrix.columns
            if c not in {"total_revenue", "net_income", "ebitda",
                         "operating_cashflow", "free_cashflow",
                         "total_debt", "total_equity", "total_assets",
                         "market_cap", "eps"}
        ]

        for ratio in ratio_cols:
            col = ratio_matrix[ratio].dropna()
            if len(col) < self.min_peers:
                continue

            q1, q3 = col.quantile(0.25), col.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - self.iqr_multiplier * iqr
            upper = q3 + self.iqr_multiplier * iqr
            median = col.median()
            mean = col.mean()

            # Modified Z-scores (robust)
            mad = (col - median).abs().median()
            if mad == 0:
                std = col.std()
                if pd.isna(std) or std == 0:
                    zscore_series = pd.Series(0.0, index=col.index)
                else:
                    zscore_series = (col - mean) / std
            else:
                zscore_series = 0.6745 * (col - median) / mad

            for ticker in ratio_matrix.index:
                val = ratio_matrix.at[ticker, ratio]
                if pd.isna(val):
                    continue

                iqr_flag = bool(val < lower or val > upper)
                z = float(zscore_series.get(ticker, 0.0))
                zscore_flag = bool(abs(z) > self.zscore_threshold)

                if not (iqr_flag or zscore_flag):
                    continue

                dev_pct = ((val - median) / abs(median) * 100) if median != 0 else np.nan
                severity = self._severity(val, lower, upper, iqr, z)
                direction = self._direction(ratio, val, median)
                is_positive = self._is_positive_outlier(ratio, direction)

                records.append({
                    "ticker": ticker,
                    "ratio": ratio,
                    "ratio_label": RATIO_LABELS.get(ratio, ratio),
                    "value": round(val, 4),
                    "sector_median": round(median, 4),
                    "sector_mean": round(mean, 4),
                    "q1": round(q1, 4),
                    "q3": round(q3, 4),
                    "lower_bound": round(lower, 4),
                    "upper_bound": round(upper, 4),
                    "zscore": round(z, 3),
                    "iqr_flag": iqr_flag,
                    "zscore_flag": zscore_flag,
                    "deviation_pct": round(dev_pct, 2) if not pd.isna(dev_pct) else np.nan,
                    "severity_score": round(severity, 2),
                    "direction": direction,
                    "is_positive_outlier": is_positive,
                    "label": "Positive" if is_positive else "Negative",
                })

        if not records:
            return pd.DataFrame()

        result = pd.DataFrame(records)
        result = result.sort_values("severity_score", ascending=False).reset_index(drop=True)
        return result

    def detect_multivariate(self, ratio_matrix: pd.DataFrame, contamination: float = 0.1) -> pd.Series:
        """
        Isolation Forest multivariate anomaly detection.

        Returns
        -------
        Series  ticker → anomaly_score  (higher = more anomalous)
        """
        ratio_cols = [
            c for c in ratio_matrix.columns
            if c not in {"total_revenue", "net_income", "ebitda",
                         "operating_cashflow", "free_cashflow",
                         "total_debt", "total_equity", "total_assets",
                         "market_cap", "eps"}
        ]
        sub = ratio_matrix[ratio_cols].copy()
        sub = sub.replace([np.inf, -np.inf], np.nan)

        # Fill missing with column median
        for col in sub.columns:
            sub[col] = sub[col].fillna(sub[col].median())

        if sub.shape[0] < 4:
            # Robust standardized distance-based fallback for small sample sizes
            medians = sub.median()
            mads = (sub - medians).abs().median()
            
            # Replace zero MADs with standard deviations, or 1.0 if std is also 0
            for col in mads.index:
                if mads[col] == 0:
                    std = sub[col].std()
                    mads[col] = std if (pd.notna(std) and std > 0) else 1.0
            
            # Standardize deviations from median (robust Manhattan distance proxy)
            standardized_diff = (sub - medians).abs() / mads
            dist = standardized_diff.sum(axis=1)
            
            # Scale distance to standard anomaly range [0.15, 0.85] for visual gauge consistency
            if dist.max() > dist.min():
                raw_scores = 0.15 + 0.70 * (dist - dist.min()) / (dist.max() - dist.min())
            else:
                raw_scores = pd.Series(0.42, index=sub.index)
            return pd.Series(raw_scores, index=sub.index, name="anomaly_score")

        scaler = RobustScaler()
        X = scaler.fit_transform(sub)

        iso = IsolationForest(contamination=contamination, random_state=42)
        scores = iso.fit_predict(X)          # -1 = anomaly, 1 = normal
        raw_scores = -iso.score_samples(X)   # higher = more anomalous

        return pd.Series(raw_scores, index=sub.index, name="anomaly_score")

    def build_peer_matrix(self, ratio_matrix: pd.DataFrame) -> pd.DataFrame:
        """
        Return ratio_matrix transposed and formatted for display:
        rows = ratios, columns = tickers.
        """
        display_cols = [c for c in ratio_matrix.columns if c in RATIO_LABELS]
        sub = ratio_matrix[display_cols].T
        sub.index = [RATIO_LABELS.get(r, r) for r in sub.index]
        return sub.round(3)

    def percentile_ranks(self, ratio_matrix: pd.DataFrame) -> pd.DataFrame:
        """
        Compute percentile rank (0–100) for every ticker × ratio cell.
        """
        return ratio_matrix.rank(pct=True).mul(100).round(1)

    def profile_archetypes(
        self,
        peer_matrix: pd.DataFrame,
        client_ratios: Dict[str, float],
        client_name: str
    ) -> Tuple[str, str]:
        """
        Dynamically clusters sector peers and groups the client into one of three corporate archetypes:
        - Elite Market Leader
        - Balanced Sector Participant
        - Debt-Strained Underperformer
        - Debt-Leveraged Asset Packer
        - Asset-Heavy Profit Leader
        - High-Volume Bootstrapper
        """
        import numpy as np
        import pandas as pd
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import RobustScaler

        # 1. Define clustering features
        core_features = ["operating_margin", "debt_to_equity", "asset_turnover"]
        
        # Verify columns exist
        available_features = [f for f in core_features if f in peer_matrix.columns]
        if len(available_features) < 2:
            # Fallback to whatever numeric ratios are available
            available_features = [c for c in peer_matrix.columns if c in RATIO_LABELS][:5]
            
        if len(available_features) < 2 or len(peer_matrix) < 4:
            return "Balanced Sector Participant", "Mixed operational footprint with standard leverage and performance profiles matching sector averages."

        # 2. Extract and align peer and client data
        peer_sub = peer_matrix[available_features].copy()
        peer_sub = peer_sub.replace([np.inf, -np.inf], np.nan)
        for col in peer_sub.columns:
            peer_sub[col] = peer_sub[col].fillna(peer_sub[col].median())
            
        # Add client row
        client_row = {}
        for col in available_features:
            client_row[col] = client_ratios.get(col, peer_sub[col].median())
        client_df = pd.DataFrame([client_row], index=[client_name])
        
        full_df = pd.concat([peer_sub, client_df])
        full_df = full_df.replace([np.inf, -np.inf], np.nan).fillna(0.0)

        # 3. Scale and Cluster
        scaler = RobustScaler()
        X = scaler.fit_transform(full_df)
        
        # Fit KMeans with K=3 clusters
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        
        # Identify the client's cluster label
        client_idx = len(full_df) - 1
        client_cluster = labels[client_idx]
        
        # 4. Analyze Centroids to Map Labels
        centroids = kmeans.cluster_centers_
        
        # Map centroids back to original scale to inspect features
        centroids_orig = scaler.inverse_transform(centroids)
        centroid_df = pd.DataFrame(centroids_orig, columns=available_features)
        
        # Get overall medians for baseline comparison
        overall_medians = peer_sub.median()
        
        # Determine archetype mappings for each of the 3 clusters
        archetypes = {}
        for cluster_id in range(3):
            row = centroid_df.iloc[cluster_id]
            
            # Profitable?
            profit = 0  # 1 = high, -1 = low, 0 = neutral
            if "operating_margin" in row:
                m_val = row["operating_margin"]
                m_med = overall_medians.get("operating_margin", 0.0)
                if m_val > m_med * 1.15:
                    profit = 1
                elif m_val < m_med * 0.85:
                    profit = -1
                    
            # Highly leveraged?
            leverage = 0  # 1 = high, -1 = low, 0 = neutral
            if "debt_to_equity" in row:
                d_val = row["debt_to_equity"]
                d_med = overall_medians.get("debt_to_equity", 0.0)
                if d_val > d_med * 1.2:
                    leverage = 1
                elif d_val < d_med * 0.8:
                    leverage = -1
                    
            # Efficient asset turns?
            efficiency = 0  # 1 = high, -1 = low, 0 = neutral
            if "asset_turnover" in row:
                a_val = row["asset_turnover"]
                a_med = overall_medians.get("asset_turnover", 0.0)
                if a_val > a_med * 1.15:
                    efficiency = 1
                elif a_val < a_med * 0.85:
                    efficiency = -1
            
            # Map combinations to archetypes
            if profit == 1 and leverage == -1:
                archetypes[cluster_id] = (
                    "Elite Market Leader",
                    "Characterized by high profitability margins, lean capital structures with minimal debt, and strong asset returns."
                )
            elif profit == -1 and leverage == 1:
                archetypes[cluster_id] = (
                    "Debt-Strained Underperformer",
                    "Demonstrates high financial leverage accompanied by operating margins well below sector medians, indicating potential liquidity or debt service strain."
                )
            elif profit == 1 and leverage == 1:
                archetypes[cluster_id] = (
                    "Leveraged Capital Expansionist",
                    "Aggressive capital structures utilizing high debt leverage to fund high-margin, asset-intensive expansion operations."
                )
            elif profit == -1 and efficiency == 1:
                archetypes[cluster_id] = (
                    "High-Volume Bootstrapper",
                    "Operates with slim operating margins offset by highly efficient asset turnover, indicating a rapid sales volume model with low pricing power."
                )
            elif profit == 1 and efficiency == -1:
                archetypes[cluster_id] = (
                    "Asset-Heavy Profit Leader",
                    "High profitability margins matched with slower asset turnover speeds, indicating premium pricing power offset by capital-intensive fixed asset models."
                )
            elif leverage == 1 and efficiency == 1:
                archetypes[cluster_id] = (
                    "Debt-Leveraged Asset Packer",
                    "Highly leveraged funding structures coupled with high asset turnover, representing a high-velocity borrowing model to maximize operational velocity."
                )
            else:
                archetypes[cluster_id] = (
                    "Balanced Sector Participant",
                    "Average operational performance, maintaining stable margin limits, standard efficiency turnover, and moderate debt leverage matching sector baselines."
                )
        
        # Return client's cluster archetype
        return archetypes.get(client_cluster, (
            "Balanced Sector Participant",
            "Average operational performance, maintaining stable margin limits, standard efficiency turnover, and moderate debt leverage matching sector baselines."
        ))

    # ── Private helpers ───────────────────────────────────────────────────────

    def _severity(
        self,
        val: float,
        lower: float,
        upper: float,
        iqr: float,
        z: float,
    ) -> float:
        """
        Composite severity score.
        - IQR-based: how many IQR-widths outside the fence?
        - Z-score contribution
        """
        iqr_score = 0.0
        if iqr > 0:
            if val < lower:
                iqr_score = (lower - val) / iqr
            elif val > upper:
                iqr_score = (val - upper) / iqr

        z_score = max(0, abs(z) - self.zscore_threshold)
        return round(0.6 * iqr_score + 0.4 * z_score, 3)

    @staticmethod
    def _direction(ratio: str, val: float, median: float) -> str:
        return "above_median" if val > median else "below_median"

    @staticmethod
    def _is_positive_outlier(ratio: str, direction: str) -> bool:
        if ratio in HIGH_IS_BAD:
            return direction == "below_median"
        if ratio in LOW_IS_BAD:
            return direction == "above_median"
        # Default: above median = positive
        return direction == "above_median"