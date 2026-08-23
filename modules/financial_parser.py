"""
financial_parser.py
===================
Standardises raw yfinance DataFrames into a canonical structure
with normalised column names, consistent dtypes, and clean indices.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CANONICAL FIELD ALIASES
# Maps many possible yfinance row-name variants to a single canonical key
# ─────────────────────────────────────────────────────────────────────────────
INCOME_ALIASES: Dict[str, List[str]] = {
    "total_revenue": [
        "Total Revenue", "Revenue", "Net Revenue", "TotalRevenue",
        "Net Sales", "Revenues", "Operating Revenue",
    ],
    "cost_of_revenue": [
        "Cost Of Revenue", "Cost of Goods Sold", "CostOfRevenue",
        "Cost Of Goods Sold", "COGS", "Reconciled Cost Of Revenue",
    ],
    "gross_profit": [
        "Gross Profit", "GrossProfit",
    ],
    "operating_income": [
        "Operating Income", "EBIT", "Operating Profit", "OperatingIncome",
        "Ebit",
    ],
    "ebitda": [
        "EBITDA", "Ebitda", "Normalized EBITDA",
    ],
    "net_income": [
        "Net Income", "Net Income Common Stockholders", "NetIncome",
        "Net Income From Continuing Operations",
        "Net Income Continuous Operations",
        "Net Income From Continuing Operation Net Minority Interest",
        "Net Income Including Noncontrolling Interests",
        "Diluted NI Availto Com Stockholders",
    ],
    "interest_expense": [
        "Interest Expense", "InterestExpense",
        "Interest Expense Non Operating",
    ],
    "interest_income": [
        "Interest Income", "Interest Income Non Operating",
        "Net Interest Income",
    ],
    "tax_provision": [
        "Tax Provision", "TaxProvision", "Income Tax Expense",
    ],
    "pretax_income": [
        "Pretax Income", "PretaxIncome", "Income Before Tax",
    ],
    "depreciation_amortization": [
        "Depreciation", "Depreciation And Amortization",
        "DepreciationAndAmortization", "D&A",
        "Reconciled Depreciation",
        "Depreciation And Amortization In Income Statement",
        "Depreciation Income Statement",
    ],
    "total_expenses": [
        "Total Expenses", "TotalExpenses", "Operating Expenses",
        "Operating Expense",
    ],
    "selling_general_admin": [
        "Selling General And Administration",
        "General And Administrative Expense",
    ],
    "basic_eps": [
        "Basic EPS", "BasicEPS",
    ],
    "diluted_eps": [
        "Diluted EPS", "DilutedEPS",
    ],
}

BALANCE_ALIASES: Dict[str, List[str]] = {
    "total_assets": [
        "Total Assets", "TotalAssets",
    ],
    "total_liabilities": [
        "Total Liabilities Net Minority Interest", "Total Liabilities",
        "TotalLiabilitiesNetMinorityInterest",
    ],
    "total_equity": [
        "Stockholders Equity", "Total Stockholders Equity",
        "Common Stock Equity", "StockholdersEquity",
        "TotalEquityGrossMinorityInterest",
        "Total Equity Gross Minority Interest",
    ],
    "current_assets": [
        "Current Assets", "Total Current Assets", "CurrentAssets",
    ],
    "current_liabilities": [
        "Current Liabilities", "Total Current Liabilities",
        "CurrentLiabilities",
    ],
    "cash_and_equivalents": [
        "Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments",
        "CashAndCashEquivalents", "Cash Financial", "Cash Equivalents",
    ],
    "inventory": [
        "Inventory", "Inventories",
    ],
    "accounts_receivable": [
        "Receivables", "Net Receivables", "Accounts Receivable",
        "AccountsReceivable", "Gross Accounts Receivable",
    ],
    "total_debt": [
        "Total Debt", "TotalDebt", "Long Term Debt And Capital Lease Obligation",
    ],
    "long_term_debt": [
        "Long Term Debt", "LongTermDebt",
    ],
    "short_term_debt": [
        "Current Debt", "Short Long Term Debt",
        "CurrentDebtAndCapitalLeaseObligation",
        "Current Debt And Capital Lease Obligation",
    ],
    "goodwill": [
        "Goodwill", "GoodwillAndOtherIntangibleAssets",
        "Goodwill And Other Intangible Assets",
    ],
    "net_ppe": [
        "Net PPE", "Property Plant Equipment Net",
    ],
    "retained_earnings": [
        "Retained Earnings",
    ],
    "working_capital": [
        "Working Capital",
    ],
}

CASHFLOW_ALIASES: Dict[str, List[str]] = {
    "operating_cashflow": [
        "Operating Cash Flow", "Cash From Operations",
        "Net Cash Provided By Operating Activities",
        "OperatingCashFlow",
    ],
    "investing_cashflow": [
        "Investing Cash Flow", "Cash From Investing Activities",
        "Net Cash Provided By Investing Activities",
        "InvestingCashFlow",
    ],
    "financing_cashflow": [
        "Financing Cash Flow", "Cash From Financing Activities",
        "Net Cash Provided By Financing Activities",
        "FinancingCashFlow",
    ],
    "capital_expenditure": [
        "Capital Expenditure", "CapitalExpenditure", "Purchase Of PPE",
        "Capital Expenditures",
    ],
    "free_cashflow": [
        "Free Cash Flow", "FreeCashFlow",
    ],
    "depreciation_amortization": [
        "Depreciation Amortization Depletion",
        "Depreciation And Amortization",
        "Depreciation",
        "Amortization Cash Flow",
    ],
    "changes_in_working_capital": [
        "Changes In Working Capital", "Change In Working Capital",
    ],
}

ALIAS_MAP = {
    "income": INCOME_ALIASES,
    "balance": BALANCE_ALIASES,
    "cashflow": CASHFLOW_ALIASES,
}


# ─────────────────────────────────────────────────────────────────────────────

class FinancialParser:
    """
    Cleans and standardises raw financial DataFrames.

    Usage
    -----
    parser = FinancialParser()
    parsed = parser.parse_all(raw_data_dict)
    """

    def __init__(self) -> None:
        self._alias_lookup: Dict[str, Dict[str, str]] = self._build_reverse_lookup()

    # ── Public API ────────────────────────────────────────────────────────────

    def parse_all(
        self, raw: Dict[str, Dict[str, pd.DataFrame]]
    ) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Parse every ticker's raw data dictionary.

        Parameters
        ----------
        raw : {ticker: {stmt_key: raw_df}}

        Returns
        -------
        {ticker: {"income": df, "balance": df, "cashflow": df,
                  "income_q": df, "balance_q": df, "cashflow_q": df}}
        """
        parsed: Dict[str, Dict[str, pd.DataFrame]] = {}
        for ticker, stmts in raw.items():
            try:
                parsed[ticker] = self._parse_ticker(ticker, stmts)
            except Exception as exc:
                logger.error("Parsing failed for %s: %s", ticker, exc)
        return parsed

    def parse_ticker(
        self, ticker: str, stmts: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        return self._parse_ticker(ticker, stmts)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _parse_ticker(
        self, ticker: str, stmts: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        mapping = {
            "income_q": ("quarterly_income_stmt", "income"),
            "balance_q": ("quarterly_balance_sheet", "balance"),
            "cashflow_q": ("quarterly_cashflow", "cashflow"),
            "income": ("income_stmt", "income"),
            "balance": ("balance_sheet", "balance"),
            "cashflow": ("cashflow", "cashflow"),
        }
        result: Dict[str, pd.DataFrame] = {}
        for out_key, (raw_key, alias_type) in mapping.items():
            df = stmts.get(raw_key)
            if df is not None and not df.empty:
                result[out_key] = self._standardise(df, alias_type, ticker)
        return result

    def _standardise(
        self, df: pd.DataFrame, alias_type: str, ticker: str
    ) -> pd.DataFrame:
        """
        Rename columns to canonical names, drop extras, fill NaN, sort by date.
        df rows = dates (already transposed by DataFetcher).
        """
        df = df.copy()

        # 1. Normalise existing column names → canonical
        #    We must handle the case where multiple raw columns map
        #    to the SAME canonical name (e.g. "EBIT" and "Operating Income"
        #    both → "operating_income").  We keep only the first match
        #    for each canonical name, preferring earlier entries in
        #    the alias list (which are more specific).
        alias_dict = ALIAS_MAP.get(alias_type, {})
        canonical_cols = list(alias_dict.keys())

        # Build rename map, tracking which canonical names we've seen
        col_map: Dict[str, str] = {}
        seen_canonical: set = set()

        for col in df.columns:
            canonical = self._resolve_alias(str(col), alias_dict)
            if canonical and canonical not in seen_canonical:
                col_map[col] = canonical
                seen_canonical.add(canonical)

        df = df.rename(columns=col_map)

        # 2. Keep only columns with a canonical name (drop unknown & duplicates)
        present = [c for c in canonical_cols if c in df.columns]

        # Safety: deduplicate columns in case renaming still left duplicates
        if df.columns.duplicated().any():
            df = df.loc[:, ~df.columns.duplicated(keep="first")]
            # Re-filter after dedup
            present = [c for c in canonical_cols if c in df.columns]

        df = df[present]

        # 3. Convert all to numeric
        df = df.apply(pd.to_numeric, errors="coerce")

        # 4. Replace inf with NaN
        df = df.replace([np.inf, -np.inf], np.nan)

        # 5. Sort ascending (oldest first) – useful for growth calcs
        df = df.sort_index()

        logger.debug("%s | %s → %d rows × %d cols", ticker, alias_type, *df.shape)
        return df

    @staticmethod
    def _build_reverse_lookup() -> Dict[str, Dict[str, str]]:
        """Build {alias_type: {raw_name_lower: canonical}} lookup."""
        result: Dict[str, Dict[str, str]] = {}
        for atype, alias_dict in ALIAS_MAP.items():
            lookup: Dict[str, str] = {}
            for canonical, variants in alias_dict.items():
                for v in variants:
                    lookup[v.lower()] = canonical
            result[atype] = lookup
        return result

    def _resolve_alias(self, raw_name: str, alias_dict: Dict[str, List[str]]) -> Optional[str]:
        """Return canonical name for raw_name, or None if unknown."""
        norm = raw_name.strip().lower()
        for canonical, variants in alias_dict.items():
            for v in variants:
                if v.lower() == norm:
                    return canonical
        return None

    # ── Cross-company matrix builder ──────────────────────────────────────────

    @staticmethod
    def build_latest_snapshot(
        parsed: Dict[str, Dict[str, pd.DataFrame]],
        stmt_key: str = "income_q",
    ) -> pd.DataFrame:
        """
        Extract the most-recent row from stmt_key for every ticker.
        Returns DataFrame: rows = tickers, columns = financial fields.
        """
        rows: Dict[str, pd.Series] = {}
        for ticker, stmts in parsed.items():
            df = stmts.get(stmt_key)
            if df is not None and not df.empty:
                rows[ticker] = df.iloc[-1]   # most recent
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows).T