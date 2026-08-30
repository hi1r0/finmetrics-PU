import pytest
import pandas as pd
import numpy as np
import tempfile
from pathlib import Path

from modules.tally_bridge import TallyBridge

def test_tally_bridge_gst_payable_and_proxy_basis():
    """Finding F2 & F8: Test real-world Tally GST Duties & Taxes as a current liability and proxy net income."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        ledger_file = tmp_path / "LedgerMaster.csv"
        jv_file = tmp_path / "JV.csv"
        
        # Real-world Indian Tally Ledger Master with GST Output Tax Payable
        ledger_df = pd.DataFrame([
            {"NAME": "Retail Sales - Counter", "PRIMARYGROUP": "Sales Accounts"},
            {"NAME": "FMCG Goods Purchase", "PRIMARYGROUP": "Purchase Accounts"},
            {"NAME": "Commercial Rent", "PRIMARYGROUP": "Indirect Expenses"},
            {"NAME": "GST Output Tax Payable", "PRIMARYGROUP": "Duties & Taxes"},
            {"NAME": "Sundry Creditors A/c", "PRIMARYGROUP": "Sundry Creditors"},
            {"NAME": "HDFC Bank", "PRIMARYGROUP": "Bank Accounts"},
            {"NAME": "Share Capital", "PRIMARYGROUP": "Capital Account"},
            {"NAME": "Store Fixtures", "PRIMARYGROUP": "Fixed Assets"},
        ])
        ledger_df.to_csv(ledger_file, index=False)
        
        # JV entries with negative debits and positive credits
        jv_df = pd.DataFrame([
            {"PARTICULARS": "Retail Sales - Counter", "DEBIT": 0.0, "CREDIT": 1000.0},
            {"PARTICULARS": "FMCG Goods Purchase", "DEBIT": -400.0, "CREDIT": 0.0},
            {"PARTICULARS": "Commercial Rent", "DEBIT": -100.0, "CREDIT": 0.0},
            {"PARTICULARS": "GST Output Tax Payable", "DEBIT": 0.0, "CREDIT": 50.0},
            {"PARTICULARS": "Sundry Creditors A/c", "DEBIT": 0.0, "CREDIT": 50.0},
            {"PARTICULARS": "HDFC Bank", "DEBIT": -300.0, "CREDIT": 0.0},
            {"PARTICULARS": "Share Capital", "DEBIT": 0.0, "CREDIT": 600.0},
            {"PARTICULARS": "Store Fixtures", "DEBIT": -400.0, "CREDIT": 0.0},
        ])
        jv_df.to_csv(jv_file, index=False)
        
        bridge = TallyBridge(str(jv_file), str(ledger_file))
        ratios = bridge.compute_ratios()
        
        # 1. Gross Profit & EBIT
        assert ratios["gross_margin"] == pytest.approx(60.0, 0.1)
        assert ratios["operating_margin"] == pytest.approx(50.0, 0.1)
        
        # 2. Net Income must NOT be inflated by GST Output Tax Payable
        assert ratios["net_margin"] == pytest.approx(50.0, 0.1)
        assert ratios["net_income_basis"] == "ebit_proxy_partial"
        
        # 3. EBITDA must be NaN (not mislabeled from EBIT), and EBIT explicitly reported
        assert pd.isna(ratios["ebitda"])
        assert ratios["ebit"] == pytest.approx(500.0, 0.1)
        
        # 4. Liquidity: Current Liab = GST Payable (50) + Creditors (50) = 100, Cash = 300 => Current Ratio = 3.0
        assert ratios["current_ratio"] == pytest.approx(3.0, 0.1)
        
        # 5. Vectorized Trial Balance Check
        tb = bridge.compute_trial_balance()
        assert not tb.empty
        gst_row = tb[tb["Ledger Name"] == "GST Output Tax Payable"]
        assert len(gst_row) == 1
        assert gst_row.iloc[0]["Benchmark Category"] == "other_current_liabilities"
        assert gst_row.iloc[0]["Final Credit"] == 50.0


def test_tally_bridge_with_explicit_tax_and_interest():
    """Test TallyBridge computes adjusted net income when explicit tax provision & interest exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        ledger_file = tmp_path / "LedgerMaster.csv"
        jv_file = tmp_path / "JV.csv"
        
        ledger_df = pd.DataFrame([
            {"NAME": "Sales", "PRIMARYGROUP": "Sales Accounts"},
            {"NAME": "COGS", "PRIMARYGROUP": "Purchase Accounts"},
            {"NAME": "Rent", "PRIMARYGROUP": "Indirect Expenses"},
            {"NAME": "Bank Interest", "PRIMARYGROUP": "Interest on Loans"},
            {"NAME": "Income Tax Provision", "PRIMARYGROUP": "Provision for Tax"},
            {"NAME": "Bank", "PRIMARYGROUP": "Bank Accounts"},
            {"NAME": "Capital", "PRIMARYGROUP": "Capital Account"},
        ])
        ledger_df.to_csv(ledger_file, index=False)
        
        jv_df = pd.DataFrame([
            {"PARTICULARS": "Sales", "DEBIT": 0.0, "CREDIT": 1000.0},
            {"PARTICULARS": "COGS", "DEBIT": -400.0, "CREDIT": 0.0},
            {"PARTICULARS": "Rent", "DEBIT": -100.0, "CREDIT": 0.0},
            {"PARTICULARS": "Bank Interest", "DEBIT": -50.0, "CREDIT": 0.0},
            {"PARTICULARS": "Income Tax Provision", "DEBIT": -50.0, "CREDIT": 0.0},
            {"PARTICULARS": "Bank", "DEBIT": -400.0, "CREDIT": 0.0},
            {"PARTICULARS": "Capital", "DEBIT": 0.0, "CREDIT": 800.0},
        ])
        jv_df.to_csv(jv_file, index=False)
        
        bridge = TallyBridge(str(jv_file), str(ledger_file))
        ratios = bridge.compute_ratios()
        
        # Revenue 1000, EBIT 500, Interest 50, Tax 50 => Net Income 400 => Net Margin 40%
        assert ratios["net_margin"] == pytest.approx(40.0, 0.1)
        assert ratios["net_income_basis"] == "tax_and_interest_adjusted"
        assert ratios["interest_coverage"] == pytest.approx(10.0, 0.1)

def test_tally_bridge_bundled_client_data():
    """Test TallyBridge on bundled PRIME RETAIL VENTURES client CSVs."""
    jv_path = Path("client/PRIME RETAIL VENTURES - JV - 2025-26.csv")
    ledger_path = Path("client/PRIME RETAIL VENTURES - Ledger Master - 2025-26.csv")
    if not jv_path.exists() or not ledger_path.exists():
        pytest.skip("Bundled client data not present")
        
    bridge = TallyBridge(str(jv_path), str(ledger_path))
    ratios = bridge.compute_ratios()
    
    assert "gross_margin" in ratios
    assert "operating_margin" in ratios
    assert "net_margin" in ratios
    assert ratios["net_income_basis"] == "ebit_proxy_partial"
    assert pd.isna(ratios["ebitda"])
    assert not pd.isna(ratios["ebit"])
    
    tb = bridge.compute_trial_balance()
    assert not tb.empty
    assert len(tb) >= 25
    assert tb["Final Debit"].sum() == pytest.approx(tb["Final Credit"].sum(), 1.0)
    
    ledger_map = bridge._load_ledger_map()
    assert ledger_map.get("GST Output Tax Payable") == "other_current_liabilities"
    assert ledger_map.get("Retail Sales - Counter") == "revenue"


