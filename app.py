"""
app.py
======
Financial Outlier Detection & Benchmarking System — Streamlit Dashboard (v2.0)
"""

import logging
import time
import io
import os
from pathlib import Path
from typing import Dict, List, Optional

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ── Module imports ─────────────────────────────────────────────────────────
from modules.sector_loader import SectorLoader
from modules.data_fetcher import DataFetcher
from modules.financial_parser import FinancialParser
from modules.ratio_engine import RatioEngine
from modules.outlier_engine import OutlierEngine, RATIO_LABELS
from modules.report_generator import ReportGenerator

# V2.0 Modules
from modules.benchmark_core import BenchmarkCore, BenchmarkCoreResult
from modules.benchmark_store import BenchmarkStore
from modules.client_comparator import ClientComparator
from modules.visualization import (
    ratio_boxplot, ratio_heatmap, radar_chart,
    outlier_scatter, correlation_heatmap,
    health_score_bars, health_score_bars_with_client,
    ratio_trend, outlier_table,
    plot_ratio_scorecard, plot_peer_stats_heatmap,
    plot_client_peer_scatter
)
from modules.ai_handler import AIHandler
from modules.tally_bridge import TallyBridge
from modules.utils import setup_logging, severity_label, format_pct, safe_divide

from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

setup_logging()
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS — Abyss Teal Palette
# ──────────────────────────────────────────────────────────────────────────────
def inject_custom_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css?family=Google+Sans:400,500,700');

        /* ── Base typography ────────────────────────────────────── */
        html, body, [class*="css"], .stMarkdown, .stButton, .stTextInput,
        .stSelectbox, .stRadio, .stSlider, .stNumberInput, .stTextArea {
            font-family: 'Google Sans', sans-serif !important;
        }

        .st-emotion-cache-10trblm, .st-emotion-cache-zt5igj,
        .st-emotion-cache-16idsys {
            font-family: 'Google Sans', sans-serif !important;
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Google Sans', sans-serif !important;
            font-weight: 700 !important;
            color: #d4f0ec !important;
        }

        /* ── Sidebar ────────────────────────────────────────────── */
        [data-testid="stSidebar"] {
            font-family: 'Google Sans', sans-serif !important;
            background-color: #001f1e !important;
            border-right: 1px solid #1a3a37 !important;
        }
        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] label {
            color: #7ab8b2 !important;
        }

        /* ── Main area ──────────────────────────────────────────── */
        .stApp, [data-testid="stAppViewContainer"] {
            background-color: #001f1e !important;
        }
        [data-testid="stHeader"] {
            background-color: #001f1e !important;
        }

        /* ── Buttons ────────────────────────────────────────────── */
        .stButton > button {
            background-color: #003b38 !important;
            color: #d4f0ec !important;
            border: 1px solid #1a3a37 !important;
            border-radius: 6px !important;
            transition: all 0.2s ease;
        }
        .stButton > button:hover {
            background-color: #00c4a7 !important;
            color: #001f1e !important;
            border-color: #00c4a7 !important;
        }

        /* ── Inputs, selects, text areas ─────────────────────────── */
        .stTextInput input, .stTextArea textarea, .stSelectbox select,
        [data-baseweb="select"] {
            background-color: #0d2e2b !important;
            color: #d4f0ec !important;
            border-color: #1a3a37 !important;
        }

        /* ── Tabs ───────────────────────────────────────────────── */
        .stTabs [data-baseweb="tab-list"] {
            background-color: #002623 !important;
            border-radius: 8px;
            gap: 4px;
            padding: 6px 8px !important;
            flex-wrap: wrap;
        }
        .stTabs [data-baseweb="tab"] {
            color: #7ab8b2 !important;
            background-color: transparent !important;
            border-radius: 6px;
            padding: 8px 20px !important;
            font-size: 0.82rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.02em !important;
            white-space: nowrap !important;
            min-width: fit-content !important;
            transition: all 0.2s ease;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background-color: #003b38 !important;
            color: #d4f0ec !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #003b38 !important;
            color: #00c4a7 !important;
            border-bottom: 2px solid #00c4a7 !important;
        }

        /* ── Metrics ────────────────────────────────────────────── */
        [data-testid="stMetric"] {
            background-color: #002623;
            border: 1px solid #1a3a37;
            border-radius: 8px;
            padding: 12px 16px;
        }
        [data-testid="stMetricValue"] {
            color: #d4f0ec !important;
        }
        [data-testid="stMetricLabel"] {
            color: #7ab8b2 !important;
        }

        /* ── Expanders ──────────────────────────────────────────── */
        .streamlit-expanderHeader {
            background-color: #002623 !important;
            color: #d4f0ec !important;
            border: 1px solid #1a3a37 !important;
            border-radius: 6px !important;
        }

        /* ── Dataframes ─────────────────────────────────────────── */
        [data-testid="stDataFrame"] {
            border: 1px solid #1a3a37 !important;
            border-radius: 6px;
        }

        /* ── Dividers ───────────────────────────────────────────── */
        hr {
            border-color: #1a3a37 !important;
        }

        /* ── Toast / alerts ─────────────────────────────────────── */
        .stAlert {
            background-color: #002623 !important;
            border: 1px solid #1a3a37 !important;
            color: #d4f0ec !important;
        }

        /* ── Scrollbar ──────────────────────────────────────────── */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #001f1e; }
        ::-webkit-scrollbar-thumb { background: #1a3a37; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #3d6e69; }

        /* ── SWOT Cards ─────────────────────────────────────────── */
        .swot-card {
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 10px;
            border-left: 4px solid;
            font-family: 'Google Sans', sans-serif;
        }
        .swot-card .swot-ratio {
            font-weight: 600;
            font-size: 0.92rem;
            margin-bottom: 4px;
        }
        .swot-card .swot-values {
            font-size: 0.78rem;
            opacity: 0.7;
            margin-bottom: 6px;
        }
        .swot-card .swot-narrative {
            font-size: 0.84rem;
            line-height: 1.45;
        }
        .swot-strength {
            background-color: #0d2e1e;
            border-left-color: #1a7a3c;
        }
        .swot-strength .swot-ratio { color: #2ecc71; }
        .swot-weakness {
            background-color: #2e200d;
            border-left-color: #e67e22;
        }
        .swot-weakness .swot-ratio { color: #f39c12; }
        .swot-opportunity {
            background-color: #002623;
            border-left-color: #00c4a7;
        }
        .swot-opportunity .swot-ratio { color: #00c4a7; }
        .swot-threat {
            background-color: #2e0d0d;
            border-left-color: #c0392b;
        }
        .swot-threat .swot-ratio { color: #e74c3c; }

        .swot-header {
            font-family: 'Google Sans', sans-serif;
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 12px;
            padding: 8px 0;
        }

        /* ── Recommendation Grid ── */
        .rec-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .rec-card {
            background: linear-gradient(135deg, rgba(7, 25, 23, 0.6) 0%, rgba(11, 34, 32, 0.8) 100%);
            border: 1px solid rgba(0, 196, 167, 0.15);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
        }
        .rec-card:hover {
            border-color: rgba(0, 196, 167, 0.6);
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(0, 196, 167, 0.15);
        }
        .rec-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: #00c4a7;
        }
        .rec-card.priority-critical::before {
            background: #ff5e57;
        }
        .rec-card.priority-high::before {
            background: #ff9f43;
        }
        .rec-card.priority-medium::before {
            background: #00d2d3;
        }
        .rec-card.priority-strategic::before {
            background: #a55eea;
        }
        .rec-badge-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 14px;
            width: 100%;
        }
        .rec-badge {
            font-size: 0.65rem;
            font-weight: 700;
            letter-spacing: 0.8px;
            padding: 4px 10px;
            border-radius: 4px;
            text-transform: uppercase;
        }
        .rec-badge.critical {
            background: rgba(255, 94, 87, 0.12);
            color: #ff5e57;
            border: 1px solid rgba(255, 94, 87, 0.3);
        }
        .rec-badge.high {
            background: rgba(255, 159, 67, 0.12);
            color: #ff9f43;
            border: 1px solid rgba(255, 159, 67, 0.3);
        }
        .rec-badge.medium {
            background: rgba(0, 210, 211, 0.12);
            color: #00d2d3;
            border: 1px solid rgba(0, 210, 211, 0.3);
        }
        .rec-badge.strategic {
            background: rgba(165, 94, 234, 0.12);
            color: #a55eea;
            border: 1px solid rgba(165, 94, 234, 0.3);
        }
        .rec-cat {
            font-size: 0.65rem;
            font-weight: 700;
            color: #7ab8b2;
            background: rgba(122, 184, 178, 0.1);
            padding: 4px 8px;
            border-radius: 4px;
            border: 1px solid rgba(122, 184, 178, 0.2);
            letter-spacing: 0.5px;
        }
        .rec-step {
            font-size: 0.72rem;
            font-weight: 700;
            color: #00c4a7;
            margin-bottom: 8px;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        .rec-desc {
            font-size: 0.88rem;
            color: #d4f0ec;
            line-height: 1.5;
            font-weight: 500;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinMetrics Suite",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ──────────────────────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "parsed_data":    None,
        "market_info":    None,
        "selected_sector": None,
        "tickers_used":   [],
        "growth_df":      None,
        "anomaly_scores": None,
        "benchmark_result": None,
        "client_result": None,
        "ai_tickers": [],
        "gemini_api_key": "",
        "tally_client_ratios": None,
        "tally_client_name": "Client",
        "tally_trial_balance": None,       # pd.DataFrame from TallyBridge
        "tally_benchmark_result": None,    # BenchmarkCoreResult from ClientComparator
        "manual_mode":            False,
        "ai_chat_session":        None,    # genai.ChatSession object
        "ai_chat_history":        [],      # list of dicts: [{"role": "assistant"|"user", "content": str}]
        "ai_chat_active_client":  None,    # str (to detect client change and reset chat)
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ──────────────────────────────────────────────────────────────────────────────
# SINGLETONS
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_sector_loader(): return SectorLoader()

@st.cache_resource
def get_fetcher(): return DataFetcher(use_cache=True, cache_ttl_hours=12, delay_seconds=0.3)

@st.cache_resource
def get_parser(): return FinancialParser()

@st.cache_resource
def get_ratio_engine(): return RatioEngine()

@st.cache_resource
def get_outlier_engine(): return OutlierEngine(iqr_multiplier=1.5, zscore_threshold=3.5)

@st.cache_resource
def get_report_gen(): return ReportGenerator()

@st.cache_resource
def get_benchmark_store(): return BenchmarkStore()


# ──────────────────────────────────────────────────────────────────────────────
# PRIVATE MANUAL ENTRY HELPERS & RESOLVERS
# ──────────────────────────────────────────────────────────────────────────────
def get_sector_medians(sector: Optional[str]) -> Dict[str, float]:
    defaults = {
        "gross_margin": 15.0,
        "operating_margin": 8.0,
        "net_margin": 5.0,
        "roe": 12.0,
        "roa": 6.0,
        "roce": 10.0,
        "current_ratio": 1.5,
        "quick_ratio": 1.0,
        "cash_ratio": 0.5,
        "debt_to_equity": 0.5,
        "debt_ratio": 0.3,
        "interest_coverage": 3.0,
        "asset_turnover": 1.2,
        "inventory_turnover": 6.0,
        "receivables_turnover": 8.0,
        "revenue_growth": 10.0,
        "net_income_growth": 8.0,
        "ocf_growth": 5.0,
    }
    if not sector:
        return defaults
    
    try:
        store = get_benchmark_store()
        loaded = store.load(sector)
        if not loaded:
            return defaults
            
        peer_stats_df, _, _ = loaded
        if peer_stats_df is None or peer_stats_df.empty:
            return defaults
            
        for r in defaults.keys():
            if r in peer_stats_df.index:
                val = peer_stats_df.loc[r, "median"]
                if not pd.isna(val):
                    defaults[r] = float(val)
    except Exception as e:
        logger.error(f"Error resolving sector medians: {e}")
        
    return defaults


def compute_raw_figures_from_medians(medians: Dict[str, float]) -> Dict[str, float]:
    revenue = 10000000.0  # 10 Million base
    gm = medians.get("gross_margin", 15.0)
    om = medians.get("operating_margin", 8.0)
    
    cogs = revenue * (1.0 - gm / 100.0)
    ebit = revenue * (om / 100.0)
    opex = max(revenue - cogs - ebit, 0.0)
    
    # Asset structure
    asset_turnover = max(medians.get("asset_turnover", 1.2), 0.1)
    total_assets = revenue / asset_turnover
    
    inv_turnover = max(medians.get("inventory_turnover", 6.0), 0.1)
    inventory = cogs / inv_turnover
    
    rec_turnover = max(medians.get("receivables_turnover", 8.0), 0.1)
    receivables = revenue / rec_turnover
    
    # Let's say current assets represent about 50% of total assets
    current_assets = total_assets * 0.5
    fixed_assets = total_assets - current_assets
    
    cur_ratio = max(medians.get("current_ratio", 1.5), 0.1)
    current_liab = current_assets / cur_ratio
    
    cash_ratio = medians.get("cash_ratio", 0.5)
    cash = current_liab * cash_ratio
    
    # Ensure cash doesn't exceed current assets - inventory - receivables
    other_ca = max(current_assets - cash - inventory - receivables, 0.0)
    # Re-sum to make it exact
    current_assets = cash + inventory + receivables + other_ca
    total_assets = current_assets + fixed_assets
    
    # Liabilities & Equity structure
    debt_ratio = medians.get("debt_ratio", 0.3)
    total_liab = total_assets * debt_ratio
    equity = total_assets - total_liab
    
    debt_to_equity = medians.get("debt_to_equity", 0.5)
    debt = equity * debt_to_equity
    
    payables = current_liab * 0.6  # 60% of current liabilities is payables
    other_cl = max(current_liab - payables, 0.0)
    
    # Adjust debt and equity slightly to make total_liab and total_assets balance perfectly
    total_liab = current_liab + debt
    equity = total_assets - total_liab
    if equity < 0:
        equity = total_assets * 0.5
        debt = total_assets - equity - current_liab
        if debt < 0:
            debt = 0.0
            current_liab = total_assets - equity
    
    return {
        "revenue": round(revenue, 2),
        "cogs": round(cogs, 2),
        "opex": round(opex, 2),
        "cash": round(cash, 2),
        "receivables": round(receivables, 2),
        "inventory": round(inventory, 2),
        "other_current_assets": round(other_ca, 2),
        "fixed_assets": round(fixed_assets, 2),
        "payables": round(payables, 2),
        "other_current_liabilities": round(other_cl, 2),
        "debt": round(debt, 2),
        "equity": round(equity, 2),
    }


def update_manual_defaults():
    # Triggered when manual target sector or input method changes
    sec = st.session_state.get("manual_sector")
    medians = get_sector_medians(sec)
    
    # Direct ratios session state
    st.session_state.m_gross_margin = medians["gross_margin"]
    st.session_state.m_operating_margin = medians["operating_margin"]
    st.session_state.m_net_margin = medians["net_margin"]
    st.session_state.m_roe = medians["roe"]
    st.session_state.m_roa = medians["roa"]
    st.session_state.m_roce = medians["roce"]
    st.session_state.m_current_ratio = medians["current_ratio"]
    st.session_state.m_quick_ratio = medians["quick_ratio"]
    st.session_state.m_cash_ratio = medians["cash_ratio"]
    st.session_state.m_debt_to_equity = medians["debt_to_equity"]
    st.session_state.m_debt_ratio = medians["debt_ratio"]
    st.session_state.m_interest_coverage = medians["interest_coverage"]
    st.session_state.m_asset_turnover = medians["asset_turnover"]
    st.session_state.m_inventory_turnover = medians["inventory_turnover"]
    st.session_state.m_receivables_turnover = medians["receivables_turnover"]
    
    st.session_state.m_revenue_growth = medians["revenue_growth"]
    st.session_state.m_net_income_growth = medians["net_income_growth"]
    st.session_state.m_ocf_growth = medians["ocf_growth"]
    
    # Raw figures session state
    raws = compute_raw_figures_from_medians(medians)
    st.session_state.m_raw_revenue = raws["revenue"]
    st.session_state.m_raw_cogs = raws["cogs"]
    st.session_state.m_raw_opex = raws["opex"]
    st.session_state.m_raw_cash = raws["cash"]
    st.session_state.m_raw_receivables = raws["receivables"]
    st.session_state.m_raw_inventory = raws["inventory"]
    st.session_state.m_raw_other_ca = raws["other_current_assets"]
    st.session_state.m_raw_fixed_assets = raws["fixed_assets"]
    st.session_state.m_raw_payables = raws["payables"]
    st.session_state.m_raw_other_cl = raws["other_current_liabilities"]
    st.session_state.m_raw_debt = raws["debt"]
    st.session_state.m_raw_equity = raws["equity"]

    # Delete scaled keys to force re-initialization with new sector medians
    for k in ["m_raw_revenue_scaled", "m_raw_cogs_scaled", "m_raw_opex_scaled", 
              "m_raw_cash_scaled", "m_raw_receivables_scaled", "m_raw_inventory_scaled", 
              "m_raw_other_ca_scaled", "m_raw_fixed_assets_scaled", "m_raw_payables_scaled", 
              "m_raw_other_cl_scaled", "m_raw_debt_scaled", "m_raw_equity_scaled"]:
        if k in st.session_state:
            del st.session_state[k]


# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────
def render_sidebar() -> Dict:
    with st.sidebar:
        st.markdown(
            '<div style="font-family:\'Google Sans\', sans-serif;font-size:1.1rem;'
            'color:#00c4a7;margin-bottom:16px;">Global Settings</div>',
            unsafe_allow_html=True,
        )

        st.markdown("### AI Search")
        # Load from environment variables (or secrets fallback) to prevent exposure
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        if not gemini_key:
            try:
                gemini_key = st.secrets.get("GEMINI_API_KEY", "")
            except Exception:
                gemini_key = ""
            
        if gemini_key:
            num_keys = len([k.strip() for k in str(gemini_key).split(",") if k.strip()])
            if num_keys > 1:
                st.success(f"API Key pool loaded ({num_keys} keys active).")
            else:
                st.success("API Key loaded securely.")
        else:
            st.caption("AI search disabled (no GEMINI_API_KEY in .env).")

        st.session_state.gemini_api_key = gemini_key

        st.divider()
        use_cache = st.toggle("Use Data Cache", value=True)

        st.divider()
        if st.button("Clear All Cache", use_container_width=True, help="Deletes all cached financial data and stored benchmarks."):
            with st.spinner("Clearing cache..."):
                # 1. Clear Streamlit's internal RAM cache
                st.cache_data.clear()
                st.cache_resource.clear()
                
                # 2. Clear Persistent Files from disk
                import shutil
                from modules.utils import DATA_CACHE
                from modules.benchmark_store import BenchmarkStore
                
                if DATA_CACHE.exists():
                    shutil.rmtree(DATA_CACHE)
                    DATA_CACHE.mkdir(parents=True, exist_ok=True)
                
                b_dir = BenchmarkStore.BENCHMARKS_DIR
                if b_dir.exists():
                    shutil.rmtree(b_dir)
                    b_dir.mkdir(parents=True, exist_ok=True)
                
                st.success("Cache Cleared!")
                time.sleep(1)
                st.rerun()
    
    return {
        "gemini_api_key": gemini_key,
        "use_cache": use_cache,
    }


# ──────────────────────────────────────────────────────────────────────────────
# DATA PIPELINE (Sector Benchmarking)
# ──────────────────────────────────────────────────────────────────────────────
def run_pipeline(cfg: Dict):
    tickers = cfg["tickers"]
    fetcher = DataFetcher(use_cache=cfg["use_cache"], delay_seconds=0.3)
    parser = get_parser()
    ratio_engine = get_ratio_engine()
    outlier_engine = OutlierEngine(
        iqr_multiplier=cfg["iqr_mult"],
        zscore_threshold=cfg["z_thresh"],
    )
    store = get_benchmark_store()
    benchmark_core = BenchmarkCore()

    status = cfg.get("status_container") or st.empty()
    progress_slot = cfg.get("progress_container") or st.empty()
    progress = progress_slot.progress(0)

    # Step 1 – Fetch
    status.info("Fetching financial data from yfinance...")
    
    def cb(done, total_, ticker):
        pct = int(done / total_ * 40)
        progress.progress(pct)
        status.info(f"Fetching [{done}/{total_}] {ticker}...")

    raw_data = fetcher.fetch_all(tickers, progress_callback=cb)

    if not raw_data:
        status.error("No data fetched. Check tickers or network.")
        return

    # Step 2 – Market info
    status.info("Fetching market info...")
    market_info = {}
    for i, t in enumerate(tickers):
        market_info[t] = fetcher.fetch_market_info(t)
        progress.progress(40 + int(i / len(tickers) * 15))

    # Step 3 – Parse
    status.info("Parsing financial statements...")
    parsed = parser.parse_all(raw_data)
    progress.progress(60)

    # Step 4 – Ratios
    status.info("Computing financial ratios...")
    ratio_df = ratio_engine.compute_all(parsed, market_info, requested_tickers=tickers)
    growth_df = ratio_engine.compute_growth_metrics(parsed)
    progress.progress(75)

    if ratio_df.empty:
        st.warning("Ratio matrix is empty - insufficient data for selected tickers.")
        progress.empty(); status.empty()
        return

    failed_tickers = ratio_df.attrs.get("failed_tickers", [])

    # Step 5 – Outliers
    status.info("Detecting outliers...")
    if not growth_df.empty:
        merged = ratio_df.join(growth_df, how="left")
    else:
        merged = ratio_df
    merged.attrs["failed_tickers"] = failed_tickers
    merged.attrs["requested_tickers"] = tickers

    outlier_df = outlier_engine.detect(merged)
    anomaly_scores = outlier_engine.detect_multivariate(merged, contamination=cfg["contamination"])
    progress.progress(85)

    # Step 6 – Benchmark Core Pipeline (Replaces ScoringEngine)
    status.info("Running Benchmark Pipeline...")
    benchmark_result = benchmark_core.run(merged, outlier_df)
    
    # Save the peer stats to the store
    store.save(cfg["chosen"], benchmark_result.peer_stats_df, merged)
    progress.progress(100)

    # Store in session state
    st.session_state.parsed_data = parsed
    st.session_state.market_info = market_info
    st.session_state.selected_sector = cfg["chosen"]
    st.session_state.requested_tickers = tickers
    st.session_state.failed_tickers = failed_tickers
    st.session_state.tickers_used = list(ratio_df.index)
    st.session_state.growth_df = growth_df
    st.session_state.anomaly_scores = anomaly_scores
    st.session_state.benchmark_result = benchmark_result
    st.session_state.client_result = None # Clear client result

    status.success(f"Benchmark generation complete — {len(ratio_df)}/{len(tickers)} companies processed.")
    time.sleep(1)
    progress.empty()
    status.empty()
    st.rerun()
    
# ──────────────────────────────────────────────────────────────────────────────
# DATA PIPELINE (Client Ingestion)
# ──────────────────────────────────────────────────────────────────────────────
def run_client_pipeline(cfg: Dict):
    status = cfg.get("status_container") or st.empty()
    if not cfg["client_file"] or not cfg["comp_sector"]:
        status.error("Please provide a CSV file and select a sector.")
        return
        
    try:
        status.info("Processing standard client CSV...")
        client_df = pd.read_csv(cfg["client_file"])
        if client_df.empty:
            status.error("Uploaded CSV is empty.")
            return
            
        client_ratios = client_df.iloc[0].to_dict()
        client_name = "Client"
        for possible_key in ["ticker", "Company Name", "company_name", "Company", "company", "Name", "name"]:
            if possible_key in client_ratios:
                client_name = str(client_ratios.pop(possible_key))
                break
        
        store = get_benchmark_store()
        comparator = ClientComparator(store)
        
        client_result = comparator.compare_client(client_ratios, cfg["comp_sector"], client_name)
        
        # Capture normalized client name from result
        if client_result.clean_matrix is not None and not client_result.clean_matrix.empty:
            client_name = str(client_result.clean_matrix.index[0])
        
        # Calculate client anomaly score dynamically using Isolation Forest
        try:
            peer_stats_df, clean_matrix, _ = store.load(cfg["comp_sector"]) or (None, None, None)
            if clean_matrix is not None and not clean_matrix.empty:
                # Use the normalized client row from client_result
                client_row = client_result.clean_matrix.iloc[0]
                # Combine clean_matrix and client row
                combined_matrix = pd.concat([clean_matrix, pd.DataFrame([client_row])])
                # Recalculate anomaly scores including the client
                from modules.outlier_engine import OutlierEngine
                outlier_engine = OutlierEngine()
                anomaly_scores = outlier_engine.detect_multivariate(combined_matrix, contamination=cfg.get("contamination", 0.1))
                st.session_state.anomaly_scores = anomaly_scores
            else:
                st.session_state.anomaly_scores = None
        except Exception as ex:
            logger.warning("Failed to compute client anomaly score: %s", ex)
            st.session_state.anomaly_scores = None
            
        # Obtain normalized client ratios from client_result clean_matrix
        norm_ratios = {}
        if client_result.clean_matrix is not None and not client_result.clean_matrix.empty:
            norm_ratios = client_result.clean_matrix.iloc[0].to_dict()
        else:
            for k, v in client_ratios.items():
                norm_k = comparator._normalize_ratio_name(k)
                norm_ratios[norm_k] = v

        st.session_state.client_result = client_result
        
        # Populate tally/manual session keys to unlock Client Comparison tab for standard CSV client uploads
        st.session_state.tally_client_ratios    = norm_ratios
        st.session_state.tally_client_name      = client_name
        st.session_state.tally_benchmark_result = client_result
        st.session_state.tally_trial_balance    = pd.DataFrame([{"Particulars": k, "Type": "Direct Ratio Input", "Value": v} for k, v in norm_ratios.items() if k != "ticker"])
        st.session_state.manual_mode            = True
        st.session_state.manual_input_method    = "Direct Ratios"
        
        # Reset AI Chat Session
        st.session_state.ai_chat_session        = None
        st.session_state.ai_chat_history        = []
        st.session_state.ai_chat_active_client  = client_name
        
        status.success("Client comparison complete!")
        time.sleep(1)
        status.empty()
    except Exception as e:
        status.error(f"Error processing client data: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# DATA PIPELINE (Tally)
# ──────────────────────────────────────────────────────────────────────────────
def run_tally_pipeline(cfg: Dict):
    """Process uploaded TallySync CSVs, compute Trial Balance, and run
    through ClientComparator for full scorecard + composite output."""
    jv_file     = cfg.get("tally_jv_file")
    ledger_file = cfg.get("tally_ledger_file")
    sector      = cfg.get("tally_sector")

    status = cfg.get("status_container") or st.empty()
    progress_slot = cfg.get("progress_container") or st.empty()

    if jv_file is None or ledger_file is None:
        status.error("Please upload both the Journal CSV and the Ledger Master CSV.")
        return
    if sector is None:
        status.error("Please build a sector benchmark first, then select one.")
        return

    import tempfile, os
    jv_temp = None
    ledger_temp = None
    progress = progress_slot.progress(0)

    try:
        # Save uploaded files to temp paths
        status.info("Saving uploaded files...")
        with tempfile.NamedTemporaryFile(delete=False, suffix="_jv.csv") as f_jv:
            f_jv.write(jv_file.read())
            jv_temp = f_jv.name
        with tempfile.NamedTemporaryFile(delete=False, suffix="_ledger.csv") as f_ld:
            f_ld.write(ledger_file.read())
            ledger_temp = f_ld.name
        progress.progress(10)

        # Step 1: TallyBridge — compute ratios
        status.info("Processing journal entries... (this may take a moment for large files)")
        bridge = TallyBridge(jv_temp, ledger_temp)
        ratios = bridge.compute_ratios()
        progress.progress(50)

        # Step 2: TallyBridge — compute trial balance
        status.info("Generating trial balance...")
        trial_balance_df = bridge.compute_trial_balance()
        progress.progress(65)

        # Step 3: ClientComparator — run full benchmark pipeline
        status.info("Running benchmark comparison against stored peers...")
        client_name = cfg.get("tally_client_name", "Client")
        store = get_benchmark_store()
        comparator = ClientComparator(store)
        tally_result = comparator.compare_client(ratios, sector, client_name)
        progress.progress(90)

        # Calculate client anomaly score dynamically using Isolation Forest
        try:
            peer_stats_df, clean_matrix, _ = store.load(sector) or (None, None, None)
            if clean_matrix is not None and not clean_matrix.empty:
                # Use the normalized client row from tally_result
                client_row = tally_result.clean_matrix.iloc[0]
                # Combine clean_matrix and client row
                combined_matrix = pd.concat([clean_matrix, pd.DataFrame([client_row])])
                # Recalculate anomaly scores including the client
                from modules.outlier_engine import OutlierEngine
                outlier_engine = OutlierEngine()
                anomaly_scores = outlier_engine.detect_multivariate(combined_matrix, contamination=cfg.get("contamination", 0.1))
                st.session_state.anomaly_scores = anomaly_scores
            else:
                st.session_state.anomaly_scores = None
        except Exception as ex:
            logger.warning("Failed to compute client anomaly score: %s", ex)
            st.session_state.anomaly_scores = None

        # Store everything in session state
        st.session_state.tally_client_ratios    = ratios
        st.session_state.tally_client_name      = client_name
        st.session_state.tally_trial_balance    = trial_balance_df
        st.session_state.tally_benchmark_result = tally_result
        st.session_state.manual_mode            = False
        
        # Reset AI Diagnostic Session
        st.session_state.ai_chat_session        = None
        st.session_state.ai_chat_history        = []
        st.session_state.ai_chat_active_client  = client_name
        
        progress.progress(100)

        status.success(f"Tally data processed! {len(ratios)} ratios computed, benchmark comparison complete.")
        time.sleep(1)

    except Exception as e:
        status.error(f"Tally Processing Error: {e}")
        logger.error("Tally pipeline error: %s", e, exc_info=True)
    finally:
        # Clean up temp files
        for p in [jv_temp, ledger_temp]:
            if p:
                try:
                    os.unlink(p)
                except Exception:
                    pass
        progress.empty()
        status.empty()
        st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# DATA PIPELINE (Manual Entry)
# ──────────────────────────────────────────────────────────────────────────────
def run_manual_pipeline(cfg: Dict):
    """Process manual entries, compute ratios, and run through ClientComparator."""
    status = cfg.get("status_container") or st.empty()
    sector = cfg.get("manual_sector")
    client_name = cfg.get("manual_client_name", "Client")
    input_method = cfg.get("manual_input_method")
    
    if sector is None:
        status.error("Please select a target sector benchmark first.")
        return

    try:
        status.info("Processing manual entries...")
        ratios = {}
        trial_balance_df = None
        
        if input_method == "Raw Financial Figures":
            # Extract raw inputs from config/session state
            revenue = st.session_state.get("m_raw_revenue", 0.0)
            cogs = st.session_state.get("m_raw_cogs", 0.0)
            opex = st.session_state.get("m_raw_opex", 0.0)
            cash = st.session_state.get("m_raw_cash", 0.0)
            receivables = st.session_state.get("m_raw_receivables", 0.0)
            inventory = st.session_state.get("m_raw_inventory", 0.0)
            other_ca = st.session_state.get("m_raw_other_ca", 0.0)
            fixed_assets = st.session_state.get("m_raw_fixed_assets", 0.0)
            payables = st.session_state.get("m_raw_payables", 0.0)
            other_cl = st.session_state.get("m_raw_other_cl", 0.0)
            debt = st.session_state.get("m_raw_debt", 0.0)
            equity = st.session_state.get("m_raw_equity", 0.0)
            
            # Compute aggregates
            current_assets = cash + receivables + inventory + other_ca
            current_liab = payables + other_cl
            total_assets = current_assets + fixed_assets
            total_liab = current_liab + debt
            gross_profit = revenue - cogs
            ebit = revenue - cogs - opex
            net_income = ebit
            capital_employed = total_assets - current_liab
            
            sd = safe_divide
            
            # Compute ratios using standard formulas
            ratios = {
                "gross_margin": sd(gross_profit, revenue) * 100,
                "operating_margin": sd(ebit, revenue) * 100,
                "net_margin": sd(net_income, revenue) * 100,
                "roa": sd(net_income, total_assets) * 100,
                "roe": sd(net_income, equity) * 100,
                "roce": sd(ebit, capital_employed) * 100,
                "current_ratio": sd(current_assets, current_liab),
                "quick_ratio": sd(current_assets - inventory, current_liab),
                "cash_ratio": sd(cash, current_liab),
                "debt_to_equity": sd(debt, equity),
                "debt_ratio": sd(total_liab, total_assets),
                "asset_turnover": sd(revenue, total_assets),
                "inventory_turnover": sd(cogs, inventory),
                "receivables_turnover": sd(revenue, receivables),
                "interest_coverage": np.nan,
                "operating_cf_ratio": np.nan,
                "fcf_margin": np.nan,
                "cash_conversion": np.nan,
                # Raw sizing values
                "total_revenue": revenue,
                "ebitda": ebit,
                "total_assets": total_assets,
                "total_debt": debt,
                "total_equity": equity,
            }
            
            # Generate a structured summary dataframe for raw inputs
            trial_balance_df = pd.DataFrame([
                {"Particulars": "Total Revenue (Sales)", "Type": "Income", "Value": revenue},
                {"Particulars": "Cost of Goods Sold (COGS)", "Type": "Expense", "Value": cogs},
                {"Particulars": "Operating Expenses (Opex)", "Type": "Expense", "Value": opex},
                {"Particulars": "Gross Profit", "Type": "Calculated Asset/Equity Effect", "Value": gross_profit},
                {"Particulars": "EBIT (Operating Profit)", "Type": "Calculated Asset/Equity Effect", "Value": ebit},
                {"Particulars": "Cash & Bank Balance", "Type": "Current Asset", "Value": cash},
                {"Particulars": "Accounts Receivable (Sundry Debtors)", "Type": "Current Asset", "Value": receivables},
                {"Particulars": "Inventory (Stock-in-Hand)", "Type": "Current Asset", "Value": inventory},
                {"Particulars": "Other Current Assets", "Type": "Current Asset", "Value": other_ca},
                {"Particulars": "Fixed Assets & Investments", "Type": "Non-Current Asset", "Value": fixed_assets},
                {"Particulars": "Accounts Payable (Sundry Creditors)", "Type": "Current Liability", "Value": payables},
                {"Particulars": "Other Current Liabilities", "Type": "Current Liability", "Value": other_cl},
                {"Particulars": "Total Debt (Loans/Borrowings)", "Type": "Non-Current Liability", "Value": debt},
                {"Particulars": "Total Equity (Capital + Reserves)", "Type": "Equity", "Value": equity},
            ])
            
        else:
            # Direct Ratios input method
            ratios = {
                "gross_margin": st.session_state.get("m_gross_margin", 0.0),
                "operating_margin": st.session_state.get("m_operating_margin", 0.0),
                "net_margin": st.session_state.get("m_net_margin", 0.0),
                "roe": st.session_state.get("m_roe", 0.0),
                "roa": st.session_state.get("m_roa", 0.0),
                "roce": st.session_state.get("m_roce", 0.0),
                "current_ratio": st.session_state.get("m_current_ratio", 0.0),
                "quick_ratio": st.session_state.get("m_quick_ratio", 0.0),
                "cash_ratio": st.session_state.get("m_cash_ratio", 0.0),
                "debt_to_equity": st.session_state.get("m_debt_to_equity", 0.0),
                "debt_ratio": st.session_state.get("m_debt_ratio", 0.0),
                "interest_coverage": st.session_state.get("m_interest_coverage", np.nan),
                "asset_turnover": st.session_state.get("m_asset_turnover", 0.0),
                "inventory_turnover": st.session_state.get("m_inventory_turnover", 0.0),
                "receivables_turnover": st.session_state.get("m_receivables_turnover", 0.0),
            }
            
            # Include Growth Metrics if toggled
            if cfg.get("manual_include_growth", False):
                ratios["revenue_growth"] = st.session_state.get("m_revenue_growth", 0.0)
                ratios["net_income_growth"] = st.session_state.get("m_net_income_growth", 0.0)
                ratios["ocf_growth"] = st.session_state.get("m_ocf_growth", 0.0)
            else:
                ratios["revenue_growth"] = np.nan
                ratios["net_income_growth"] = np.nan
                ratios["ocf_growth"] = np.nan
                
            ratios.update({
                "operating_cf_ratio": np.nan,
                "fcf_margin": np.nan,
                "cash_conversion": np.nan,
                # Size values (can default to standard numbers if not provided)
                "total_revenue": 10000000.0,
                "ebitda": 10000000.0 * (st.session_state.get("m_operating_margin", 0.0) / 100),
                "total_assets": 10000000.0 / st.session_state.get("m_asset_turnover", 1.0),
                "total_debt": 0.0,
                "total_equity": 10000000.0,
            })
            
            # Generate a summary dataframe of inputted ratios
            ratio_labels = {
                "gross_margin": "Gross Margin (%)",
                "operating_margin": "Operating Margin (%)",
                "net_margin": "Net Margin (%)",
                "roe": "ROE (%)",
                "roa": "ROA (%)",
                "roce": "ROCE (%)",
                "current_ratio": "Current Ratio",
                "quick_ratio": "Quick Ratio",
                "cash_ratio": "Cash Ratio",
                "debt_to_equity": "Debt to Equity",
                "debt_ratio": "Debt Ratio",
                "asset_turnover": "Asset Turnover",
                "inventory_turnover": "Inventory Turnover",
                "receivables_turnover": "Receivables Turnover",
            }
            if cfg.get("manual_include_growth", False):
                ratio_labels.update({
                    "revenue_growth": "Revenue Growth (%)",
                    "net_income_growth": "Net Income Growth (%)",
                    "ocf_growth": "OCF Growth (%)"
                })
            
            records = [{"Particulars": label, "Type": "Direct Ratio Input", "Value": ratios[r_key]} for r_key, label in ratio_labels.items() if r_key in ratios]
            trial_balance_df = pd.DataFrame(records)
            
        # Run standard comparator
        store = get_benchmark_store()
        comparator = ClientComparator(store)
        manual_result = comparator.compare_client(ratios, sector, client_name)
        
        # Calculate client anomaly score dynamically using Isolation Forest
        try:
            peer_stats_df, clean_matrix, _ = store.load(sector) or (None, None, None)
            if clean_matrix is not None and not clean_matrix.empty:
                # Use the normalized client row from manual_result
                client_row = manual_result.clean_matrix.iloc[0]
                # Combine clean_matrix and client row
                combined_matrix = pd.concat([clean_matrix, pd.DataFrame([client_row])])
                # Recalculate anomaly scores including the client
                from modules.outlier_engine import OutlierEngine
                outlier_engine = OutlierEngine()
                anomaly_scores = outlier_engine.detect_multivariate(combined_matrix, contamination=cfg.get("contamination", 0.1))
                st.session_state.anomaly_scores = anomaly_scores
            else:
                st.session_state.anomaly_scores = None
        except Exception as ex:
            logger.warning("Failed to compute client anomaly score: %s", ex)
            st.session_state.anomaly_scores = None
        
        # Save standard session state keys
        st.session_state.tally_client_ratios    = ratios
        st.session_state.tally_client_name      = client_name
        st.session_state.tally_trial_balance    = trial_balance_df
        st.session_state.tally_benchmark_result = manual_result
        st.session_state.manual_mode            = True
        st.session_state.manual_input_method    = input_method
        
        # Reset AI Diagnostic Session
        st.session_state.ai_chat_session        = None
        st.session_state.ai_chat_history        = []
        st.session_state.ai_chat_active_client  = client_name
        
        status.success("Private comparison complete!")
        time.sleep(1)
        
    except Exception as e:
        status.error(f"Manual Entry Processing Error: {e}")
        logger.error("Manual entry pipeline error: %s", e, exc_info=True)
    finally:
        status.empty()
        st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# PAGE RENDERERS
# ──────────────────────────────────────────────────────────────────────────────
def page_home(global_cfg: Dict) -> Dict:
    st.markdown(
        """
        <div class="banner" style="background: linear-gradient(135deg, #001f1e 0%, #002623 50%, #001f1e 100%); border: 1px solid #1a3a37; border-radius: 10px; padding: 20px 28px; margin-bottom: 24px; display: flex; align-items: center; gap: 16px;">
            <div>
                <div style="font-family: 'Google Sans', sans-serif; font-size: 1.8rem; font-weight: 600; color: #00c4a7; line-height: 1.2;">FinMetrics Suite</div>
                <div style="font-size: 0.85rem; color: #7ab8b2; margin-top: 4px;">
                    Automated Ratio-First Financial Analysis
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    status_container = st.empty()
    progress_container = st.empty()
    
    sl = get_sector_loader()
    store = get_benchmark_store()
    
    # ── Section 1: Define Scope ──────────────────────────────────────────
    st.markdown("### 1. Define Scope")
    c1, c2 = st.columns([1, 2])
    
    with c1:
        analysis_type = st.radio("Analysis Unit", ["Sector", "Industry", "AI Search"], horizontal=True, help="Choose whether to build the peer benchmark based on a broad Sector classification or a specific Industry group.")
    
    with c2:
        if analysis_type == "AI Search":
            ai_query = st.text_input("Describe the Industry", placeholder="e.g. Electric Vehicle Infrastructure", help="Enter keywords describing a target market or sector niche. Gemini will dynamically search and retrieve matching stock tickers.")
            ai_market = st.text_input("Market / Country", value="NSE India", placeholder="e.g. NSE India, NYSE USA, LSE UK", help="The target stock exchange or market scope for AI ticker discovery (e.g. NSE India, NYSE USA, LSE UK).")
            
            if st.button("Discover Tickers", use_container_width=True, help="Query the Gemini API to search and dynamically compile relevant traded stock tickers."):
                gemini_key = global_cfg.get("gemini_api_key")
                if not gemini_key:
                    st.error("Please enter your Gemini API Key in the sidebar.")
                elif not ai_query:
                    st.error("Please enter an industry to search.")
                else:
                    with st.spinner(f"Gemini is analyzing the {ai_market} market..."):
                        try:
                            from modules.ai_handler import AIHandler
                            handler = AIHandler(gemini_key)
                            found = handler.search_industry_tickers(ai_query, ai_market)
                            if found:
                                st.session_state.ai_tickers = found
                                st.success(f"Found {len(found)} relevant tickers!")
                            else:
                                st.warning("No tickers found for this industry.")
                        except Exception as e:
                            st.error(f"AI Search Failed: {e}")
            chosen = f"AI: {ai_query}" if ai_query else "AI Search"
            tickers = st.session_state.ai_tickers
        elif analysis_type == "Sector":
            options = sl.get_sectors()
            chosen = st.selectbox("Select Sector", options, index=0, help="Select the Sector peer group database to load or build a benchmark scorecard for.")
            tickers = sl.get_companies_by_sector(chosen)
        else:
            options = sl.get_industries()
            chosen = st.selectbox("Select Industry", options, index=0, help="Select the Industry peer group database to load or build a benchmark scorecard for.")
            tickers = sl.get_companies_by_industry(chosen)

    with st.expander(f"Ticker Override ({len(tickers)} companies selected)", expanded=False):
        default_val = "\n".join(tickers)
        custom = st.text_area("Custom Tickers (one per line, .NS suffix)", value=default_val, height=160)
        tickers = [t.strip().upper() for t in custom.split("\n") if t.strip()]

    # ── Section 2: Calibration ───────────────────────────────────────────
    if "calib_iqr" not in st.session_state:
        st.session_state.calib_iqr = 1.5
    if "calib_z" not in st.session_state:
        st.session_state.calib_z = 3.5
    if "calib_contam" not in st.session_state:
        st.session_state.calib_contam = 10

    st.markdown("### 2. Calibration (Advanced)")
    with st.expander("Outlier & Model Settings", expanded=False):
        c_btn, _ = st.columns([1, 4])
        if c_btn.button("Reset Defaults", help="Restore recommended default settings"):
            st.session_state.calib_iqr = 1.5
            st.session_state.calib_z = 3.5
            st.session_state.calib_contam = 10
            st.rerun()

        c3, c4, c5 = st.columns(3)
        iqr_mult = c3.slider(
            "IQR Multiplier", 
            1.0, 3.0, 
            key="calib_iqr", 
            step=0.1,
            help="Multiplier for the Interquartile Range (IQR) to identify outliers. Data points beyond [Q1 - Multiplier * IQR] or [Q3 + Multiplier * IQR] are classified as outliers. Default is 1.5."
        )
        z_thresh = c4.slider(
            "Z-Score Threshold", 
            2.0, 5.0, 
            key="calib_z", 
            step=0.1,
            help="Standard deviations from the mean to identify outliers. Observations exceeding this threshold are flagged as extreme anomalies. Default is 3.5."
        )
        contamination = c5.slider(
            "Isolation Forest (%)", 
            5, 30, 
            key="calib_contam", 
            step=5,
            help="Estimated proportion of anomalous data in the dataset. Used to calibrate the contamination parameter of the machine learning isolation forest algorithm. Default is 10%."
        ) / 100

    # ── Section 3: Build Benchmark ───────────────────────────────────────
    st.markdown("### 3. Build Benchmark")
    run = st.button("Build Sector Benchmark", type="primary", use_container_width=True)
    
    st.divider()

    # ── Section 4: Client Comparison ─────────────────────────────────────
    st.markdown("### 4. Client Comparison")
    
    comp_sector = None
    client_file = None
    run_client = False
    
    tab_tally, tab_manual = st.tabs(["TallySync Upload", "Private Manual Entry"])
    
    with tab_tally:
        tally_available = store.list_available()
        if tally_available:
            c8, c9 = st.columns(2)
            tally_jv_file = c8.file_uploader(
                "Journal CSV (JV)", 
                type=["csv"], 
                key="tally_jv",
                help="Upload the Tally Journal Vouchers CSV export. This file must contain transaction-level journal entries with columns like Date, Particulars, Vch Type, Vch No, Debit, and Credit."
            )
            tally_ledger_file = c9.file_uploader(
                "Ledger Master CSV", 
                type=["csv"], 
                key="tally_ledger",
                help="Upload the Tally Ledger Master CSV export. This maps specific account ledger names to their respective corporate Tally Accounting Groups (e.g. Sales Accounts, Purchase Accounts, Sundry Debtors, Sundry Creditors)."
            )
            c10, c11 = st.columns(2)
            tally_client_name = c10.text_input(
                "Client Name", 
                value="PRIME RETAIL VENTURES",
                help="Specify the name or identifier of the client company. This name will appear on all reports, benchmarking scorecards, and AI diagnostic analyses."
            )
            tally_sector = c11.selectbox(
                "Benchmark against sector:", 
                tally_available, 
                key="tally_sector",
                help="Select the baseline industry sector to compare the client's performance against. Peer benchmarks must be generated first."
            )
            run_tally = st.button("Process Tally Data", type="primary", use_container_width=True)
        else:
            tally_jv_file = None
            tally_ledger_file = None
            tally_client_name = "Client"
            tally_sector = None
            run_tally = False
            st.info("Build a benchmark first to generate and store peer groups for comparison.")

    with tab_manual:
        manual_available = store.list_available()
        if manual_available:
            # Setup initial state if not present
            if "manual_sector" not in st.session_state:
                st.session_state.manual_sector = manual_available[0]
                update_manual_defaults()

            c_man1, c_man2 = st.columns(2)
            manual_sector = c_man1.selectbox(
                "Benchmark against sector:",
                manual_available,
                key="manual_sector",
                on_change=update_manual_defaults,
                help="Select the baseline industry sector to compare the client's performance against. Peer benchmarks must be generated first."
            )
            manual_input_method = c_man2.radio(
                "Input Method:",
                ["Raw Financial Figures", "Direct Ratios"],
                key="manual_input_method",
                on_change=update_manual_defaults,
                horizontal=True,
                help="Choose whether to enter raw balance sheet and income statement figures (which will automatically calculate ratios) or to input completed direct financial ratios manually."
            )

            manual_client_name = st.text_input(
                "Client Name",
                value="Private Client Co.",
                key="manual_client_name",
                help="Specify the name or identifier of the client company. This name will appear on all reports, benchmarking scorecards, and AI diagnostic analyses."
            )

            st.divider()

            manual_include_growth = False
            
            if manual_input_method == "Raw Financial Figures":
                c_title, c_denom = st.columns([2, 2])
                c_title.markdown(
                    "<div style='font-family:\"Google Sans\";font-size:1.1rem;color:#00c4a7;font-weight:600;margin-top:6px;'>Enter Raw Financial Figures</div>",
                    unsafe_allow_html=True
                )
                denom_unit = c_denom.selectbox(
                    "Input Denomination Unit:",
                    ["Absolute (Actuals)", "In Lakhs (₹ 100,000)", "In Crores (₹ 10,000,000)"],
                    key="manual_denomination_unit",
                    help="Select the unit denomination for raw financial entries. Inputs will be entered and displayed in this denomination, but scaled up internally to align with peer benchmarks."
                )
                
                # Setup prev_denom_unit and sync block
                if "prev_denom_unit" not in st.session_state:
                    st.session_state.prev_denom_unit = "Absolute (Actuals)"
                
                # Identify conversion factor
                factor = 1.0
                if denom_unit == "In Lakhs (₹ 100,000)":
                    factor = 100000.0
                elif denom_unit == "In Crores (₹ 10,000,000)":
                    factor = 10000000.0
                
                # If denomination changed, delete scaled keys to force re-initialization
                if denom_unit != st.session_state.prev_denom_unit:
                    st.session_state.prev_denom_unit = denom_unit
                    for k in ["m_raw_revenue_scaled", "m_raw_cogs_scaled", "m_raw_opex_scaled", 
                              "m_raw_cash_scaled", "m_raw_receivables_scaled", "m_raw_inventory_scaled", 
                              "m_raw_other_ca_scaled", "m_raw_fixed_assets_scaled", "m_raw_payables_scaled", 
                              "m_raw_other_cl_scaled", "m_raw_debt_scaled", "m_raw_equity_scaled"]:
                        if k in st.session_state:
                            del st.session_state[k]
                            
                st.divider()
                
                col_inc, col_bs = st.columns(2)
                
                with col_inc:
                    st.markdown(
                        "<div style='font-family:\"Google Sans\";font-size:0.95rem;color:#7ab8b2;font-weight:500;border-bottom:1px solid #1a3a37;padding-bottom:4px;margin-bottom:12px;'>Income Statement (Annualized)</div>",
                        unsafe_allow_html=True
                    )
                    st.number_input("Total Revenue (Sales)", min_value=0.0, value=st.session_state.get("m_raw_revenue", 0.0) / factor, key="m_raw_revenue_scaled", format="%.2f", help="Total sales revenue generated from core business operations during the financial year (before deducting any costs or taxes).")
                    st.number_input("Cost of Goods Sold (COGS)", min_value=0.0, value=st.session_state.get("m_raw_cogs", 0.0) / factor, key="m_raw_cogs_scaled", format="%.2f", help="Direct costs attributable to the production or purchase of goods sold (materials, direct labor, and manufacturing overhead).")
                    st.number_input("Operating Expenses (Opex)", min_value=0.0, value=st.session_state.get("m_raw_opex", 0.0) / factor, key="m_raw_opex_scaled", format="%.2f", help="Indirect expenses incurred to run daily operations (rent, office salaries, utility bills, administrative overhead, marketing).")
                    
                with col_bs:
                    st.markdown(
                        "<div style='font-family:\"Google Sans\";font-size:0.95rem;color:#7ab8b2;font-weight:500;border-bottom:1px solid #1a3a37;padding-bottom:4px;margin-bottom:12px;'>Balance Sheet</div>",
                        unsafe_allow_html=True
                    )
                    
                    bs_asset, bs_liab = st.columns(2)
                    with bs_asset:
                        st.markdown("<span style='font-size:0.85rem;color:#7ab8b2;font-weight:500;'>Assets</span>", unsafe_allow_html=True)
                        st.number_input("Cash & Bank Balance", min_value=0.0, value=st.session_state.get("m_raw_cash", 0.0) / factor, key="m_raw_cash_scaled", format="%.2f", help="Highly liquid funds available in bank checking/savings accounts, petty cash, or cash equivalents.")
                        st.number_input("Accounts Receivable", min_value=0.0, value=st.session_state.get("m_raw_receivables", 0.0) / factor, key="m_raw_receivables_scaled", format="%.2f", help="Outstanding invoice amounts owed to your company by customers for goods or services delivered on credit.")
                        st.number_input("Inventory (Stock-in-Hand)", min_value=0.0, value=st.session_state.get("m_raw_inventory", 0.0) / factor, key="m_raw_inventory_scaled", format="%.2f", help="Total cost value of raw materials, work-in-progress, and finished goods currently held in stock.")
                        st.number_input("Other Current Assets", min_value=0.0, value=st.session_state.get("m_raw_other_ca", 0.0) / factor, key="m_raw_other_ca_scaled", format="%.2f", help="Short-term assets due within 12 months, excluding cash, receivables, and stock (e.g. prepaid expenses, advance taxes, supplier deposits).")
                        st.number_input("Fixed Assets & Investments", min_value=0.0, value=st.session_state.get("m_raw_fixed_assets", 0.0) / factor, key="m_raw_fixed_assets_scaled", format="%.2f", help="Long-term assets held for business use (land, buildings, machinery, vehicles, computers) and long-term financial holdings.")
                    
                    with bs_liab:
                        st.markdown("<span style='font-size:0.85rem;color:#7ab8b2;font-weight:500;'>Liabilities & Equity</span>", unsafe_allow_html=True)
                        st.number_input("Accounts Payable", min_value=0.0, value=st.session_state.get("m_raw_payables", 0.0) / factor, key="m_raw_payables_scaled", format="%.2f", help="Outstanding invoice amounts owed by your company to suppliers for goods or services purchased on credit.")
                        st.number_input("Other Current Liabilities", min_value=0.0, value=st.session_state.get("m_raw_other_cl", 0.0) / factor, key="m_raw_other_cl_scaled", format="%.2f", help="Short-term obligations due within 12 months, excluding payables (e.g. accrued salaries, duties and taxes payable, short-term provisions).")
                        st.number_input("Total Debt (Loans)", min_value=0.0, value=st.session_state.get("m_raw_debt", 0.0) / factor, key="m_raw_debt_scaled", format="%.2f", help="Total sum of all short-term and long-term interest-bearing loans, credit lines, and bank borrowings.")
                        st.number_input("Total Equity", min_value=0.0, value=st.session_state.get("m_raw_equity", 0.0) / factor, key="m_raw_equity_scaled", format="%.2f", help="Total owner/partner capital plus accumulated reserves and surplus (represents the net worth of the company).")
                        
                        # Sync scaled inputs back to absolute session state immediately so calculations below are accurate
                        st.session_state.m_raw_revenue = st.session_state.get("m_raw_revenue_scaled", 0.0) * factor
                        st.session_state.m_raw_cogs = st.session_state.get("m_raw_cogs_scaled", 0.0) * factor
                        st.session_state.m_raw_opex = st.session_state.get("m_raw_opex_scaled", 0.0) * factor
                        st.session_state.m_raw_cash = st.session_state.get("m_raw_cash_scaled", 0.0) * factor
                        st.session_state.m_raw_receivables = st.session_state.get("m_raw_receivables_scaled", 0.0) * factor
                        st.session_state.m_raw_inventory = st.session_state.get("m_raw_inventory_scaled", 0.0) * factor
                        st.session_state.m_raw_other_ca = st.session_state.get("m_raw_other_ca_scaled", 0.0) * factor
                        st.session_state.m_raw_fixed_assets = st.session_state.get("m_raw_fixed_assets_scaled", 0.0) * factor
                        st.session_state.m_raw_payables = st.session_state.get("m_raw_payables_scaled", 0.0) * factor
                        st.session_state.m_raw_other_cl = st.session_state.get("m_raw_other_cl_scaled", 0.0) * factor
                        st.session_state.m_raw_debt = st.session_state.get("m_raw_debt_scaled", 0.0) * factor
                        st.session_state.m_raw_equity = st.session_state.get("m_raw_equity_scaled", 0.0) * factor
                        
                        # Balance sheet integrity check
                        tot_assets = (st.session_state.get("m_raw_cash", 0.0) + 
                                      st.session_state.get("m_raw_receivables", 0.0) + 
                                      st.session_state.get("m_raw_inventory", 0.0) + 
                                      st.session_state.get("m_raw_other_ca", 0.0) + 
                                      st.session_state.get("m_raw_fixed_assets", 0.0))
                        tot_liab_eq = (st.session_state.get("m_raw_payables", 0.0) + 
                                       st.session_state.get("m_raw_other_cl", 0.0) + 
                                       st.session_state.get("m_raw_debt", 0.0) + 
                                       st.session_state.get("m_raw_equity", 0.0))
                        diff = abs(tot_assets - tot_liab_eq)
                        
                        if diff > 1.0:
                            st.warning(f"Balance Sheet is unbalanced by: {diff / factor:,.2f} (Assets: {tot_assets / factor:,.2f} | Liab+Eq: {tot_liab_eq / factor:,.2f})")
                        else:
                            st.success(f"Balance Sheet is balanced perfectly! ({tot_assets / factor:,.2f})")
            else:
                st.markdown(
                    "<div style='font-family:\"Google Sans\";font-size:1.1rem;color:#00c4a7;font-weight:600;margin-bottom:12px;'>Enter Direct Financial Ratios</div>",
                    unsafe_allow_html=True
                )
                
                col_r1, col_r2, col_r3 = st.columns(3)
                
                with col_r1:
                    st.markdown(
                        "<div style='font-family:\"Google Sans\";font-size:0.95rem;color:#7ab8b2;font-weight:500;border-bottom:1px solid #1a3a37;padding-bottom:4px;margin-bottom:12px;'>Profitability & Returns</div>",
                        unsafe_allow_html=True
                    )
                    st.number_input(
                        "Gross Margin (%)", 
                        value=st.session_state.get("m_gross_margin", 0.0), 
                        key="m_gross_margin", 
                        format="%.2f",
                        help="Gross Profit Margin. Formula: (Total Revenue - Cost of Goods Sold) / Total Revenue * 100. Measures the percentage of sales revenue remaining after deducting the direct cost of producing or purchasing goods sold."
                    )
                    st.number_input(
                        "Operating Margin (%)", 
                        value=st.session_state.get("m_operating_margin", 0.0), 
                        key="m_operating_margin", 
                        format="%.2f",
                        help="Operating Profit Margin. Formula: Operating Income (EBIT) / Total Revenue * 100. Measures the percentage of sales revenue remaining after deducting both direct costs and daily operating expenses (Opex)."
                    )
                    st.number_input(
                        "Net Margin (%)", 
                        value=st.session_state.get("m_net_margin", 0.0), 
                        key="m_net_margin", 
                        format="%.2f",
                        help="Net Profit Margin. Formula: Net Income / Total Revenue * 100. Represents the percentage of sales revenue that translates into bottom-line net profit after all expenses, interest, and taxes are paid."
                    )
                    st.number_input(
                        "ROE (%)", 
                        value=st.session_state.get("m_roe", 0.0), 
                        key="m_roe", 
                        format="%.2f",
                        help="Return on Equity. Formula: Net Income / Total Equity * 100. Measures a company's profitability and efficiency in generating profits relative to the amount of shareholder equity invested."
                    )
                    st.number_input(
                        "ROA (%)", 
                        value=st.session_state.get("m_roa", 0.0), 
                        key="m_roa", 
                        format="%.2f",
                        help="Return on Assets. Formula: Net Income / Total Assets * 100. Indicates how efficiently a company utilizes its total assets to generate net income."
                    )
                    st.number_input(
                        "ROCE (%)", 
                        value=st.session_state.get("m_roce", 0.0), 
                        key="m_roce", 
                        format="%.2f",
                        help="Return on Capital Employed. Formula: EBIT / (Total Assets - Current Liabilities) * 100. Evaluates a company's profitability and efficiency relative to the total capital actively employed in the business (equity plus long-term debt)."
                    )
                    
                with col_r2:
                    st.markdown(
                        "<div style='font-family:\"Google Sans\";font-size:0.95rem;color:#7ab8b2;font-weight:500;border-bottom:1px solid #1a3a37;padding-bottom:4px;margin-bottom:12px;'>Liquidity & Solvency</div>",
                        unsafe_allow_html=True
                    )
                    st.number_input(
                        "Current Ratio", 
                        min_value=0.0, 
                        value=st.session_state.get("m_current_ratio", 0.0), 
                        key="m_current_ratio", 
                        format="%.2f",
                        help="Current Ratio. Formula: Total Current Assets / Total Current Liabilities. Evaluates short-term liquidity by measuring the company's ability to cover its short-term obligations (due within 12 months) with its short-term assets."
                    )
                    st.number_input(
                        "Quick Ratio", 
                        min_value=0.0, 
                        value=st.session_state.get("m_quick_ratio", 0.0), 
                        key="m_quick_ratio", 
                        format="%.2f",
                        help="Quick Ratio (Acid-Test). Formula: (Cash & Bank + Accounts Receivable) / Total Current Liabilities. Assesses short-term liquidity using only highly liquid assets, excluding inventory and prepaid expenses which are harder to quickly convert to cash."
                    )
                    st.number_input(
                        "Cash Ratio", 
                        min_value=0.0, 
                        value=st.session_state.get("m_cash_ratio", 0.0), 
                        key="m_cash_ratio", 
                        format="%.2f",
                        help="Cash Ratio. Formula: Cash & Bank Balance / Total Current Liabilities. The most conservative liquidity metric, measuring the company's ability to immediately cover all current liabilities using only cash and cash equivalents."
                    )
                    st.number_input(
                        "Debt to Equity", 
                        min_value=0.0, 
                        value=st.session_state.get("m_debt_to_equity", 0.0), 
                        key="m_debt_to_equity", 
                        format="%.2f",
                        help="Debt to Equity Ratio. Formula: Total Debt / Total Equity. A leverage metric indicating the proportion of company financing that comes from debt/creditors versus owners/equity."
                    )
                    st.number_input(
                        "Debt Ratio", 
                        min_value=0.0, 
                        value=st.session_state.get("m_debt_ratio", 0.0), 
                        key="m_debt_ratio", 
                        format="%.2f",
                        help="Debt Ratio. Formula: Total Debt / Total Assets. Represents the proportion of a company's assets that are financed through debt instead of equity."
                    )
                    st.number_input(
                        "Interest Coverage", 
                        min_value=0.0, 
                        value=st.session_state.get("m_interest_coverage", np.nan), 
                        key="m_interest_coverage", 
                        format="%.2f",
                        help="Interest Coverage Ratio. Formula: Operating Income (EBIT) / Interest Expense. Measures a company's ability to pay interest on its outstanding debt from its operating profit."
                    )
                    
                with col_r3:
                    st.markdown(
                        "<div style='font-family:\"Google Sans\";font-size:0.95rem;color:#7ab8b2;font-weight:500;border-bottom:1px solid #1a3a37;padding-bottom:4px;margin-bottom:12px;'>Operations & Growth</div>",
                        unsafe_allow_html=True
                    )
                    st.number_input(
                        "Asset Turnover", 
                        min_value=0.0, 
                        value=st.session_state.get("m_asset_turnover", 0.0), 
                        key="m_asset_turnover", 
                        format="%.2f",
                        help="Asset Turnover Ratio. Formula: Total Revenue / Total Assets. Measures the efficiency with which a company uses its assets to generate revenue (sales volume relative to asset base)."
                    )
                    st.number_input(
                        "Inventory Turnover", 
                        min_value=0.0, 
                        value=st.session_state.get("m_inventory_turnover", 0.0), 
                        key="m_inventory_turnover", 
                        format="%.2f",
                        help="Inventory Turnover Ratio. Formula: Cost of Goods Sold (COGS) / Inventory (Stock-in-Hand). Measures how many times a company's inventory is sold and replaced over a given period."
                    )
                    st.number_input(
                        "Receivables Turnover", 
                        min_value=0.0, 
                        value=st.session_state.get("m_receivables_turnover", 0.0), 
                        key="m_receivables_turnover", 
                        format="%.2f",
                        help="Receivables Turnover Ratio. Formula: Total Revenue / Accounts Receivable. Measures the efficiency of the company's credit sales collection, showing how many times receivables are collected during the period."
                    )
                    
                    st.divider()
                    manual_include_growth = st.toggle("Include Growth Indicators", value=False, key="manual_include_growth")
                    if manual_include_growth:
                        st.number_input(
                            "Revenue Growth (%)", 
                            value=st.session_state.get("m_revenue_growth", 0.0), 
                            key="m_revenue_growth", 
                            format="%.2f",
                            help="Revenue Growth Rate. Formula: (Current Period Revenue - Prior Period Revenue) / Prior Period Revenue * 100. Year-on-year percentage change in total sales revenue."
                        )
                        st.number_input(
                            "Net Income Growth (%)", 
                            value=st.session_state.get("m_net_income_growth", 0.0), 
                            key="m_net_income_growth", 
                            format="%.2f",
                            help="Net Income Growth Rate. Formula: (Current Period Net Income - Prior Period Net Income) / Prior Period Net Income * 100. Year-on-year percentage change in bottom-line net profit."
                        )
                        st.number_input(
                            "OCF Growth (%)", 
                            value=st.session_state.get("m_ocf_growth", 0.0), 
                            key="m_ocf_growth", 
                            format="%.2f",
                            help="Operating Cash Flow (OCF) Growth Rate. Formula: (Current Period Operating Cash Flow - Prior Period Operating Cash Flow) / Prior Period Operating Cash Flow * 100. Year-on-year percentage change in cash flows generated from core operating activities."
                        )

            run_manual = st.button("Process Private Data", type="primary", key="run_man_btn", use_container_width=True)
        else:
            manual_sector = None
            manual_client_name = "Client"
            manual_input_method = "Raw Financial Figures"
            manual_include_growth = False
            run_manual = False
            st.info("Build a benchmark first to generate and store peer groups for comparison.")

    return {
        "chosen": chosen,
        "tickers": tickers,
        "iqr_mult": iqr_mult,
        "z_thresh": z_thresh,
        "contamination": contamination,
        "use_cache": global_cfg.get("use_cache", True),
        "run": run,
        "analysis_type": analysis_type,
        "comp_sector": comp_sector,
        "client_file": client_file,
        "run_client": run_client,
        "tally_jv_file": tally_jv_file,
        "tally_ledger_file": tally_ledger_file,
        "tally_client_name": tally_client_name,
        "tally_sector": tally_sector,
        "run_tally": run_tally,
        "manual_sector": manual_sector if manual_available else None,
        "manual_client_name": manual_client_name if manual_available else "Client",
        "manual_input_method": manual_input_method if manual_available else "Raw Financial Figures",
        "manual_include_growth": manual_include_growth,
        "run_manual": run_manual if manual_available else False,
        "status_container": status_container,
        "progress_container": progress_container,
    }


def page_scorecard(result: BenchmarkCoreResult):
    st.markdown("## Ratio Scorecard")
    st.caption("Primary evaluation matrix showing descriptive positions and percentile ranks based on the **latest quarterly reporting period**.")
    
    scorecard = result.ratio_scorecard_df
    
    total_ratios = len(scorecard)
    if total_ratios == 0:
        st.warning("No scorecard data available.")
        return
        
    above_count = len(scorecard[scorecard["position_label"] == "Above Benchmark"])
    at_count = len(scorecard[scorecard["position_label"] == "At Benchmark"])
    below_count = len(scorecard[scorecard["position_label"] == "Below Benchmark"])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Above Benchmark", above_count)
    c2.metric("At Benchmark", at_count)
    c3.metric("Below Benchmark", below_count)
    
    st.divider()
    
    tickers = scorecard["ticker"].unique().tolist()
    selected_ticker = st.selectbox("Select Company:", tickers)
    
    st.plotly_chart(plot_ratio_scorecard(scorecard, selected_ticker), use_container_width=True, key="chart_scorecard_main")
    
    st.markdown("### Raw Scorecard Data")
    disp_df = scorecard[scorecard["ticker"] == selected_ticker].copy()
    st.dataframe(disp_df, use_container_width=True, hide_index=True)


def page_outliers(result: BenchmarkCoreResult):
    outlier_df = result.outlier_df
    if outlier_df is None or outlier_df.empty:
        st.success("No statistical outliers detected.")
        return

    st.markdown("## Outliers")
    st.plotly_chart(outlier_scatter(outlier_df), use_container_width=True, key="chart_outliers_main")
    st.dataframe(outlier_df, use_container_width=True)


def page_peer_benchmark(result: BenchmarkCoreResult):
    st.markdown("## Peer Benchmark")
    
    # Peer Universe Coverage Badge (F9)
    req_tickers = st.session_state.get("requested_tickers", [])
    failed_tickers = st.session_state.get("failed_tickers", [])
    tickers_used = st.session_state.get("tickers_used", [])
    
    total_requested = len(req_tickers) if req_tickers else (len(tickers_used) + len(failed_tickers))
    included_count = len(tickers_used) if tickers_used else (len(result.clean_matrix) if result.clean_matrix is not None else 0)
    
    if total_requested > 0:
        if failed_tickers:
            st.info(f"**Peer Universe Coverage:** {included_count}/{total_requested} peers included ({len(failed_tickers)} skipped due to missing statements or data errors).")
            with st.expander("View Skipped Tickers"):
                st.write(", ".join(failed_tickers))
        else:
            st.success(f"**Peer Universe Coverage:** {included_count}/{total_requested} peers included (100% complete).")

    peer_stats = result.peer_stats_df
    if peer_stats is None or peer_stats.empty:
        st.info("No peer statistics available.")
        return
        
    st.plotly_chart(plot_peer_stats_heatmap(peer_stats), use_container_width=True, key="chart_peer_benchmark_main")
    
    st.markdown("### Descriptive Statistics")
    st.dataframe(peer_stats, use_container_width=True)


def page_composite(result: BenchmarkCoreResult):
    st.markdown("## Composite Scores")
    pillar_summary = result.pillar_summary_df
    
    if pillar_summary is None or pillar_summary.empty:
        st.info("No composite scores available.")
        return
        
    is_multi = len(pillar_summary) > 1
    
    if is_multi:
        temp_df = pillar_summary.rename(columns={"composite_score": "overall_score"})
        st.plotly_chart(health_score_bars(temp_df), use_container_width=True, key="chart_composite_main")
        
    st.dataframe(pillar_summary, use_container_width=True, hide_index=True)


# page_report removed — SWOT insights now live inside Client Comparison tab


def page_export(result: BenchmarkCoreResult):
    st.markdown("## Export Reports")
    st.caption("Generate and download professional executive briefings in various formats.")

    report_gen = get_report_gen()
    client_name = st.session_state.get("tally_client_name", "Client")
    sector_name = st.session_state.get("selected_sector", "Sector")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Excel Benchmark Report")
        st.caption("A multi-sheet spreadsheet containing full ratios, benchmarks, outliers, rankings, and structural explanations.")
        if st.button("Generate Excel Report", use_container_width=True):
            with st.spinner("Building Excel..."):
                explanation_df = report_gen.explain_all(result.ratio_scorecard_df)
                path = report_gen.export_excel(
                    result.ratio_scorecard_df,
                    result.peer_stats_df,
                    result.outlier_df if result.outlier_df is not None else pd.DataFrame(),
                    result.pillar_summary_df,
                    explanation_df,
                    sector=sector_name
                )
                with open(path, "rb") as f:
                    st.download_button(
                        "Download Excel",
                        f.read(),
                        file_name=path.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

    # PowerPoint export temporarily disabled as requested by the user.
    # To restore, remove the variable assignment and the triple-quotes around the block below.
    _disabled_pptx_code = """
    with c2:
        st.markdown("### PowerPoint Executive Suite")
        st.caption("A high-end 5-slide dark-mode executive briefing deck summarizing performance rankings, SWOT, outliers, and action items.")
        if st.button("Generate PPTX Presentation", use_container_width=True):
            with st.spinner("Compiling Slide Deck..."):
                try:
                    from modules.pptx_generator import PPTXGenerator
                    pptx_gen = PPTXGenerator()
                    
                    # 1. Parse SWOT
                    swot = report_gen.generate_swot(result.ratio_scorecard_df, client_name)
                    
                    # 2. Extract recommendations from AI chat session if completed
                    recommendations = []
                    briefing_content = ""
                    for msg in st.session_state.get("ai_chat_history", []):
                        if msg["role"] == "assistant" and ("This concludes our diagnostic review of" in msg["content"] or "--- DIAGNOSTIC BRIEFING SHEET ---" in msg["content"]):
                            if "--- DIAGNOSTIC BRIEFING SHEET ---" in msg["content"]:
                                parts = msg["content"].split("--- DIAGNOSTIC BRIEFING SHEET ---")
                                briefing_content = parts[1].strip()
                            else:
                                briefing_content = msg["content"]
                            break
                            
                    if briefing_content:
                        action_plan_part = ""
                        if "Strategic Action Plan:" in briefing_content:
                            action_plan_part = briefing_content.split("Strategic Action Plan:")[1].strip()
                        elif "Strategic Action Plan" in briefing_content:
                            action_plan_part = briefing_content.split("Strategic Action Plan")[1].strip()
                        else:
                            action_plan_part = briefing_content
                        
                        for line in action_plan_part.split("\n"):
                            line_clean = line.strip()
                            if not line_clean:
                                continue
                            for prefix in ["- [ ]", "* [ ]", "- [x]", "* [x]", "- ", "* ", "1. ", "2. ", "3. ", "4. "]:
                                if line_clean.startswith(prefix):
                                    line_clean = line_clean[len(prefix):].strip()
                                    break
                            if line_clean and len(line_clean) > 10:
                                recommendations.append(line_clean)

                    # 3. Apply rule-based fallbacks for recommendations if empty/incomplete
                    scorecard = result.ratio_scorecard_df
                    weak_ratios = set()
                    if scorecard is not None and not scorecard.empty:
                        weak_df = scorecard[scorecard["position_label"].isin(["Below Benchmark", "Near Benchmark (Low)"])]
                        weak_ratios = set(weak_df["ratio"].tolist())

                    # Fallbacks
                    while len(recommendations) < 4:
                        idx = len(recommendations)
                        if idx == 0:
                            # Cost Control
                            if any(r in weak_ratios for r in ["gross_margin", "operating_margin", "net_margin"]):
                                recommendations.append("Conduct an immediate operational expense audit and renegotiate key supplier agreements to restore gross profit margins.")
                            else:
                                recommendations.append("Establish rigorous structural cost control targets across administrative cost segments to prevent future margin compression.")
                        elif idx == 1:
                            # Working Capital & Liquidity
                            if any(r in weak_ratios for r in ["current_ratio", "quick_ratio", "cash_ratio"]):
                                recommendations.append("Implement aggressive working capital management systems, prioritizing cash conversion speed and receivable collections.")
                            else:
                                recommendations.append("Monitor safety inventory thresholds and optimize vendor credit terms to ensure immediate solvency protection.")
                        elif idx == 2:
                            # Scale & Growth
                            if any(r in weak_ratios for r in ["revenue_growth", "net_income_growth", "ocf_growth"]):
                                recommendations.append("Revise basic pricing strategies and expand high-margin geographic markets to re-accelerate sales volume growth.")
                            else:
                                recommendations.append("Implement target customer acquisition cost and scaling efficiency benchmarks before testing adjacent product offerings.")
                        elif idx == 3:
                            # Capital Allocation
                            if any(r in weak_ratios for r in ["roe", "roa", "roce", "asset_turnover"]):
                                recommendations.append("Set higher hurdle rates for new capital expenditures and optimize the utilization capacity of current fixed assets.")
                            else:
                                recommendations.append("Direct free cash flows toward high-ROE reinvestment opportunities or strategic debt service to improve capital efficiency.")

                    recommendations = recommendations[:4]

                    # 4. Extract anomaly score with three-tier resolution strategy
                    anomaly_score = np.nan
                    state_anomalies = st.session_state.get("anomaly_scores")
                    
                    if result.ratio_scorecard_df is not None and not result.ratio_scorecard_df.empty:
                        if "ticker" in result.ratio_scorecard_df.columns:
                            tickers_in_scorecard = result.ratio_scorecard_df["ticker"].dropna().unique().tolist()
                            
                            # Tier 1: Try matching client_name directly in state_anomalies
                            if state_anomalies is not None and not state_anomalies.empty:
                                if client_name in state_anomalies.index:
                                    anomaly_score = float(state_anomalies.loc[client_name])
                                elif "Client" in state_anomalies.index:
                                    anomaly_score = float(state_anomalies.loc["Client"])
                                    client_name = "Client"
                                
                            # Tier 2: Check other tickers present in the scorecard
                            if pd.isna(anomaly_score) or np.isnan(anomaly_score):
                                if state_anomalies is not None and not state_anomalies.empty:
                                    for t in tickers_in_scorecard:
                                        if t in state_anomalies.index:
                                            anomaly_score = float(state_anomalies.loc[t])
                                            client_name = t
                                            break
                                            
                            # Tier 3: Compute anomaly score dynamically on-the-fly using sector peer matrix
                            if pd.isna(anomaly_score) or np.isnan(anomaly_score):
                                try:
                                    from modules.outlier_engine import OutlierEngine
                                    from modules.benchmark_store import get_benchmark_store
                                    outlier_engine = OutlierEngine()
                                    store = get_benchmark_store()
                                    sector = st.session_state.get("selected_sector", sector_name)
                                    
                                    # Load peer matrix
                                    peer_stats_df, clean_matrix, _ = store.load(sector) or (None, None, None)
                                    if clean_matrix is not None and not clean_matrix.empty:
                                        # Use the first client ticker or "Client"
                                        target_ticker = tickers_in_scorecard[0] if tickers_in_scorecard else "Client"
                                        # Reconstruct client ratios row
                                        client_df = result.ratio_scorecard_df[result.ratio_scorecard_df["ticker"] == target_ticker]
                                        if not client_df.empty:
                                            client_ratios = dict(zip(client_df["ratio"], client_df["raw_value"]))
                                            client_row = pd.Series(client_ratios, name=target_ticker)
                                            # Align client columns with clean_matrix (detect_multivariate will fillna)
                                            client_row = client_row.reindex(clean_matrix.columns)
                                            combined_matrix = pd.concat([clean_matrix, pd.DataFrame([client_row])])
                                            # Fit Isolation Forest and score
                                            anomaly_scores = outlier_engine.detect_multivariate(combined_matrix)
                                            if target_ticker in anomaly_scores.index:
                                                anomaly_score = float(anomaly_scores.loc[target_ticker])
                                                client_name = target_ticker
                                except Exception as dyn_ex:
                                    logger.warning("Dynamic anomaly score calculation failed: %s", dyn_ex)

                    # 5. Compile PowerPoint
                    path = pptx_gen.generate_presentation(
                        client_name=client_name,
                        sector_name=sector_name,
                        scorecard_df=result.ratio_scorecard_df,
                        pillar_summary_df=result.pillar_summary_df,
                        outlier_df=result.outlier_df if result.outlier_df is not None else pd.DataFrame(),
                        swot=swot,
                        recommendations=recommendations,
                        anomaly_score=anomaly_score,
                        filename=None,
                        peer_stats_df=result.peer_stats_df,
                    )
                    
                    with open(path, "rb") as f:
                        st.download_button(
                            "Download PPTX Presentation",
                            f.read(),
                            file_name=path.name,
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Failed to generate PPTX Presentation: {e}")
                    logger.error("PPTX generation failed: %s", e, exc_info=True)
    """


# ──────────────────────────────────────────────────────────────────────────────
# CLIENT COMPARISON PAGE (Tally)
# ──────────────────────────────────────────────────────────────────────────────
def page_tally_client(result):
    """Render the Tally/Manual Client Comparison tab with 5 sub-tabs:
    Trial Balance / Financial Summary, Ratio Scorecard, Composite Scores, Ratio Distribution, SWOT Insights."""
    st.markdown("## Client Comparison")
    
    is_manual = st.session_state.get("manual_mode", False)
    input_method = st.session_state.get("manual_input_method", "Raw Financial Figures")
    
    if is_manual:
        st.caption("Your confidential financials benchmarked against the industry peer group.")
    else:
        st.caption("Your Tally client benchmarked against the industry peer group.")

    tally_result = st.session_state.get("tally_benchmark_result")
    trial_balance = st.session_state.get("tally_trial_balance")
    client_ratios = st.session_state.get("tally_client_ratios")
    client_name   = st.session_state.get("tally_client_name", "Client")

    if tally_result is None:
        st.info("Upload your TallySync CSVs or enter private manual figures to begin.")
        return

    st.success(f"Showing benchmarked results for: **{client_name}**")

    tab_title = "Financial Summary" if is_manual else "Trial Balance"
    sub_tabs = st.tabs([tab_title, "Ratio Scorecard", "Composite Scores", "Ratio Distribution", "SWOT Insights", "AI Diagnostic"])

    # ── Sub-Tab 1: Trial Balance / Financial Summary ──────────────────────
    with sub_tabs[0]:
        if is_manual:
            st.markdown("### Financial Summary")
            if input_method == "Raw Financial Figures":
                denom_unit = st.session_state.get("manual_denomination_unit", "Absolute (Actuals)")
                disp_factor = 1.0
                unit_label = "Amount"
                if denom_unit == "In Lakhs (₹ 100,000)":
                    disp_factor = 100000.0
                    unit_label = "Amount (In Lakhs)"
                elif denom_unit == "In Crores (₹ 10,000,000)":
                    disp_factor = 10000000.0
                    unit_label = "Amount (In Crores)"

                rev = st.session_state.get("m_raw_revenue", 0.0)
                cogs = st.session_state.get("m_raw_cogs", 0.0)
                opex = st.session_state.get("m_raw_opex", 0.0)
                cash = st.session_state.get("m_raw_cash", 0.0)
                receivables = st.session_state.get("m_raw_receivables", 0.0)
                inventory = st.session_state.get("m_raw_inventory", 0.0)
                other_ca = st.session_state.get("m_raw_other_ca", 0.0)
                fixed_assets = st.session_state.get("m_raw_fixed_assets", 0.0)
                payables = st.session_state.get("m_raw_payables", 0.0)
                other_cl = st.session_state.get("m_raw_other_cl", 0.0)
                debt = st.session_state.get("m_raw_debt", 0.0)
                equity = st.session_state.get("m_raw_equity", 0.0)
                
                gp = rev - cogs
                ebit = gp - opex
                tot_assets = cash + receivables + inventory + other_ca + fixed_assets
                tot_liab_eq = payables + other_cl + debt + equity
                
                c_inc, c_bs = st.columns(2)
                with c_inc:
                    st.markdown(
                        "<div style='font-family:\"Google Sans\";font-size:1rem;color:#00c4a7;font-weight:600;border-bottom:1px solid #1a3a37;padding-bottom:4px;margin-bottom:12px;'>Income Statement</div>",
                        unsafe_allow_html=True
                    )
                    inc_data = pd.DataFrame({
                        "Particulars": [
                            "Total Revenue (Sales)",
                            "Cost of Goods Sold (COGS)",
                            "Gross Profit",
                            "Operating Expenses (Opex)",
                            "EBIT (Operating Profit)"
                        ],
                        unit_label: [
                            f"{rev / disp_factor:,.2f}",
                            f"{cogs / disp_factor:,.2f}",
                            f"{gp / disp_factor:,.2f}",
                            f"{opex / disp_factor:,.2f}",
                            f"{ebit / disp_factor:,.2f}"
                        ]
                    })
                    st.dataframe(inc_data, use_container_width=True, hide_index=True)
                    
                    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
                    m1, m2 = st.columns(2)
                    m1.metric("Gross Profit Margin", f"{safe_divide(gp, rev)*100:.1f}%")
                    m2.metric("Operating Margin", f"{safe_divide(ebit, rev)*100:.1f}%")
                    
                with c_bs:
                    st.markdown(
                        "<div style='font-family:\"Google Sans\";font-size:1rem;color:#00c4a7;font-weight:600;border-bottom:1px solid #1a3a37;padding-bottom:4px;margin-bottom:12px;'>Balance Sheet Summary</div>",
                        unsafe_allow_html=True
                    )
                    bs_data = pd.DataFrame({
                        "Particulars": [
                            "Cash & Bank Balance",
                            "Accounts Receivable",
                            "Inventory (Stock-in-Hand)",
                            "Other Current Assets",
                            "Fixed Assets & Investments",
                            "Total Assets",
                            "Accounts Payable",
                            "Other Current Liabilities",
                            "Total Debt (Loans)",
                            "Total Equity",
                            "Total Liabilities & Equity"
                        ],
                        unit_label: [
                            f"{cash / disp_factor:,.2f}",
                            f"{receivables / disp_factor:,.2f}",
                            f"{inventory / disp_factor:,.2f}",
                            f"{other_ca / disp_factor:,.2f}",
                            f"{fixed_assets / disp_factor:,.2f}",
                            f"{tot_assets / disp_factor:,.2f}",
                            f"{payables / disp_factor:,.2f}",
                            f"{other_cl / disp_factor:,.2f}",
                            f"{debt / disp_factor:,.2f}",
                            f"{equity / disp_factor:,.2f}",
                            f"{tot_liab_eq / disp_factor:,.2f}"
                        ]
                    })
                    st.dataframe(bs_data, use_container_width=True, hide_index=True)
            else:
                st.markdown("### Ratio Inputs Summary")
                if trial_balance is not None and not trial_balance.empty:
                    st.dataframe(trial_balance, use_container_width=True, hide_index=True)
                else:
                    st.info("No ratio summary available.")
                    
            if trial_balance is not None and not trial_balance.empty:
                csv_data = trial_balance.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download Financial Summary CSV",
                    data=csv_data,
                    file_name=f"{client_name.replace(' ', '_')}_financial_summary.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        else:
            st.markdown("### Trial Balance")
            if trial_balance is not None and not trial_balance.empty:
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Ledgers", len(trial_balance))
                c2.metric("Total Debit", f'{trial_balance["Final Debit"].sum():,.2f}')
                c3.metric("Total Credit", f'{trial_balance["Final Credit"].sum():,.2f}')
                st.divider()
                st.dataframe(trial_balance, use_container_width=True, hide_index=True)

                csv_data = trial_balance.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download Trial Balance CSV",
                    data=csv_data,
                    file_name=f"{client_name.replace(' ', '_')}_trial_balance.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                st.info("No trial balance data available.")

    # ── Sub-Tab 2: Ratio Scorecard ────────────────────────────────────────
    with sub_tabs[1]:
        st.markdown("### Ratio Scorecard")
        st.caption("Detailed score breakdown comparing the client to the peer group using the **latest quarterly statements**.")
        scorecard = tally_result.ratio_scorecard_df
        if scorecard is not None and not scorecard.empty:
            total_ratios = len(scorecard)
            above_count = len(scorecard[scorecard["position_label"] == "Above Benchmark"])
            at_count    = len(scorecard[scorecard["position_label"] == "At Benchmark"])
            below_count = len(scorecard[scorecard["position_label"] == "Below Benchmark"])

            c1, c2, c3 = st.columns(3)
            c1.metric("Above Benchmark", above_count)
            c2.metric("At Benchmark", at_count)
            c3.metric("Below Benchmark", below_count)
            st.divider()

            st.plotly_chart(
                plot_ratio_scorecard(scorecard, client_name),
                use_container_width=True,
                key="chart_tally_scorecard"
            )

            st.markdown("### Raw Scorecard Data")
            st.dataframe(scorecard, use_container_width=True, hide_index=True)
        else:
            st.info("No scorecard data available.")

    # ── Sub-Tab 3: Composite Scores — Client inserted into peer ranking ───
    with sub_tabs[2]:
        st.markdown("### Composite Scores")
        pillar_summary = tally_result.pillar_summary_df
        if pillar_summary is not None and not pillar_summary.empty:
            comp_score = pillar_summary["composite_score"].values[0] if "composite_score" in pillar_summary.columns else None
            risk_cat   = pillar_summary["risk_category"].values[0] if "risk_category" in pillar_summary.columns else None

            if comp_score is not None:
                c1, c2, c3 = st.columns(3)
                c1.metric("Client Composite Score", f"{comp_score:.1f} / 100")
                c2.metric("Risk Category", risk_cat or "N/A")
                # Show where they rank vs peers if peer data is available
                if result is not None and result.pillar_summary_df is not None:
                    peer_ps = result.pillar_summary_df
                    if "composite_score" in peer_ps.columns:
                        n_peers = len(peer_ps)
                        n_below = int((peer_ps["composite_score"] < comp_score).sum())
                        c3.metric("Sector Percentile", f"{n_below/max(n_peers,1)*100:.0f}th")
                st.divider()

            # Combined chart: Peers + client highlighted
            if result is not None and result.pillar_summary_df is not None:
                st.plotly_chart(
                    health_score_bars_with_client(
                        result.pillar_summary_df,
                        pillar_summary,
                        client_name,
                    ),
                    use_container_width=True,
                    key="chart_tally_health_bars"
                )
            else:
                st.info("Build a benchmark first to see the client ranked against peers.")

            st.markdown("### Client Pillar Breakdown")
            st.dataframe(pillar_summary, use_container_width=True, hide_index=True)
        else:
            st.info("No composite scores available.")

    # ── Sub-Tab 4: Peer Competitive Mapping (Scatter Plot) ────────────────
    with sub_tabs[3]:
        st.markdown("### Peer Competitive Mapping")
        st.caption("Each dot represents an industry peer company's performance for the **latest quarter**. The orange diamond is your client.")
        
        # Use the peer clean_matrix from the benchmark result
        if result is not None and result.clean_matrix is not None and not result.clean_matrix.empty:
            peer_df = result.clean_matrix
            st.plotly_chart(
                plot_client_peer_scatter(peer_df, client_ratios=client_ratios, client_name=client_name),
                use_container_width=True,
                key="chart_tally_peer_scatter"
            )
        elif tally_result.clean_matrix is not None:
            st.info("Peer group distribution requires a loaded sector benchmark. Showing client data only.")
            st.dataframe(
                pd.DataFrame([client_ratios], index=[client_name]).T.rename(columns={client_name: "Value"}),
                use_container_width=True,
            )
        else:
            st.info("No distribution data available.")

    # ── Sub-Tab 5: SWOT Insights ──────────────────────────────────────────
    with sub_tabs[4]:
        st.markdown("### Strategic SWOT Insights")
        st.caption("Client financial health classified into Strengths, Weaknesses, Opportunities & Threats.")

        scorecard = tally_result.ratio_scorecard_df
        if scorecard is not None and not scorecard.empty:
            report_gen = get_report_gen()
            swot = report_gen.generate_swot(scorecard, client_name)

            total_items = sum(len(v) for v in swot.values())
            if total_items == 0:
                st.info("All ratios are in the moderate zone — no strong SWOT signals detected.")
            else:
                # Summary metrics
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("Strengths", len(swot["strengths"]))
                mc2.metric("Weaknesses", len(swot["weaknesses"]))
                mc3.metric("Opportunities", len(swot["opportunities"]))
                mc4.metric("Threats", len(swot["threats"]))
                st.divider()

                # ── 2×2 Grid ──
                top_left, top_right = st.columns(2)
                bot_left, bot_right = st.columns(2)

                def _render_swot_cards(container, items, css_class, header_text, badge_html):
                    with container:
                        st.markdown(
                            f'<div class="swot-header" style="display: flex; align-items: center;">{header_text} {badge_html}</div>',
                            unsafe_allow_html=True,
                        )
                        if not items:
                            st.caption("No items in this quadrant.")
                        for item in items:
                            st.markdown(
                                f"""
                                <div class="swot-card {css_class}">
                                    <div class="swot-ratio">{item['ratio_label']}</div>
                                    <div class="swot-values">
                                        Value: {item['raw_value']:.2f} &nbsp;|&nbsp;
                                        Peer Median: {item['peer_median']:.2f} &nbsp;|&nbsp;
                                        Percentile: P{item['percentile_rank']:.0f}
                                    </div>
                                    <div class="swot-narrative">{item['narrative']}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                badge_s = '<span style="background: rgba(46,204,113,0.12); color: #2ecc71; border-radius: 4px; padding: 2px 8px; font-size: 0.65rem; font-weight: 700; border: 1px solid rgba(46,204,113,0.3); margin-left: 10px;">INTERNAL / POSITIVE</span>'
                badge_w = '<span style="background: rgba(243,156,18,0.12); color: #f39c12; border-radius: 4px; padding: 2px 8px; font-size: 0.65rem; font-weight: 700; border: 1px solid rgba(243,156,18,0.3); margin-left: 10px;">INTERNAL / NEGATIVE</span>'
                badge_o = '<span style="background: rgba(0,196,167,0.12); color: #00c4a7; border-radius: 4px; padding: 2px 8px; font-size: 0.65rem; font-weight: 700; border: 1px solid rgba(0,196,167,0.3); margin-left: 10px;">EXTERNAL / STRATEGIC</span>'
                badge_t = '<span style="background: rgba(231,76,60,0.12); color: #e74c3c; border-radius: 4px; padding: 2px 8px; font-size: 0.65rem; font-weight: 700; border: 1px solid rgba(231,76,60,0.3); margin-left: 10px;">EXTERNAL / RISK</span>'

                _render_swot_cards(top_left,  swot["strengths"],     "swot-strength",     "STRENGTHS",     badge_s)
                _render_swot_cards(top_right, swot["weaknesses"],    "swot-weakness",     "WEAKNESSES",    badge_w)
                _render_swot_cards(bot_left,  swot["opportunities"], "swot-opportunity",  "OPPORTUNITIES", badge_o)
                _render_swot_cards(bot_right, swot["threats"],       "swot-threat",       "THREATS",       badge_t)

                # Export SWOT as CSV
                st.divider()
                swot_df = report_gen.swot_to_dataframe(swot)
                if not swot_df.empty:
                    csv_data = swot_df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "⬇ Download SWOT Report (CSV)",
                        data=csv_data,
                        file_name=f"{client_name.replace(' ', '_')}_SWOT_Report.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
        else:
            st.info("No scorecard data available for SWOT analysis.")

    # ── Sub-Tab 6: AI Diagnostic ──────────────────────────────────────────
    with sub_tabs[5]:
        st.markdown("### AI Financial Diagnostic")
        st.caption("Investigative consultation to uncover operational root causes of key financial deviations.")

        # Double safety check: if active client in session state doesn't match current client, reset chat
        if st.session_state.get("ai_chat_active_client") != client_name:
            st.session_state.ai_chat_session = None
            st.session_state.ai_chat_history = []
            st.session_state.ai_chat_active_client = client_name
            st.session_state.ai_chat_start_requested = False

        gemini_key = st.session_state.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            st.warning("Please configure your GEMINI_API_KEY in the environment variables or app settings to enable the AI Diagnostic.")
        else:
            # 1. Calculate dynamic Peer Archetype using K-Means clustering on peer group
            archetype_label, archetype_desc = "Balanced Sector Participant", "Average operational performance, maintaining stable margin limits, standard efficiency turnover, and moderate debt leverage matching sector baselines."
            peer_matrix = result.clean_matrix if result is not None else None
            if peer_matrix is not None and not peer_matrix.empty and client_ratios is not None:
                try:
                    from modules.outlier_engine import OutlierEngine
                    outlier_eng = OutlierEngine()
                    archetype_label, archetype_desc = outlier_eng.profile_archetypes(
                        peer_matrix=peer_matrix,
                        client_ratios=client_ratios,
                        client_name=client_name
                    )
                except Exception as e:
                    logger.warning(f"Failed to calculate Peer Archetype: {e}")

            # 2. Render Peer Archetype Badge
            st.markdown(
                f"<div style='border: 1px solid #1a3a37; background: linear-gradient(135deg, #071917 0%, #0b2220 100%); padding: 16px; border-radius: 8px; margin-bottom: 20px; font-family: \"Google Sans\", sans-serif; box-shadow: 0 4px 12px rgba(0,0,0,0.15);'>"
                f"<div style='color: #00c4a7; font-weight: 700; font-size: 1rem; border-bottom: 1px solid #1a3a37; padding-bottom: 6px; margin-bottom: 8px; letter-spacing: 0.5px;'>PEER ARCHETYPE: {archetype_label.upper()}</div>"
                f"<div style='color: #a5c3c0; font-size: 0.88rem; line-height: 1.4; font-weight: 500;'>{archetype_desc}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

            is_chat_active = st.session_state.ai_chat_session is not None
            
            # Simple primary/secondary triggers
            if is_chat_active:
                if st.button("Reset Consultation", use_container_width=True, type="secondary"):
                    st.session_state.ai_chat_session = None
                    st.session_state.ai_chat_history = []
                    st.session_state.ai_chat_start_requested = False
                    st.rerun()
            else:
                if st.button("Start Consultation", use_container_width=True, type="primary"):
                    st.session_state.ai_chat_start_requested = True
                    st.rerun()

            # Show active diagnostic scope
            scorecard = tally_result.ratio_scorecard_df
            if scorecard is not None and not scorecard.empty:
                weak_ratios = scorecard[scorecard["position_label"].isin(["Below Benchmark", "Near Benchmark (Low)"])]
                if not weak_ratios.empty:
                    st.markdown(
                        f"<div style='border: 1px solid #1a3a37; background-color: #0b1f1d; padding: 12px; border-radius: 6px; margin-bottom: 20px; font-family: \"Google Sans\", sans-serif;'>"
                        f"<div style='color: #00c4a7; font-weight: 600; font-size: 0.95rem; margin-bottom: 6px;'>Active Diagnostic Scope ({client_name})</div>"
                        f"<div style='color: #8da4a1; font-size: 0.85rem;'>The AI is conducting a causal analysis focusing on the following deviations:</div>"
                        f"<div style='margin-top: 8px; font-size: 0.85rem; color: #a5c3c0; font-weight: 500;'>"
                        + " &nbsp;•&nbsp; ".join([row['ratio'].replace('_', ' ').title() for _, row in weak_ratios.iterrows()]) +
                        f"</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                # Initialize chat session if requested and not yet started
                if st.session_state.ai_chat_session is None:
                    if st.session_state.get("ai_chat_start_requested", False):
                        with st.spinner("Initializing AI Diagnostic session..."):
                            try:
                                from modules.ai_handler import AIHandler
                                handler = AIHandler(gemini_key)
                                context_prompt = handler.generate_diagnostic_context(
                                    scorecard_df=scorecard,
                                    client_name=client_name,
                                    archetype_label=archetype_label,
                                    archetype_desc=archetype_desc
                                )
                                chat_sess = handler.start_diagnostic_chat(context_prompt)
                                st.session_state.ai_chat_session = chat_sess
                                
                                # Proactively request the first question
                                first_msg = handler.send_diagnostic_message(chat_sess, "Please introduce yourself as the FinMetrics AI Diagnostic Assistant and ask the first investigative, causal question regarding our weakest financial metric.")
                                st.session_state.ai_chat_history.append({"role": "assistant", "content": first_msg})
                                st.session_state.ai_chat_start_requested = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to initialize AI Diagnostic: {e}")
                                st.session_state.ai_chat_start_requested = False
                    else:
                        st.info("Click 'Start Consultation' to begin your multi-perspective diagnostic review.")

                if st.session_state.ai_chat_session is not None:
                    # Display history using Streamlit's native st.chat_message
                    for msg in st.session_state.ai_chat_history:
                        with st.chat_message(msg["role"], avatar="assistant" if msg["role"] == "assistant" else "user"):
                            st.write(msg["content"])

                    # Check if session has concluded
                    has_concluded = False
                    briefing_content = ""
                    for msg in st.session_state.ai_chat_history:
                        if msg["role"] == "assistant" and ("This concludes our diagnostic review of" in msg["content"] or "--- DIAGNOSTIC BRIEFING SHEET ---" in msg["content"]):
                            has_concluded = True
                            if "--- DIAGNOSTIC BRIEFING SHEET ---" in msg["content"]:
                                parts = msg["content"].split("--- DIAGNOSTIC BRIEFING SHEET ---")
                                briefing_content = parts[1].strip()
                            else:
                                briefing_content = msg["content"]
                            break

                    if has_concluded:
                        # Parse recommendations
                        recommendations = []
                        action_plan_part = ""
                        if "Strategic Action Plan:" in briefing_content:
                            action_plan_part = briefing_content.split("Strategic Action Plan:")[1].strip()
                        elif "Strategic Action Plan" in briefing_content:
                            action_plan_part = briefing_content.split("Strategic Action Plan")[1].strip()
                        else:
                            action_plan_part = briefing_content
                        
                        for line in action_plan_part.split("\n"):
                            line_clean = line.strip()
                            if not line_clean:
                                continue
                            for prefix in ["- [ ]", "* [ ]", "- [x]", "* [x]", "- ", "* ", "1. ", "2. ", "3. ", "4. "]:
                                if line_clean.startswith(prefix):
                                    line_clean = line_clean[len(prefix):].strip()
                                    break
                            if line_clean and len(line_clean) > 10:
                                recommendations.append(line_clean)
                                
                        # Clean up recommendations (take first 4, pad if needed)
                        while len(recommendations) < 4:
                            recommendations.append("Implement specific ratio tracking and optimization metrics to restore performance.")
                        recommendations = recommendations[:4]

                        # Map category dynamically/statically
                        def get_category_badge(idx: int, text: str) -> str:
                            if idx == 0:
                                return "FINANCIAL CONTROL"
                            elif idx == 1:
                                return "RISK MITIGATION"
                            elif idx == 2:
                                return "OPERATIONAL EFFICIENCY / GROWTH"
                            elif idx == 3:
                                return "CAPITAL OPTIMIZATION"
                            
                            t = text.lower()
                            if any(w in t for w in ["revenue", "sales", "margin", "cost", "pricing", "expense"]):
                                return "FINANCIAL CONTROL"
                            elif any(w in t for w in ["capital", "expenditure", "capex", "asset", "infrastructure", "invest"]):
                                return "CAPITAL OPTIMIZATION"
                            elif any(w in t for w in ["efficiency", "performance", "metric", "process", "inventory", "turnover"]):
                                return "OPERATIONAL EFFICIENCY / GROWTH"
                            elif any(w in t for w in ["leverage", "debt", "interest", "liquidity", "borrow"]):
                                return "RISK MITIGATION"
                            return "STRATEGIC ALIGNMENT"

                        rec1_cat = get_category_badge(0, recommendations[0])
                        rec2_cat = get_category_badge(1, recommendations[1])
                        rec3_cat = get_category_badge(2, recommendations[2])
                        rec4_cat = get_category_badge(3, recommendations[3])

                        st.markdown(
                            f"""<div style='border: 1px solid #00c4a7; background: linear-gradient(135deg, #022522 0%, #053b36 100%); padding: 24px; border-radius: 12px; margin-top: 24px; margin-bottom: 24px; font-family: "Google Sans", sans-serif; box-shadow: 0 8px 32px rgba(0,0,0,0.3);'>
<div style='color: #00c4a7; font-weight: 700; font-size: 1.25rem; border-bottom: 2px solid #00c4a7; padding-bottom: 8px; margin-bottom: 16px; letter-spacing: 0.5px;'>EXECUTIVE DIAGNOSTIC SUMMARY</div>
<div style='color: #d4f0ec; font-size: 0.95rem; line-height: 1.6; font-weight: 500;'>
The AI Financial Diagnostic has successfully concluded. A formal causal summary and strategic action roadmap have been synthesized based on {client_name}'s financial deviations and operational feedback.
</div>
<div class="rec-grid">
<div class="rec-card priority-critical">
<div class="rec-badge-container">
<span class="rec-badge critical">CRITICAL</span>
<span class="rec-cat">{rec1_cat}</span>
</div>
<div class="rec-step">ACTION 1: STRUCTURAL COST CONTROL</div>
<div class="rec-desc">{recommendations[0]}</div>
</div>
<div class="rec-card priority-high">
<div class="rec-badge-container">
<span class="rec-badge high">HIGH PRIORITY</span>
<span class="rec-cat">{rec2_cat}</span>
</div>
<div class="rec-step">ACTION 2: WORKING CAPITAL & LIQUIDITY ACTION</div>
<div class="rec-desc">{recommendations[1]}</div>
</div>
<div class="rec-card priority-medium">
<div class="rec-badge-container">
<span class="rec-badge medium">MEDIUM PRIORITY</span>
<span class="rec-cat">{rec3_cat}</span>
</div>
<div class="rec-step">ACTION 3: SCALE & GROWTH ACTION</div>
<div class="rec-desc">{recommendations[2]}</div>
</div>
<div class="rec-card priority-strategic">
<div class="rec-badge-container">
<span class="rec-badge strategic">STRATEGIC OPTIMIZATION</span>
<span class="rec-cat">{rec4_cat}</span>
</div>
<div class="rec-step">ACTION 4: CAPITAL ALLOCATION OPTIMIZATION</div>
<div class="rec-desc">{recommendations[3]}</div>
</div>
</div>
</div>""",
                            unsafe_allow_html=True
                        )

                        report_data = f"# AI Financial Diagnostic Briefing Report: {client_name}\n\n"
                        report_data += f"Date: {time.strftime('%Y-%m-%d')}\n"
                        report_data += f"Peer Archetype: {archetype_label}\n\n"
                        report_data += f"This concludes our diagnostic review of {client_name}'s financial deviations.\n\n"
                        report_data += briefing_content

                        st.download_button(
                            label="Download Executive Briefing Report (MD)",
                            data=report_data,
                            file_name=f"{client_name.replace(' ', '_')}_Diagnostic_Briefing_Report.md",
                            mime="text/markdown",
                            use_container_width=True
                        )

                    # Handle chat input
                    if not has_concluded:
                        user_input = st.chat_input("Explain your business actions, investments, or operational factors here...")
                        if user_input:
                            # Save and display user message immediately
                            st.session_state.ai_chat_history.append({"role": "user", "content": user_input})
                            
                            with st.spinner("Analyzing causality..."):
                                try:
                                    from modules.ai_handler import AIHandler
                                    handler = AIHandler(gemini_key)
                                    ai_response = handler.send_diagnostic_message(st.session_state.ai_chat_session, user_input)
                                    st.session_state.ai_chat_history.append({"role": "assistant", "content": ai_response})
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to get AI response: {e}")


def combine_client_and_peer_results(client_res: BenchmarkCoreResult, peer_res: BenchmarkCoreResult) -> BenchmarkCoreResult:
    """
    Combines client results (from CSV/Tally/Manual) with peer results
    (from sector benchmarks) for integrated view in dashboard main tabs.
    """
    logger.info("Merging client and peer results for integrated dashboard rendering")
    
    # 1. peer_stats_df is the same, use peer's
    peer_stats = peer_res.peer_stats_df
    
    # 2. ratio_scorecard_df: concatenate and drop duplicates on ['ticker', 'ratio']
    client_scorecard = client_res.ratio_scorecard_df
    peer_scorecard = peer_res.ratio_scorecard_df
    
    if client_scorecard is not None and not client_scorecard.empty:
        if peer_scorecard is not None and not peer_scorecard.empty:
            merged_scorecard = pd.concat([peer_scorecard, client_scorecard])
            merged_scorecard = merged_scorecard.drop_duplicates(subset=["ticker", "ratio"], keep="last")
        else:
            merged_scorecard = client_scorecard
    else:
        merged_scorecard = peer_scorecard
        
    # 3. pillar_summary_df: concatenate, drop duplicate tickers, and re-calculate sector rank and percentile
    client_summary = client_res.pillar_summary_df
    peer_summary = peer_res.pillar_summary_df
    
    if client_summary is not None and not client_summary.empty:
        if peer_summary is not None and not peer_summary.empty:
            merged_summary = pd.concat([peer_summary, client_summary])
            merged_summary = merged_summary.drop_duplicates(subset=["ticker"], keep="last")
            # Recalculate sector rank and percentile based on composite_score
            if "composite_score" in merged_summary.columns:
                merged_summary["sector_rank"] = merged_summary["composite_score"].rank(ascending=False, method="min").astype(int)
                n = len(merged_summary)
                merged_summary["percentile"] = (((n - merged_summary["sector_rank"]) / max(n - 1, 1)) * 100).round(1)
        else:
            merged_summary = client_summary
    else:
        merged_summary = peer_summary
        
    # 4. outlier_df: concatenate and drop duplicates on ['ticker', 'ratio']
    client_outliers = client_res.outlier_df
    peer_outliers = peer_res.outlier_df
    
    if client_outliers is not None and not client_outliers.empty:
        if peer_outliers is not None and not peer_outliers.empty:
            merged_outliers = pd.concat([peer_outliers, client_outliers])
            subset_cols = [c for c in ["ticker", "ratio"] if c in merged_outliers.columns]
            if subset_cols:
                merged_outliers = merged_outliers.drop_duplicates(subset=subset_cols, keep="last")
        else:
            merged_outliers = client_outliers
    else:
        merged_outliers = peer_outliers
        
    # 5. clean_matrix: concatenate and drop duplicates on index
    client_matrix = client_res.clean_matrix
    peer_matrix = peer_res.clean_matrix
    
    if client_matrix is not None and not client_matrix.empty:
        if peer_matrix is not None and not peer_matrix.empty:
            merged_matrix = pd.concat([peer_matrix, client_matrix])
            merged_matrix = merged_matrix[~merged_matrix.index.duplicated(keep="last")]
        else:
            merged_matrix = client_matrix
    else:
        merged_matrix = peer_matrix
        
    return BenchmarkCoreResult(
        peer_stats_df=peer_stats,
        ratio_scorecard_df=merged_scorecard,
        pillar_summary_df=merged_summary,
        outlier_df=merged_outliers,
        clean_matrix=merged_matrix
    )


# ──────────────────────────────────────────────────────────────────────────────
# MAIN ROUTER
# ──────────────────────────────────────────────────────────────────────────────
def main():
    inject_custom_css()
    global_cfg = render_sidebar()

    tabs = st.tabs([
        "Home",
        "Ratio Scorecard",
        "Outliers",
        "Peer Benchmark",
        "Composite Score",
        "Client Comparison",
        "Export",
    ])

    with tabs[0]:
        cfg = page_home(global_cfg)

        if cfg["run"]:
            run_pipeline(cfg)

        if cfg["run_client"]:
            run_client_pipeline(cfg)

        if cfg["run_tally"]:
            run_tally_pipeline(cfg)

        if cfg.get("run_manual"):
            run_manual_pipeline(cfg)

    # Determine active result (Standard CSV client upload, TallySync/Manual benchmark, or Peer Benchmark)
    client_res = st.session_state.client_result
    if client_res is None:
        client_res = st.session_state.tally_benchmark_result
        
    peer_res = st.session_state.benchmark_result
    
    if client_res is not None and peer_res is not None:
        result = combine_client_and_peer_results(client_res, peer_res)
    elif client_res is not None:
        result = client_res
    else:
        result = peer_res

    if result is not None:
        with tabs[1]: page_scorecard(result)
        with tabs[2]: page_outliers(result)
        with tabs[3]: page_peer_benchmark(result)
        with tabs[4]: page_composite(result)

    # Client Comparison Tab (index 5)
    with tabs[5]:
        page_tally_client(result)

    if result is not None:
        with tabs[6]: page_export(result)
    else:
        for i in [1, 2, 3, 4, 6]:
            with tabs[i]:
                st.info("Run an analysis first.")


if __name__ == "__main__":
    main()