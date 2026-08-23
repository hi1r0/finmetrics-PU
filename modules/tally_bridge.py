"""
tally_bridge.py
===============
Converts raw TallySync CSV exports (Journal + Ledger Master) into a
dictionary of financial ratios that the BenchmarkCore pipeline can consume.

Supports the following ratios (calculable from a single year's JV data):
  Profitability:  gross_margin, operating_margin, net_margin, roa, roe, roce
  Liquidity:      current_ratio, quick_ratio, cash_ratio
  Solvency:       debt_to_equity, debt_ratio, interest_coverage
  Efficiency:     asset_turnover, inventory_turnover, receivables_turnover
  Cash Flow:      operating_cf_ratio, fcf_margin, cash_conversion
"""

import logging
import os
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

from modules.utils import safe_divide

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tally Primary Group → Internal Pillar Mapping
# ---------------------------------------------------------------------------
_GROUP_TO_PILLAR: Dict[str, str] = {
    # Revenue
    "Sales Accounts":       "revenue",
    "Direct Incomes":       "revenue",
    # COGS
    "Purchase Accounts":    "cogs",
    "Direct Expenses":      "cogs",
    # Operating Expenses
    "Indirect Expenses":    "opex",
    # Cash & Bank
    "Bank Accounts":        "cash",
    "Cash-in-Hand":         "cash",
    # Debtors / Receivables
    "Sundry Debtors":       "receivables",
    # Inventory
    "Stock-in-Hand":        "inventory",
    # Other Current Assets
    "Current Assets":       "other_current_assets",
    "Deposits (Asset)":     "other_current_assets",
    "Loans & Advances (Asset)": "other_current_assets",
    "Branch / Divisions":   "other_current_assets",
    "Suspense A/c":         "other_current_assets",
    "Misc. Expenses (ASSET)": "other_current_assets",
    # Fixed / Non-Current Assets
    "Fixed Assets":         "fixed_assets",
    "Investments":          "fixed_assets",
    # Creditors / Payables
    "Sundry Creditors":     "payables",
    # Other Current Liabilities
    "Current Liabilities":  "other_current_liabilities",
    "Duties & Taxes":       "other_current_liabilities",
    "Provisions":           "other_current_liabilities",
    # Debt
    "Secured Loans":        "debt",
    "Unsecured Loans":      "debt",
    "Bank OD A/c":          "debt",
    # Equity
    "Capital Account":      "equity",
    "Reserves & Surplus":   "equity",
}

# Pillars whose balance is calculated as Credit - Debit
_CREDIT_NATURE = {"revenue", "payables", "other_current_liabilities", "debt", "equity"}


