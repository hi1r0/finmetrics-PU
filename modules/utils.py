"""
utils.py
========
Shared utility functions used across all modules.
"""

import os
import json
import logging
import hashlib
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from functools import wraps
from datetime import datetime

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_CACHE = PROJECT_ROOT / "data" / "cache"
OUTPUTS_CHARTS = PROJECT_ROOT / "outputs" / "charts"
OUTPUTS_REPORTS = PROJECT_ROOT / "outputs" / "reports"
OUTPUTS_TABLES = PROJECT_ROOT / "outputs" / "tables"

for _p in [DATA_RAW, DATA_PROCESSED, DATA_CACHE, OUTPUTS_CHARTS, OUTPUTS_REPORTS, OUTPUTS_TABLES]:
    _p.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with a consistent format."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# ─────────────────────────────────────────────────────────────────────────────
# RETRY DECORATOR
# ─────────────────────────────────────────────────────────────────────────────

def retry(max_attempts: int = 3, delay: float = 2.0, exceptions=(Exception,)):
    """Decorator: retry a function up to max_attempts times on failure."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    logger.warning(
                        "Attempt %d/%d failed for %s: %s",
                        attempt, max_attempts, func.__name__, exc,
                    )
                    if attempt < max_attempts:
                        time.sleep(delay * attempt)
            logger.error("All %d attempts failed for %s.", max_attempts, func.__name__)
            return None
        return wrapper
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# FILE CACHE
# ─────────────────────────────────────────────────────────────────────────────

def cache_key(ticker: str, data_type: str) -> str:
    raw = f"{ticker}_{data_type}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def save_cache(ticker: str, data_type: str, df: pd.DataFrame, ttl_hours: int = 24) -> None:
    key = cache_key(ticker, data_type)
    path = DATA_CACHE / f"{key}.parquet"
    meta_path = DATA_CACHE / f"{key}.meta.json"
    try:
        df.to_parquet(path)
        meta = {"ticker": ticker, "data_type": data_type,
                "saved_at": datetime.utcnow().isoformat(), "ttl_hours": ttl_hours}
        meta_path.write_text(json.dumps(meta))
    except Exception as exc:
        logger.warning("Cache save failed for %s/%s: %s", ticker, data_type, exc)


def load_cache(ticker: str, data_type: str) -> Optional[pd.DataFrame]:
    key = cache_key(ticker, data_type)
    path = DATA_CACHE / f"{key}.parquet"
    meta_path = DATA_CACHE / f"{key}.meta.json"
    if not path.exists() or not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text())
        saved_at = datetime.fromisoformat(meta["saved_at"])
        age_hours = (datetime.utcnow() - saved_at).total_seconds() / 3600
        if age_hours > meta.get("ttl_hours", 24):
            logger.debug("Cache expired for %s/%s.", ticker, data_type)
            return None
        return pd.read_parquet(path)
    except Exception as exc:
        logger.warning("Cache load failed for %s/%s: %s", ticker, data_type, exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# NUMERIC HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def safe_divide(numerator: float, denominator: float, default: float = np.nan) -> float:
    """Division that returns default when denominator is zero or NaN."""
    try:
        if pd.isna(denominator) or denominator == 0:
            return default
        return numerator / denominator
    except Exception:
        return default


def pct_change(current: float, previous: float) -> float:
    """Percentage change with zero/NaN denominator guard."""
    return safe_divide(current - previous, abs(previous)) * 100


def winsorise(series: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    """Clip series at given quantile bounds."""
    lo, hi = series.quantile(lower), series.quantile(upper)
    return series.clip(lo, hi)


def to_numeric_series(series: pd.Series) -> pd.Series:
    """Coerce all values to float, replacing errors with NaN."""
    return pd.to_numeric(series, errors="coerce")


# ─────────────────────────────────────────────────────────────────────────────
# DATAFRAME HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase, strip, replace spaces with underscores."""
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df


def drop_all_nan_rows(df: pd.DataFrame, thresh: float = 0.7) -> pd.DataFrame:
    """Drop rows where more than `thresh` fraction of values are NaN."""
    min_count = int((1 - thresh) * len(df.columns))
    return df.dropna(thresh=max(min_count, 1))


def flatten_multiindex(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten MultiIndex columns to single level string."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["_".join(map(str, col)).strip() for col in df.columns]
    return df


def align_dates(dfs: List[pd.DataFrame]) -> List[pd.DataFrame]:
    """Reindex all DataFrames to a common date union."""
    all_dates = sorted(set().union(*[set(df.index) for df in dfs]))
    return [df.reindex(all_dates) for df in dfs]


# ─────────────────────────────────────────────────────────────────────────────
# FORMATTING
# ─────────────────────────────────────────────────────────────────────────────

def format_crore(value: float, decimals: int = 2) -> str:
    """Format large INR values as ₹X Cr."""
    if pd.isna(value):
        return "N/A"
    return f"₹{value / 1e7:,.{decimals}f} Cr"


def format_pct(value: float, decimals: int = 1) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{value:.{decimals}f}%"


def severity_label(score: float) -> str:
    """Convert numeric severity score to human-readable label."""
    if pd.isna(score):
        return "Unknown"
    if score >= 3.0:
        return "Critical"
    if score >= 2.0:
        return "High"
    if score >= 1.0:
        return "Medium"
    return "Low"