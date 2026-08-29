import pytest
import pandas as pd
import numpy as np
import tempfile
from pathlib import Path

from modules.tally_bridge import TallyBridge

def test_tally_bridge_ratio_computation():
    """Finding F2: Test TallyBridge computes ratios and separates interest/tax when present."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        ledger_file = tmp_path / "LedgerMaster.csv"
        jv_file = tmp_path / "JV.csv"
        
        # Create minimal Ledger Master
        ledger_df = pd.DataFrame([
            {"NAME": "Sales Account", "PRIMARYGROUP": "Sales Accounts"},
            {"NAME": "Purchase Material", "PRIMARYGROUP": "Purchase Accounts"},
            {"NAME": "Rent Expense", "PRIMARYGROUP": "Indirect Expenses"},
            {"NAME": "Bank Interest Paid", "PRIMARYGROUP": "Interest on Loans"},
            {"NAME": "Income Tax Provision", "PRIMARYGROUP": "Duties & Taxes"},
            {"NAME": "HDFC Bank", "PRIMARYGROUP": "Bank Accounts"},
            {"NAME": "Share Capital", "PRIMARYGROUP": "Capital Account"},
            {"NAME": "Term Loan", "PRIMARYGROUP": "Secured Loans"},
            {"NAME": "Office Building", "PRIMARYGROUP": "Fixed Assets"},
        ])
        ledger_df.to_csv(ledger_file, index=False)
        
        # Create minimal JV
        # In TallySync: Credit is positive, Debit is negative (or standard amounts)
        # Let's say: Sales = 1000 (Cr), Purchase = 400 (Dr), Rent = 100 (Dr), Interest = 50 (Dr), Tax = 50 (Dr)
        jv_df = pd.DataFrame([
            {"PARTICULARS": "Sales Account", "DEBIT": 0.0, "CREDIT": 1000.0},
            {"PARTICULARS": "Purchase Material", "DEBIT": -400.0, "CREDIT": 0.0},
            {"PARTICULARS": "Rent Expense", "DEBIT": -100.0, "CREDIT": 0.0},
            {"PARTICULARS": "Bank Interest Paid", "DEBIT": -50.0, "CREDIT": 0.0},
            {"PARTICULARS": "Income Tax Provision", "DEBIT": -50.0, "CREDIT": 0.0},
            {"PARTICULARS": "HDFC Bank", "DEBIT": -200.0, "CREDIT": 0.0},
            {"PARTICULARS": "Share Capital", "DEBIT": 0.0, "CREDIT": 500.0},
            {"PARTICULARS": "Term Loan", "DEBIT": 0.0, "CREDIT": 200.0},
            {"PARTICULARS": "Office Building", "DEBIT": -500.0, "CREDIT": 0.0},
        ])
        jv_df.to_csv(jv_file, index=False)
        
        bridge = TallyBridge(str(jv_file), str(ledger_file))
        ratios = bridge.compute_ratios()
        
        assert "gross_margin" in ratios
        assert "operating_margin" in ratios
        assert "net_margin" in ratios
        
        # Revenue = 1000, COGS = 400 => Gross Profit = 600 => Gross Margin = 60%
        assert ratios["gross_margin"] == pytest.approx(60.0, 0.1)
        # Opex = 100 => EBIT = 500 => Operating Margin = 50%
        assert ratios["operating_margin"] == pytest.approx(50.0, 0.1)
        # Interest = 50, Tax = 50 => Net Income = 400 => Net Margin = 40%
        assert ratios["net_margin"] == pytest.approx(40.0, 0.1)
        assert ratios["ebitda"] == pytest.approx(500.0, 0.1)