class TallyBridge:
    """
    Reads TallySync Journal + Ledger Master CSVs and produces a flat
    dictionary of financial ratios compatible with the benchmarking engine.

    Usage
    -----
    bridge = TallyBridge(jv_path, ledger_path)
    ratios = bridge.compute_ratios()   # -> Dict[str, float]
    """

    def __init__(self, jv_path: str, ledger_path: str, chunk_size: int = 50_000):
        self.jv_path = Path(jv_path)
        self.ledger_path = Path(ledger_path)
        self.chunk_size = chunk_size

        if not self.jv_path.exists():
            raise FileNotFoundError(f"Journal file not found: {self.jv_path}")
        if not self.ledger_path.exists():
            raise FileNotFoundError(f"Ledger Master file not found: {self.ledger_path}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute_ratios(self) -> Dict[str, float]:
        """Main entry point. Returns a dict of ratio_name -> float."""
        logger.info("TallyBridge: Loading ledger master...")
        ledger_map = self._load_ledger_map()

        logger.info("TallyBridge: Aggregating journal entries (file: %.1f MB)...",
                    self.jv_path.stat().st_size / 1e6)
        pillars = self._aggregate_journal(ledger_map)

        logger.info("TallyBridge: Computing ratios from pillars...")
        ratios = self._compute_ratios(pillars)

        logger.info("TallyBridge: Done. %d ratios computed.", len(ratios))
        return ratios

    def compute_trial_balance(self) -> pd.DataFrame:
        """
        Returns a professional Trial Balance DataFrame with all ledgers,
        showing Final Debit and Final Credit columns (absolute values).
        """
        ledger_map = self._load_ledger_map()
        ledger_stats = self._collect_ledger_stats(ledger_map)

        tb = pd.DataFrame.from_dict(ledger_stats, orient="index").reset_index()
        tb.columns = ["Ledger Name", "Raw Debit", "Raw Credit", "Benchmark Category"]
        # Net = Debit + Credit (Debit is negative in TallySync export)
        tb["Net"] = tb["Raw Debit"] + tb["Raw Credit"]
        tb["Final Debit"]  = tb["Net"].apply(lambda x: abs(x) if x < 0 else 0.0)
        tb["Final Credit"] = tb["Net"].apply(lambda x: x if x > 0 else 0.0)
        return tb[["Ledger Name", "Final Debit", "Final Credit", "Benchmark Category"]]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_ledger_map(self) -> Dict[str, str]:
        """Read Ledger Master CSV and build ledger_name -> pillar mapping."""
        try:
            df = pd.read_csv(self.ledger_path, encoding="latin1")
        except UnicodeDecodeError:
            df = pd.read_csv(self.ledger_path, encoding="utf-8")

        mapping: Dict[str, str] = {}
        for _, row in df.iterrows():
            name  = str(row.get("NAME", "")).strip()
            group = str(row.get("PRIMARYGROUP", "")).strip()
            mapping[name] = _GROUP_TO_PILLAR.get(group, "EXCLUDE")
        return mapping

    def _aggregate_journal(self, ledger_map: Dict[str, str]) -> Dict[str, float]:
        """Stream-process the JV CSV and sum net balances per pillar."""
        pillars = {p: 0.0 for p in set(_GROUP_TO_PILLAR.values()) if p != "EXCLUDE"}

        for chunk in pd.read_csv(
            self.jv_path, encoding="latin1", chunksize=self.chunk_size
        ):
            for _, row in chunk.iterrows():
                ledger = str(row.get("PARTICULARS", "")).strip()
                pillar = ledger_map.get(ledger, "EXCLUDE")
                if pillar == "EXCLUDE":
                    continue

                debit  = float(row["DEBIT"])  if not pd.isna(row.get("DEBIT"))  else 0.0
                credit = float(row["CREDIT"]) if not pd.isna(row.get("CREDIT")) else 0.0

                # TallySync export: Debits are negative, Credits are positive
                if pillar in _CREDIT_NATURE:
                    balance = credit - debit
                else:
                    balance = debit - credit

                pillars[pillar] += balance

        return pillars

    def _collect_ledger_stats(self, ledger_map: Dict[str, str]) -> Dict:
        """Collect per-ledger debit/credit totals (used for Trial Balance)."""
        stats: Dict[str, Dict] = {}
        for chunk in pd.read_csv(
            self.jv_path, encoding="latin1", chunksize=self.chunk_size
        ):
            for _, row in chunk.iterrows():
                ledger = str(row.get("PARTICULARS", "")).strip()
                pillar = ledger_map.get(ledger, "EXCLUDE")
                debit  = float(row["DEBIT"])  if not pd.isna(row.get("DEBIT"))  else 0.0
                credit = float(row["CREDIT"]) if not pd.isna(row.get("CREDIT")) else 0.0

                if ledger not in stats:
                    stats[ledger] = {"Debit": 0.0, "Credit": 0.0, "Pillar": pillar}
                stats[ledger]["Debit"]  += debit
                stats[ledger]["Credit"] += credit
        return stats

    def _compute_ratios(self, p: Dict[str, float]) -> Dict[str, float]:
        """Apply ratio formulas to pillar totals. Returns NaN for undefined."""
        sd = safe_divide

        revenue     = p.get("revenue", 0.0)
        cogs        = p.get("cogs", 0.0)
        opex        = p.get("opex", 0.0)
        cash        = p.get("cash", 0.0)
        receivables = p.get("receivables", 0.0)
        inventory   = p.get("inventory", 0.0)
        other_ca    = p.get("other_current_assets", 0.0)
        payables    = p.get("payables", 0.0)
        other_cl    = p.get("other_current_liabilities", 0.0)
        fixed       = p.get("fixed_assets", 0.0)
        debt        = p.get("debt", 0.0)
        equity      = p.get("equity", 0.0)

        current_assets = cash + receivables + inventory + other_ca
        current_liab   = payables + other_cl
        total_assets   = current_assets + fixed
        total_liab     = current_liab + debt
        gross_profit   = revenue - cogs
        ebit           = revenue - cogs - opex   # EBIT approximation
        net_income     = ebit                    # No tax data available
        capital_employed = total_assets - current_liab

        return {
            # ── Profitability ──────────────────────────────────────────
            "gross_margin":     sd(gross_profit, revenue) * 100,
            "operating_margin": sd(ebit,         revenue) * 100,
            "net_margin":       sd(net_income,   revenue) * 100,
            "roa":              sd(net_income,   total_assets) * 100,
            "roe":              sd(net_income,   equity) * 100,
            "roce":             sd(ebit, capital_employed) * 100,

            # ── Liquidity ──────────────────────────────────────────────
            "current_ratio":   sd(current_assets,             current_liab),
            "quick_ratio":     sd(current_assets - inventory, current_liab),
            "cash_ratio":      sd(cash,                       current_liab),

            # ── Solvency / Leverage ────────────────────────────────────
            "debt_to_equity":    sd(debt,       equity),
            "debt_ratio":        sd(total_liab, total_assets),
            "interest_coverage": np.nan,  # Requires interest expense from Indirect Expenses

            # ── Efficiency ─────────────────────────────────────────────
            "asset_turnover":       sd(revenue, total_assets),
            "inventory_turnover":   sd(cogs,    inventory),
            "receivables_turnover": sd(revenue, receivables),

            # ── Cash Flow (approximation — no Cash Flow Statement) ─────
            "operating_cf_ratio": np.nan,
            "fcf_margin":         np.nan,
            "cash_conversion":    np.nan,

            # ── Raw values (used by downstream scorecard) ──────────────
            "total_revenue":  revenue,
            "ebitda":         ebit,
            "total_assets":   total_assets,
            "total_debt":     debt,
            "total_equity":   equity,
        }
