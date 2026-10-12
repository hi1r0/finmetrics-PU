import pytest
from streamlit.testing.v1 import AppTest
from modules.benchmark_store import BenchmarkStore
from modules.benchmark_core import BenchmarkCore
from modules.outlier_engine import OutlierEngine
import pandas as pd

def test_app_initial_render():
    """Verify app.py loads cleanly with zero exceptions on cold start."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert len(at.exception) == 0, f"Exceptions on cold start: {[e.value for e in at.exception]}"
    assert at.session_state["benchmark_result"] is None


def test_app_load_stored_benchmark():
    """Verify loading a pre-calculated benchmark from BenchmarkStore via UI button."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    
    load_btns = [b for b in at.button if b.label == "Load Benchmark"]
    if not load_btns:
        pytest.skip("No pre-stored benchmarks available on disk.")
        
    load_btns[0].click()
    at.run()
    
    assert len(at.exception) == 0, f"Exceptions after loading benchmark: {[e.value for e in at.exception]}"
    res = at.session_state["benchmark_result"]
    assert res is not None
    assert not res.ratio_scorecard_df.empty
    assert not res.peer_stats_df.empty
    assert not res.pillar_summary_df.empty


def test_app_all_tabs_with_populated_result():
    """Verify all 6 tabs render without exceptions when benchmark_result is in session_state."""
    store = BenchmarkStore()
    available = store.list_available()
    if not available:
        pytest.skip("No pre-stored benchmarks available on disk.")
        
    p_df, c_mat, meta = store.load(available[0])
    oe = OutlierEngine()
    out_df = oe.detect(c_mat)
    bc = BenchmarkCore()
    res = bc.run(c_mat, out_df)
    
    at = AppTest.from_file("app.py", default_timeout=30)
    at.session_state["benchmark_result"] = res
    at.session_state["selected_sector"] = available[0]
    at.session_state["tickers_used"] = list(c_mat.index)
    at.session_state["requested_tickers"] = list(c_mat.index)
    at.session_state["failed_tickers"] = []
    at.session_state["outlier_df"] = out_df
    
    at.run()
    assert len(at.exception) == 0, f"Exceptions with populated benchmark: {[e.value for e in at.exception]}"
