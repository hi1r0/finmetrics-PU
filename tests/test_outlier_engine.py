import pytest
import pandas as pd
import numpy as np

from modules.outlier_engine import OutlierEngine

def test_outlier_engine_default_zscore_threshold():
    """Finding F3: Ensure zscore_threshold defaults to 2.5 (literature & blueprint standard)."""
    engine = OutlierEngine()
    assert engine.zscore_threshold == 2.5
    assert engine.iqr_multiplier == 1.5
    assert engine.min_peers == 3

def test_outlier_detection_flags_extreme_value():
    """Verify that an extreme value in a peer distribution is correctly detected."""
    engine = OutlierEngine(zscore_threshold=2.5, iqr_multiplier=1.5, min_peers=3)
    
    # Synthetic ratio matrix: 5 peers with normal D/E (0.5 - 1.0) and 1 extreme outlier (50.0)
    data = {
        "debt_to_equity": [0.5, 0.6, 0.7, 0.8, 0.9, 50.0],
        "current_ratio": [1.5, 1.6, 1.4, 1.55, 1.45, 1.5],
    }
    index = ["TICKER1", "TICKER2", "TICKER3", "TICKER4", "TICKER5", "OUTLIER_CO"]
    ratio_df = pd.DataFrame(data, index=index)
    
    outliers = engine.detect(ratio_df)
    assert not outliers.empty
    
    # OUTLIER_CO debt_to_equity should be flagged
    flagged = outliers[(outliers["ticker"] == "OUTLIER_CO") & (outliers["ratio"] == "debt_to_equity")]
    assert len(flagged) == 1
    assert flagged.iloc[0]["value"] == 50.0
    assert bool(flagged.iloc[0]["iqr_flag"]) or bool(flagged.iloc[0]["zscore_flag"])
