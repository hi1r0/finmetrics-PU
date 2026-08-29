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

def test_client_comparator_evaluation(tmp_path):
    """Test ClientComparator correctly compares client against benchmark store."""
    from modules.benchmark_store import BenchmarkStore
    from modules.client_comparator import ClientComparator
    
    store = BenchmarkStore(benchmarks_dir=tmp_path)
    
    data = {
        "debt_to_equity": [0.5, 0.6, 0.7, 0.8, 0.9],
        "gross_margin": [40.0, 42.0, 39.0, 41.0, 40.5],
        "net_margin": [12.0, 13.0, 11.5, 12.5, 12.0],
        "roe": [15.0, 16.0, 14.5, 15.5, 15.0],
        "roa": [8.0, 8.5, 7.8, 8.2, 8.0],
    }
    index = ["CO_A", "CO_B", "CO_C", "CO_D", "CO_E"]
    ratio_df = pd.DataFrame(data, index=index)
    
    core = BenchmarkCore()
    result = core.run(ratio_df, pd.DataFrame())
    store.save("TestSector", result.peer_stats_df, result.clean_matrix)
    
    comparator = ClientComparator(store=store)
    client_ratios = {
        "debt_to_equity": 0.6,
        "gross_margin": 45.0,
        "net_margin": 14.0,
        "roe": 18.0,
        "roa": 9.0,
    }
    client_res = comparator.compare_client(client_ratios, sector="TestSector", client_name="MyClient")
    
    assert not client_res.ratio_scorecard_df.empty
    assert (client_res.pillar_summary_df["ticker"] == "MyClient").any()
    assert client_res.pillar_summary_df.iloc[0]["composite_score"] > 50.0

