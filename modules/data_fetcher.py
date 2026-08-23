"""
data_fetcher.py
===============
Fetches financial statements and market data from yfinance for NSE tickers.
Implements caching, retry logic, and structured logging.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
import yfinance as yf

from modules.utils import retry, save_cache, load_cache

logger = logging.getLogger(__name__)

# Statement types returned per ticker
STATEMENT_KEYS = [
    "quarterly_income_stmt",
    "quarterly_balance_sheet",
    "quarterly_cashflow",
    "income_stmt",
    "balance_sheet",
    "cashflow",
]


class DataFetcher:
    """
    Fetches and caches financial data from yfinance.

    Parameters
    ----------
    use_cache : bool
        Whether to load from local cache before hitting the API.
    cache_ttl_hours : int
        How many hours a cached response is considered fresh.
    delay_seconds : float
        Politeness delay between consecutive API calls.
    """

    def __init__(
        self,
        use_cache: bool = True,
        cache_ttl_hours: int = 24,
        delay_seconds: float = 0.5,
    ) -> None:
        self.use_cache = use_cache
        self.cache_ttl_hours = cache_ttl_hours
        self.delay_seconds = delay_seconds

    # ── Public API ────────────────────────────────────────────────────────────

    def fetch_all(
        self, tickers: List[str], progress_callback=None
    ) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Fetch all statements for a list of tickers.

        Returns
        -------
        dict  ticker → {statement_key → DataFrame}
        """
        results: Dict[str, Dict[str, pd.DataFrame]] = {}
        total = len(tickers)

        for idx, ticker in enumerate(tickers):
            logger.info("Fetching [%d/%d] %s …", idx + 1, total, ticker)
            data = self.fetch_ticker(ticker)
            if data:
                results[ticker] = data
            else:
                logger.warning("No data returned for %s — skipped.", ticker)

            if progress_callback:
                progress_callback(idx + 1, total, ticker)

            time.sleep(self.delay_seconds)

        logger.info("Completed fetch: %d/%d tickers successful.", len(results), total)
        return results

    def fetch_ticker(self, ticker: str) -> Optional[Dict[str, pd.DataFrame]]:
        """
        Fetch all statement types for one ticker.

        Returns a dict of {statement_key: DataFrame} or None on total failure.
        """
        result: Dict[str, pd.DataFrame] = {}

        # Try loading everything from cache first
        if self.use_cache:
            all_cached = True
            for key in STATEMENT_KEYS:
                cached = load_cache(ticker, key)
                if cached is not None:
                    result[key] = cached
                else:
                    all_cached = False
                    break
            if all_cached and result:
                logger.debug("Cache hit for %s.", ticker)
                return result

        # Live fetch via yfinance
        try:
            t = yf.Ticker(ticker)
            result = self._extract_statements(t, ticker)
        except Exception as exc:
            logger.error("yfinance error for %s: %s", ticker, exc)
            return None

        # Cache individual statements
        if self.use_cache:
            for key, df in result.items():
                if df is not None and not df.empty:
                    save_cache(ticker, key, df, ttl_hours=self.cache_ttl_hours)

        return result if result else None

    def fetch_market_info(self, ticker: str) -> Dict:
        """Fetch basic market info (PE, PB, market cap, etc.)."""
        try:
            t = yf.Ticker(ticker)
            info = t.info or {}
            return {
                "market_cap": info.get("marketCap", np.nan),
                "pe_ratio": info.get("trailingPE", np.nan),
                "pb_ratio": info.get("priceToBook", np.nan),
                "ev_ebitda": info.get("enterpriseToEbitda", np.nan),
                "beta": info.get("beta", np.nan),
                "52w_high": info.get("fiftyTwoWeekHigh", np.nan),
                "52w_low": info.get("fiftyTwoWeekLow", np.nan),
                "dividend_yield": info.get("dividendYield", np.nan),
                "eps_ttm": info.get("trailingEps", np.nan),
                "current_price": info.get("currentPrice", np.nan),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "company_name": info.get("longName", ticker),
            }
        except Exception as exc:
            logger.warning("market_info failed for %s: %s", ticker, exc)
            return {}

    # ── Private helpers ───────────────────────────────────────────────────────

    @retry(max_attempts=3, delay=2.0)
    def _extract_statements(
        self, ticker_obj: yf.Ticker, ticker: str
    ) -> Dict[str, pd.DataFrame]:
        """Extract and lightly clean all statement DataFrames."""
        mapping = {
            "quarterly_income_stmt": self._get_df(ticker_obj, "quarterly_income_stmt"),
            "quarterly_balance_sheet": self._get_df(ticker_obj, "quarterly_balance_sheet"),
            "quarterly_cashflow": self._get_df(ticker_obj, "quarterly_cashflow"),
            "income_stmt": self._get_df(ticker_obj, "income_stmt"),
            "balance_sheet": self._get_df(ticker_obj, "balance_sheet"),
            "cashflow": self._get_df(ticker_obj, "cashflow"),
        }
        # Drop completely empty statements
        return {k: v for k, v in mapping.items() if v is not None and not v.empty}

    @staticmethod
    def _get_df(ticker_obj: yf.Ticker, attr: str) -> Optional[pd.DataFrame]:
        """
        Safely access a yfinance attribute and return a cleaned DataFrame.
        Handles both old-style (financials/balancesheet) and new-style attribute names.
        """
        aliases = {
            "quarterly_income_stmt": ["quarterly_income_stmt", "quarterly_financials"],
            "quarterly_balance_sheet": ["quarterly_balance_sheet", "quarterly_balancesheet"],
            "quarterly_cashflow": ["quarterly_cashflow", "quarterly_cash_flow"],
            "income_stmt": ["income_stmt", "financials"],
            "balance_sheet": ["balance_sheet", "balancesheet"],
            "cashflow": ["cashflow", "cash_flow"],
        }
        for name in aliases.get(attr, [attr]):
            try:
                df = getattr(ticker_obj, name, None)
                if df is not None and not df.empty:
                    df = df.T  # rows = dates, cols = line items
                    df = df.apply(pd.to_numeric, errors="coerce")
                    df.index = pd.to_datetime(df.index, errors="coerce")
                    df = df[~df.index.isna()].sort_index(ascending=False)
                    return df
            except Exception as exc:
                logger.debug("Attribute %s failed: %s", name, exc)
        return None

    # ── Convenience ───────────────────────────────────────────────────────────

    def get_price_history(
        self,
        ticker: str,
        period: str = "2y",
        interval: str = "1mo",
    ) -> pd.DataFrame:
        """Fetch OHLCV price history."""
        try:
            df = yf.download(ticker, period=period, interval=interval, progress=False)
            return df
        except Exception as exc:
            logger.warning("Price history failed for %s: %s", ticker, exc)
            return pd.DataFrame()