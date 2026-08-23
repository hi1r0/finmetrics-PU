import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from modules.benchmark_store import BenchmarkStore
from modules.benchmark_classifier import BenchmarkClassifier
from modules.benchmark_core import BenchmarkCoreResult, PILLARS, PILLAR_WEIGHTS, RISK_CATEGORIES

logger = logging.getLogger(__name__)

class ClientComparator:
    """
    Compares a single client's financials against a frozen peer benchmark.
    """
    
    def __init__(self, store: BenchmarkStore):
        self.store = store
        self.classifier = BenchmarkClassifier()

    def _normalize_ratio_name(self, name: str) -> str:
        s = str(name).strip().lower()
        for suffix in [" (%)", " (%)", " (x)", " (x)", " (multi)", " (sales)", " (days)", "%", " x"]:
            s = s.replace(suffix.lower(), "")
        s = s.strip()
        s = s.replace(" ", "_").replace("-", "_").replace("/", "_")
        s = s.strip("_")
        
        synonyms = {
            "company_name": "ticker",
            "company": "ticker",
            "name": "ticker",
            "ticker": "ticker",
            
            "gross_margin": "gross_margin",
            "gross_profit_margin": "gross_margin",
            "gpm": "gross_margin",
            
            "operating_margin": "operating_margin",
            "operating_profit_margin": "operating_margin",
            "opm": "operating_margin",
            "ebit_margin": "operating_margin",
            
            "net_margin": "net_margin",
            "net_profit_margin": "net_margin",
            "npm": "net_margin",
            
            "roe": "roe",
            "return_on_equity": "roe",
            
            "roa": "roa",
            "return_on_assets": "roa",
            
            "roce": "roce",
            "return_on_capital_employed": "roce",
            
            "current_ratio": "current_ratio",
            "cr": "current_ratio",
            
            "quick_ratio": "quick_ratio",
            "qr": "quick_ratio",
            "acid_test": "quick_ratio",
            
            "cash_ratio": "cash_ratio",
            
            "debt_to_equity": "debt_to_equity",
            "debt_equity": "debt_to_equity",
            "d_e": "debt_to_equity",
            
            "debt_ratio": "debt_ratio",
            "debt_assets": "debt_ratio",
            "d_a": "debt_ratio",
            
            "interest_coverage": "interest_coverage",
            "interest_coverage_ratio": "interest_coverage",
            "icr": "interest_coverage",
            "times_interest_earned": "interest_coverage",
            
            "asset_turnover": "asset_turnover",
            "assets_turnover": "asset_turnover",
            "ato": "asset_turnover",
            
            "inventory_turnover": "inventory_turnover",
            "inventory_turnover_ratio": "inventory_turnover",
            "itr": "inventory_turnover",
            
            "receivables_turnover": "receivables_turnover",
            "receivables_turnover_ratio": "receivables_turnover",
            "rtr": "receivables_turnover",
            
            "revenue_growth": "revenue_growth",
            "sales_growth": "revenue_growth",
            
            "net_income_growth": "net_income_growth",
            "profit_growth": "net_income_growth",
            
            "ocf_growth": "ocf_growth",
            "operating_cash_flow_growth": "ocf_growth",
            
            "total_revenue": "total_revenue",
            "revenue": "total_revenue",
            "sales": "total_revenue",
            "ebitda": "ebitda",
            "ebitda_margin": "ebitda",
            "net_income": "net_income",
            "operating_cashflow": "operating_cashflow",
            "free_cashflow": "free_cashflow",
            "total_debt": "total_debt",
            "debt": "total_debt",
            "total_equity": "total_equity",
            "equity": "total_equity",
            "total_assets": "total_assets",
            "assets": "total_assets",
        }
        return synonyms.get(s, s)

    def compare_client(
        self,
        client_ratios: Dict[str, float],
        sector: str,
        client_name: str = "Client",
    ) -> BenchmarkCoreResult:
        logger.info(f"Comparing client '{client_name}' against sector '{sector}'")
        
        peer_stats_df, clean_matrix, _ = self.store.load(sector) or (None, None, None)
        if peer_stats_df is None or clean_matrix is None:
            raise ValueError(f"No benchmark found for sector '{sector}'. Please build the benchmark first.")
            
        # Normalize incoming client ratio keys
        normalized_ratios = {}
        for k, v in client_ratios.items():
            norm_k = self._normalize_ratio_name(k)
            if isinstance(v, str):
                try:
                    v = float(v.replace(",", "").replace("%", "").replace("$", "").strip())
                except ValueError:
                    pass
            normalized_ratios[norm_k] = v
            
        if "ticker" in normalized_ratios:
            possible_name = str(normalized_ratios.pop("ticker")).strip()
            if possible_name and possible_name.lower() != "nan":
                client_name = possible_name
                
        client_ratios = normalized_ratios
            
        client_df = pd.DataFrame([client_ratios], index=[client_name])
        client_df.index.name = "ticker"
        
        results = []
        for ratio in client_df.columns:
            if ratio not in peer_stats_df.index:
                continue
            raw_val = client_df.at[client_name, ratio]
            peer_row = peer_stats_df.loc[ratio]
            peer_vals = clean_matrix[ratio].dropna() if ratio in clean_matrix.columns else None
            
            res = self.classifier.classify_ratio(ratio, raw_val, peer_row, peer_vals)
            res["ticker"] = client_name
            res["is_outlier_excluded"] = False
            results.append(res)
            
        scorecard = pd.DataFrame(results)
        
        ratio_to_pillar = {}
        for pillar, metrics in PILLARS.items():
            for ratio, _, _ in metrics:
                ratio_to_pillar[ratio] = pillar
                
        scorecard["pillar"] = scorecard["ratio"].map(lambda r: ratio_to_pillar.get(r, "Other"))
        
        pct_df = scorecard.pivot(index="ticker", columns="ratio", values="percentile_rank")
        pillar_summary = pd.DataFrame(index=pct_df.index)
        
        for pillar, metrics in PILLARS.items():
            col_name = f"{pillar.lower()}_score"
            available = [(col, w) for col, w, _ in metrics if col in pct_df.columns]
            if not available:
                pillar_summary[col_name] = 50.0
                continue
                
            weighted_sum = pd.Series(0.0, index=pct_df.index)
            total_weight = pd.Series(0.0, index=pct_df.index)
            
            for col, weight in available:
                vals = pct_df[col]
                mask = vals.notna()
                weighted_sum += vals.fillna(0) * weight * mask.astype(float)
                total_weight += mask.astype(float) * weight
                
            pillar_summary[col_name] = (weighted_sum / total_weight.replace(0, np.nan)).fillna(50.0).round(2)
            
        composite = pd.Series(0.0, index=pillar_summary.index)
        total_weight_comp = 0.0
        
        for pillar, weight in PILLAR_WEIGHTS.items():
            col_name = f"{pillar.lower()}_score"
            if col_name in pillar_summary.columns:
                composite += pillar_summary[col_name] * weight
                total_weight_comp += weight
                
        if total_weight_comp > 0:
            composite = composite / total_weight_comp
            
        pillar_summary["composite_score"] = composite.round(2)
        
        def get_risk(score):
            for threshold, label in RISK_CATEGORIES:
                if score >= threshold:
                    return label
            return "Distressed"
            
        pillar_summary["risk_category"] = pillar_summary["composite_score"].apply(get_risk)
        pillar_summary = pillar_summary.reset_index()
        
        return BenchmarkCoreResult(
            peer_stats_df=peer_stats_df,
            ratio_scorecard_df=scorecard,
            pillar_summary_df=pillar_summary,
            outlier_df=pd.DataFrame(), 
            clean_matrix=client_df,
        )
