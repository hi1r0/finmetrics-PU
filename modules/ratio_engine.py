"""
ratio_engine.py
===============
Computes all financial ratios from parsed statements for every company.
Also calculates QoQ / YoY changes and CAGR for trend analysis.
"""

import logging
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from modules.utils import safe_divide, pct_change

logger = logging.getLogger(__name__)


class RatioEngine:
    """
    Computes financial ratios for a set of parsed company statements.

    Usage
    -----
    engine = RatioEngine()
    ratio_df = engine.compute_all(parsed_data)   # cross-sectional DataFrame
    """

    # ── Public API ────────────────────────────────────────────────────────────

    def compute_all(
        self,
        parsed: Dict[str, Dict[str, pd.DataFrame]],
        market_info: Optional[Dict[str, Dict]] = None,
    ) -> pd.DataFrame:
        """
        Compute the latest-quarter ratios for every company.

        Returns
        -------
        DataFrame  rows = tickers, columns = ratio names
        """
        rows: Dict[str, Dict[str, float]] = {}
        for ticker, stmts in parsed.items():
            try:
                ratios = self._compute_ticker_ratios(ticker, stmts, market_info)
                rows[ticker] = ratios
            except Exception as exc:
                logger.error("Ratio calc failed for %s: %s", ticker, exc)

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows).T
        df.index.name = "ticker"
        return df

    def compute_ratio_history(
        self,
        ticker: str,
        stmts: Dict[str, pd.DataFrame],
    ) -> pd.DataFrame:
        """
        Compute quarterly ratio time-series for one company.
        Returns DataFrame: rows = dates, columns = ratio names.
        """
        income_q = stmts.get("income_q", pd.DataFrame())
        balance_q = stmts.get("balance_q", pd.DataFrame())
        cashflow_q = stmts.get("cashflow_q", pd.DataFrame())

        dates = sorted(
            set(income_q.index.tolist())
            | set(balance_q.index.tolist())
            | set(cashflow_q.index.tolist())
        )
        if not dates:
            return pd.DataFrame()

        records = []
        for date in dates:
            inc = self._row(income_q, date)
            bal = self._row(balance_q, date)
            cf = self._row(cashflow_q, date)
            r = self._compute_ratios_from_rows(inc, bal, cf)
            r["date"] = date
            records.append(r)

        df = pd.DataFrame(records).set_index("date").sort_index()
        return df

    def compute_changes(self, ratio_history: pd.DataFrame) -> pd.DataFrame:
        """
        Compute QoQ and YoY percentage changes for each ratio.
        Returns DataFrame with same index, columns suffixed _qoq / _yoy.
        """
        qoq = ratio_history.pct_change(1) * 100
        yoy = ratio_history.pct_change(4) * 100   # 4 quarters ≈ 1 year
        qoq.columns = [f"{c}_qoq" for c in qoq.columns]
        yoy.columns = [f"{c}_yoy" for c in yoy.columns]
        return pd.concat([qoq, yoy], axis=1)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _compute_ticker_ratios(
        self,
        ticker: str,
        stmts: Dict[str, pd.DataFrame],
        market_info: Optional[Dict[str, Dict]],
    ) -> Dict[str, float]:
        """Extract latest-quarter rows and compute all ratios."""
        inc = self._latest(self._first_valid(stmts, "income_q", "income"))
        bal = self._latest(self._first_valid(stmts, "balance_q", "balance"))
        cf = self._latest(self._first_valid(stmts, "cashflow_q", "cashflow"))

        ratios = self._compute_ratios_from_rows(inc, bal, cf)

        # ── Valuation ratios from market_info ────────────────────────────────
        if market_info and ticker in market_info:
            mi = market_info[ticker]
            ratios["pe_ratio"] = mi.get("pe_ratio", np.nan)
            ratios["pb_ratio"] = mi.get("pb_ratio", np.nan)
            ratios["ev_ebitda"] = mi.get("ev_ebitda", np.nan)
            ratios["eps"] = mi.get("eps_ttm", np.nan)
            ratios["market_cap"] = mi.get("market_cap", np.nan)
            ratios["dividend_yield"] = mi.get("dividend_yield", np.nan)

        return ratios

    @staticmethod
    def _safe_get(src: pd.Series, key: str) -> float:
        """Safely extract a scalar float from a Series.
        Handles missing keys, NaN, and edge cases where duplicate
        columns might return a non-scalar."""
        try:
            val = src.get(key, np.nan)
            # If get() returned something non-scalar (e.g. a Series/DataFrame
            # from duplicate columns), take the first non-NaN value
            if isinstance(val, (pd.Series, pd.DataFrame)):
                if isinstance(val, pd.DataFrame):
                    val = val.iloc[0]
                val = val.dropna()
                if val.empty:
                    return np.nan
                val = val.iloc[0] if len(val) > 1 else val.item()
            result = float(val)
            return result if not np.isnan(result) else np.nan
        except (TypeError, ValueError, IndexError):
            return np.nan

    @staticmethod
    def _compute_ratios_from_rows(
        inc: pd.Series, bal: pd.Series, cf: pd.Series
    ) -> Dict[str, float]:
        """Core ratio calculations from three Series (income, balance, cashflow)."""
        def g(key: str, src: pd.Series) -> float:
            return RatioEngine._safe_get(src, key)

        # Income
        revenue = g("total_revenue", inc)
        gross_profit = g("gross_profit", inc)
        operating_income = g("operating_income", inc)
        net_income = g("net_income", inc)
        interest_expense = g("interest_expense", inc)
        ebitda = g("ebitda", inc)
        tax_provision = g("tax_provision", inc)
        pretax_income = g("pretax_income", inc)
        da = g("depreciation_amortization", inc)

        # Balance
        total_assets = g("total_assets", bal)
        total_liabilities = g("total_liabilities", bal)
        total_equity = g("total_equity", bal)
        current_assets = g("current_assets", bal)
        current_liabilities = g("current_liabilities", bal)
        cash = g("cash_and_equivalents", bal)
        inventory = g("inventory", bal)
        receivables = g("accounts_receivable", bal)
        total_debt = g("total_debt", bal)
        long_term_debt = g("long_term_debt", bal)

        # Cash flow
        op_cf = g("operating_cashflow", cf)
        capex = abs(g("capital_expenditure", cf)) if not np.isnan(g("capital_expenditure", cf)) else np.nan
        free_cf = g("free_cashflow", cf)
        if np.isnan(free_cf) and not np.isnan(op_cf) and not np.isnan(capex):
            free_cf = op_cf - capex

        sd = safe_divide

        return {
            # ── LIQUIDITY ────────────────────────────────────────────────────
            "current_ratio":   sd(current_assets, current_liabilities),
            "quick_ratio":     sd(current_assets - inventory, current_liabilities),
            "cash_ratio":      sd(cash, current_liabilities),

            # ── LEVERAGE ─────────────────────────────────────────────────────
            "debt_to_equity":      sd(total_debt, total_equity),
            "debt_ratio":          sd(total_liabilities, total_assets),
            "interest_coverage":   sd(operating_income, abs(interest_expense) if interest_expense else np.nan),

            # ── PROFITABILITY ─────────────────────────────────────────────────
            "gross_margin":     sd(gross_profit, revenue) * 100,
            "operating_margin": sd(operating_income, revenue) * 100,
            "net_margin":       sd(net_income, revenue) * 100,
            "roe":              sd(net_income, total_equity) * 100,
            "roa":              sd(net_income, total_assets) * 100,
            "roce":             sd(operating_income, total_assets - current_liabilities) * 100,

            # ── EFFICIENCY ───────────────────────────────────────────────────
            "asset_turnover":       sd(revenue, total_assets),
            "inventory_turnover":   sd(revenue, inventory),
            "receivables_turnover": sd(revenue, receivables),

            # ── CASH FLOW ────────────────────────────────────────────────────
            "operating_cf_ratio":   sd(op_cf, current_liabilities),
            "fcf_margin":           sd(free_cf, revenue) * 100,
            "cash_conversion":      sd(op_cf, net_income),

            # ── RAW VALUES (used downstream) ─────────────────────────────────
            "total_revenue":    revenue,
            "net_income":       net_income,
            "ebitda":           ebitda,
            "operating_cashflow": op_cf,
            "free_cashflow":    free_cf,
            "total_debt":       total_debt,
            "total_equity":     total_equity,
            "total_assets":     total_assets,
        }

    @staticmethod
    def _latest(df: Optional[pd.DataFrame]) -> pd.Series:
        """Return last row of df as Series, or empty Series if unavailable."""
        if df is None or df.empty:
            return pd.Series(dtype=float)
        return df.iloc[-1]

    @staticmethod
    def _first_valid(stmts: Dict[str, pd.DataFrame], *keys: str) -> Optional[pd.DataFrame]:
        """Return the first non-None, non-empty DataFrame from stmts for the given keys.
        Avoids using Python `or` on DataFrames which triggers truth-value ambiguity."""
        for key in keys:
            df = stmts.get(key)
            if df is not None and not df.empty:
                return df
        return None

    @staticmethod
    def _row(df: pd.DataFrame, date) -> pd.Series:
        """Return row nearest to date, or empty Series."""
        if df.empty:
            return pd.Series(dtype=float)
        if date in df.index:
            return df.loc[date]
        # Find closest date
        diffs = abs(df.index - date)
        nearest = df.index[diffs.argmin()]
        if abs((nearest - date).days) <= 45:
            return df.loc[nearest]
        return pd.Series(dtype=float)

    # ── Growth metrics ────────────────────────────────────────────────────────

    @staticmethod
    def compute_growth_metrics(
        parsed: Dict[str, Dict[str, pd.DataFrame]]
    ) -> pd.DataFrame:
        """
        Compute YoY revenue / net income / EBITDA / OCF growth for every ticker.
        Uses annual statements (income, cashflow).
        """
        rows: Dict[str, Dict[str, float]] = {}
        for ticker, stmts in parsed.items():
            inc = stmts.get("income", pd.DataFrame())
            cf = stmts.get("cashflow", pd.DataFrame())

            if inc.empty or len(inc) < 2:
                continue

            latest = inc.iloc[-1]
            prior = inc.iloc[-2]
            latest_cf = cf.iloc[-1] if not cf.empty else pd.Series(dtype=float)
            prior_cf = cf.iloc[-2] if len(cf) >= 2 else pd.Series(dtype=float)

            rows[ticker] = {
                "revenue_growth": pct_change(
                    latest.get("total_revenue", np.nan),
                    prior.get("total_revenue", np.nan)
                ),
                "net_income_growth": pct_change(
                    latest.get("net_income", np.nan),
                    prior.get("net_income", np.nan)
                ),
                "ebitda_growth": pct_change(
                    latest.get("ebitda", np.nan),
                    prior.get("ebitda", np.nan)
                ),
                "ocf_growth": pct_change(
                    latest_cf.get("operating_cashflow", np.nan),
                    prior_cf.get("operating_cashflow", np.nan)
                ),
            }

        return pd.DataFrame(rows).T if rows else pd.DataFrame()