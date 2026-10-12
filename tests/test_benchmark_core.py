import pytest
import pandas as pd
import numpy as np

from modules.benchmark_core import BenchmarkCore
from modules.outlier_engine import OutlierEngine

def test_outlier_value_survives_in_own_scorecard():
    """Finding F1: Outlier value must not be replaced with NaN in the company's own scorecard."""
    # Synthetic dataset with 5 peers + 1 outlier
    data = {
        "debt_to_equity": [0.5, 0.6, 0.7, 0.8, 0.9, 50.0],
        "current_ratio": [1.5, 1.6, 1.4, 1.55, 1.45, 1.5],
        "gross_margin": [40.0, 42.0, 39.0, 41.0, 40.5, 40.0],
        "operating_margin": [20.0, 21.0, 19.5, 20.5, 20.0, 20.0],
        "net_margin": [12.0, 13.0, 11.5, 12.5, 12.0, 12.0],
        "roe": [15.0, 16.0, 14.5, 15.5, 15.0, 15.0],
        "roa": [8.0, 8.5, 7.8, 8.2, 8.0, 8.0],
    }
    index = ["CO_A", "CO_B", "CO_C", "CO_D", "CO_E", "OUTLIER_CO"]
    ratio_df = pd.DataFrame(data, index=index)
    
    outlier_engine = OutlierEngine(zscore_threshold=2.5, iqr_multiplier=1.5, min_peers=3)
    outlier_df = outlier_engine.detect(ratio_df)
    
    core = BenchmarkCore()
    result = core.run(ratio_df, outlier_df)
    
    scorecard = result.ratio_scorecard_df
    assert not scorecard.empty
    
    # Check OUTLIER_CO's debt_to_equity row in scorecard
    outlier_row = scorecard[(scorecard["ticker"] == "OUTLIER_CO") & (scorecard["ratio"] == "debt_to_equity")]
    assert len(outlier_row) == 1
    
    # 1. Raw value MUST NOT be NaN or No Data
    raw_val = outlier_row.iloc[0]["raw_value"]
    assert not pd.isna(raw_val), "Outlier's own raw_value was incorrectly masked to NaN"
    assert raw_val == 50.0
    assert outlier_row.iloc[0]["health_label"] != "No Data"
    assert bool(outlier_row.iloc[0]["is_outlier_excluded"]) is True
    
    # 2. Peer median for debt_to_equity MUST be computed excluding 50.0
    peer_stats = result.peer_stats_df
    de_median = peer_stats.loc["debt_to_equity", "median"]
    # Median of [0.5, 0.6, 0.7, 0.8, 0.9] is 0.7
    assert de_median == pytest.approx(0.7, 0.01)

def test_benchmark_core_pipeline_full():
    """Verify complete Phase 1 benchmark pipeline execution across peers."""
    data = {
        "debt_to_equity": [0.5, 0.6, 0.7, 0.8, 0.9],
        "current_ratio": [1.5, 1.6, 1.4, 1.55, 1.45],
        "gross_margin": [40.0, 42.0, 39.0, 41.0, 40.5],
        "operating_margin": [20.0, 21.0, 19.5, 20.5, 20.0],
        "net_margin": [12.0, 13.0, 11.5, 12.5, 12.0],
        "roe": [15.0, 16.0, 14.5, 15.5, 15.0],
        "roa": [8.0, 8.5, 7.8, 8.2, 8.0],
    }
    index = ["CO_A", "CO_B", "CO_C", "CO_D", "CO_E"]
    ratio_df = pd.DataFrame(data, index=index)
    
    core = BenchmarkCore()
    result = core.run(ratio_df, pd.DataFrame())
    
    # 1. Peer stats must contain summary stats for all computed ratios
    peer_stats = result.peer_stats_df
    assert not peer_stats.empty
    assert "gross_margin" in peer_stats.index
    assert peer_stats.loc["gross_margin", "median"] == pytest.approx(40.5, 0.01)
    
    # 2. Scorecard must include each company x ratio row
    scorecard = result.ratio_scorecard_df
    assert len(scorecard) == len(index) * len(data)
    assert set(scorecard["ticker"]) == set(index)
    assert "percentile_rank" in scorecard.columns
    assert "position_label" in scorecard.columns
    
    # 3. Pillar summary must have ranking and composite score for all peers
    summary = result.pillar_summary_df
    assert len(summary) == len(index)
    assert "composite_score" in summary.columns
    assert "sector_rank" in summary.columns
    assert "risk_category" in summary.columns
    assert summary["sector_rank"].min() == 1
    assert summary["sector_rank"].max() == len(index)


def test_benchmark_store_persistence(tmp_path):
    """Verify BenchmarkStore can save and reload sector peer statistics and clean matrices."""
    from modules.benchmark_store import BenchmarkStore
    
    store = BenchmarkStore(benchmarks_dir=tmp_path)
    data = {
        "gross_margin": [40.0, 42.0, 39.0],
        "net_margin": [12.0, 13.0, 11.5],
    }
    index = ["PEER_1", "PEER_2", "PEER_3"]
    ratio_df = pd.DataFrame(data, index=index)
    
    core = BenchmarkCore()
    result = core.run(ratio_df, pd.DataFrame())
    
    store.save("Banking", result.peer_stats_df, result.clean_matrix)
    assert "Banking" in store.list_available()
    
    loaded = store.load("Banking")
    assert loaded is not None
    loaded_stats, loaded_matrix, loaded_meta = loaded
    assert loaded_stats.loc["gross_margin", "median"] == pytest.approx(40.0, 0.01)
    assert len(loaded_matrix) == 3
    assert loaded_meta["sector"] == "Banking"


