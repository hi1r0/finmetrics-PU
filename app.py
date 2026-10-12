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

# Phase 1 Core Benchmarking Modules
from modules.benchmark_core import BenchmarkCore, BenchmarkCoreResult
from modules.benchmark_store import BenchmarkStore
from modules.visualization import (
    ratio_boxplot, ratio_heatmap, radar_chart,
    outlier_scatter, correlation_heatmap,
    health_score_bars, ratio_trend, outlier_table,
    plot_ratio_scorecard, plot_peer_stats_heatmap
)
from modules.ai_handler import AIHandler
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
        "parsed_data":      None,
        "market_info":      None,
        "selected_sector":  None,
        "requested_tickers":[],
        "failed_tickers":   [],
        "tickers_used":     [],
        "growth_df":        None,
        "anomaly_scores":   None,
        "benchmark_result": None,
        "ai_tickers":       [],
        "gemini_api_key":   "",
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

    status.success(f"Benchmark generation complete — {len(ratio_df)}/{len(tickers)} companies processed.")
    time.sleep(1)
    progress.empty()
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

    return {
        "chosen": chosen,
        "tickers": tickers,
        "iqr_mult": iqr_mult,
        "z_thresh": z_thresh,
        "contamination": contamination,
        "use_cache": global_cfg.get("use_cache", True),
        "run": run,
        "analysis_type": analysis_type,
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


def page_export(result: BenchmarkCoreResult):
    st.markdown("## Export Reports")
    st.caption("Generate and download professional executive briefings in various formats.")

    report_gen = get_report_gen()
    sector_name = st.session_state.get("selected_sector", "Sector")

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
        "Export",
    ])

    with tabs[0]:
        cfg = page_home(global_cfg)

        if cfg["run"]:
            run_pipeline(cfg)

    result = st.session_state.benchmark_result

    if result is not None:
        with tabs[1]: page_scorecard(result)
        with tabs[2]: page_outliers(result)
        with tabs[3]: page_peer_benchmark(result)
        with tabs[4]: page_composite(result)
        with tabs[5]: page_export(result)
    else:
        for i in [1, 2, 3, 4, 5]:
            with tabs[i]:
                st.info("Run an analysis first.")


if __name__ == "__main__":
    main()
