import pytest
import pandas as pd
from pathlib import Path

from modules.report_generator import ReportGenerator
from modules.benchmark_core import BenchmarkCore

def test_report_generator_explain_all():
    """Verify statistical explanation generation for scorecard rows."""
    scorecard_df = pd.DataFrame([
        {
            "ticker": "RELIANCE",
            "ratio": "operating_margin",
            "raw_value": 18.5,
            "peer_median": 15.0,
            "position_label": "Above Benchmark",
        },
        {
            "ticker": "RELIANCE",
            "ratio": "debt_to_equity",
            "raw_value": 1.2,
            "peer_median": 0.8,
            "position_label": "Below Benchmark",
        },
        {
            "ticker": "TCS",
            "ratio": "gross_margin",
            "raw_value": 45.0,
            "peer_median": 45.0,
            "position_label": "At Benchmark",
        }
    ])
    
    gen = ReportGenerator()
    exp_df = gen.explain_all(scorecard_df)
    
    assert not exp_df.empty
    assert len(exp_df) == 3
    assert set(exp_df.columns) == {"ticker", "ratio", "explanation", "category", "source"}
    
    opp_row = exp_df[exp_df["ratio"] == "operating_margin"].iloc[0]
    assert opp_row["category"] == "Opportunity"
    assert "[OPPORTUNITY]" in opp_row["explanation"]
    
    risk_row = exp_df[exp_df["ratio"] == "debt_to_equity"].iloc[0]
    assert risk_row["category"] == "Risk"
    assert "[RISK]" in risk_row["explanation"]


def test_report_generator_export_excel(tmp_path, monkeypatch):
    """Verify Excel report generation creates a valid workbook with required sheets."""
    import modules.report_generator as rg
    monkeypatch.setattr(rg, "OUTPUTS_REPORTS", tmp_path)
    
    data = {
        "debt_to_equity": [0.5, 0.6, 0.7, 0.8, 0.9],
        "gross_margin": [40.0, 42.0, 39.0, 41.0, 40.5],
    }
    index = ["CO_A", "CO_B", "CO_C", "CO_D", "CO_E"]
    ratio_df = pd.DataFrame(data, index=index)
    
    core = BenchmarkCore()
    result = core.run(ratio_df, pd.DataFrame())
    
    gen = ReportGenerator()
    exp_df = gen.explain_all(result.ratio_scorecard_df)
    
    excel_path = gen.export_excel(
        ratio_scorecard_df=result.ratio_scorecard_df,
        peer_stats_df=result.peer_stats_df,
        outlier_df=result.outlier_df if result.outlier_df is not None else pd.DataFrame(),
        pillar_summary_df=result.pillar_summary_df,
        explanation_df=exp_df,
        sector="Energy",
    )
    
    assert excel_path.exists()
    assert excel_path.suffix == ".xlsx"
    
    # Read sheets back
    excel_file = pd.ExcelFile(excel_path)
    sheet_names = excel_file.sheet_names
    assert "Ratio Scorecard" in sheet_names
    assert "Peer Benchmark" in sheet_names
    assert "Composite Scores" in sheet_names
    assert "Business Report" in sheet_names
    assert "Summary" in sheet_names
