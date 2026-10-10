import pytest
import pandas as pd
import numpy as np

from modules.ratio_engine import RatioEngine, PERCENTAGE_METRICS
from modules.benchmark_core import score_pillars, rank_and_categorize, PILLARS, PILLAR_WEIGHTS

def test_compute_changes_percentage_metrics_use_diff():
    """Finding F4: Percentage metrics (margins, returns) must use percentage points difference (.diff), not .pct_change."""
    engine = RatioEngine()
    
    # Quarterly time series for a turnaround company
    # Q1: -2.0% net margin, Q2: +3.0% net margin
    # If pct_change was used: (3 - (-2)) / (-2) * 100 = -250% (misleading negative growth)
    # With .diff(): 3.0 - (-2.0) = +5.0 percentage points
    history = pd.DataFrame({
        "net_margin": [-2.0, 3.0, 4.5, 6.0, 8.0],
        "gross_margin": [20.0, 22.0, 25.0, 24.0, 26.0],
        "roe": [-5.0, 2.0, 5.0, 8.0, 10.0],
        "dividend_yield": [0.0, 1.5, 1.8, 2.0, 2.2],
    }, index=["2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31", "2026-03-31"])
    
    changes = engine.compute_changes(history)
    
    assert "net_margin_qoq" in changes.columns
    assert "net_margin_yoy" in changes.columns
    
    # QoQ for Q2: +5.0 percentage points
    assert changes.loc["2025-06-30", "net_margin_qoq"] == pytest.approx(5.0, 0.01)
    # YoY for Q5 (index 4 vs index 0): 8.0 - (-2.0) = +10.0 percentage points
    assert changes.loc["2026-03-31", "net_margin_yoy"] == pytest.approx(10.0, 0.01)
    
    # Gross margin QoQ for Q2: 22 - 20 = +2.0 percentage points
    assert changes.loc["2025-06-30", "gross_margin_qoq"] == pytest.approx(2.0, 0.01)


def test_compute_changes_multiples_safe_pct_change():
    """Finding F4: Multiples use percentage change, but sign flips / negative base values return NaN."""
    engine = RatioEngine()
    
    history = pd.DataFrame({
        "pe_ratio": [10.0, 12.0, -5.0, 15.0, 20.0],
        "current_ratio": [1.5, 1.8, 1.6, 2.0, 2.2],
    }, index=["2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31", "2026-03-31"])
    
    changes = engine.compute_changes(history)
    
    # Q2 PE ratio: (12 - 10) / 10 * 100 = +20%
    assert changes.loc["2025-06-30", "pe_ratio_qoq"] == pytest.approx(20.0, 0.01)
    
    # Q4 PE ratio: previous base in Q3 was -5.0. Growth rate over negative base is NaN
    assert pd.isna(changes.loc["2025-12-31", "pe_ratio_qoq"])
    
    # Q5 PE ratio: previous base in Q4 was 15.0. (20 - 15) / 15 * 100 = +33.33%
    assert changes.loc["2026-03-31", "pe_ratio_qoq"] == pytest.approx(33.333, 0.01)


def test_compute_all_tracks_failed_tickers():
    """Finding F9: Ensure compute_all records failed/skipped tickers in df.attrs."""
    engine = RatioEngine()
    
    parsed = {
        "VALID_CO": {
            "income": pd.DataFrame({"Total Revenue": [1000.0], "Operating Income": [200.0]}),
            "balance": pd.DataFrame({"Total Assets": [2000.0], "Total Liabilities Net Minority Interest": [800.0]}),
            "cashflow": pd.DataFrame({"Operating Cash Flow": [180.0]}),
        },
        "EMPTY_CO": {},  # Missing statements
    }
    
    # Request 3 tickers, 1 valid, 1 with empty statements, 1 completely missing from fetch
    requested = ["VALID_CO", "EMPTY_CO", "NETWORK_FAILED_CO"]
    
    df = engine.compute_all(parsed, requested_tickers=requested)
    
    assert "VALID_CO" in df.index
    assert "EMPTY_CO" not in df.index
    assert "NETWORK_FAILED_CO" not in df.index
    
    assert "failed_tickers" in df.attrs
    assert "requested_tickers" in df.attrs
    assert set(df.attrs["failed_tickers"]) == {"EMPTY_CO", "NETWORK_FAILED_CO"}
    assert df.attrs["requested_tickers"] == requested


def test_shared_scoring_pure_functions():
    """Finding F7: Test score_pillars and rank_and_categorize pure functions."""
    scorecard = pd.DataFrame([
        {"ticker": "CO_A", "ratio": "gross_margin", "percentile_rank": 80.0},
        {"ticker": "CO_A", "ratio": "operating_margin", "percentile_rank": 70.0},
        {"ticker": "CO_B", "ratio": "gross_margin", "percentile_rank": 40.0},
        {"ticker": "CO_B", "ratio": "operating_margin", "percentile_rank": 50.0},
    ])
    
    custom_pillars = {
        "Profitability": [("gross_margin", 0.5, True), ("operating_margin", 0.5, True)]
    }
    
    pillars_df = score_pillars(scorecard, pillars=custom_pillars)
    assert not pillars_df.empty
    assert "profitability_score" in pillars_df.columns
    assert pillars_df.loc["CO_A", "profitability_score"] == pytest.approx(75.0, 0.1)
    assert pillars_df.loc["CO_B", "profitability_score"] == pytest.approx(45.0, 0.1)
    
    ranked = rank_and_categorize(pillars_df, pillar_weights={"Profitability": 1.0})
    assert "composite_score" in ranked.columns
    assert "risk_category" in ranked.columns
    assert ranked.loc[ranked["ticker"] == "CO_A", "composite_score"].iloc[0] == pytest.approx(75.0, 0.1)
