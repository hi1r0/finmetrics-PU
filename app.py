"""
app.py
======
FinMetrics Suite — Institutional Investment Choice & Financial Health Diagnostics
Specialized sector profiles, Piotroski F-Score, Altman Z''-Score, DuPont 3-Stage ROE,
Valuation Overlays, and Macro Sector Compass for NSE Equities.
"""

import logging
import time
import io
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# ── Module imports ─────────────────────────────────────────────────────────
from modules.sector_loader import SectorLoader
from modules.data_fetcher import DataFetcher
from modules.financial_parser import FinancialParser
from modules.ratio_engine import RatioEngine
from modules.outlier_engine import OutlierEngine, RATIO_LABELS
from modules.report_generator import ReportGenerator

# Institutional Benchmarking & Scoring
from modules.benchmark_core import BenchmarkCore, BenchmarkCoreResult, score_pillars, rank_and_categorize
from modules.benchmark_store import BenchmarkStore

# Sector Profiles & Health Models
from modules.sector_profiles import (
    get_sector_profile,
    list_supported_sectors,
    SectorProfile,
    SECTOR_PROFILES,
)
from modules.health_models import (
    compute_piotroski_f_score,
    compute_altman_z_score,
    compute_dupont_decomposition,
    compute_valuation_overlay,
    evaluate_company_health,
    HealthVerdict,
    DistressZone,
    CompanyHealthCheck,
    PiotroskiResult,
    AltmanZResult,
    DuPontResult,
    ValuationOverlayResult,
)
from modules.sector_compass import SectorCompassEngine, SectorCompassSummary

from modules.visualization import (
    ratio_boxplot, ratio_heatmap, radar_chart,
    outlier_scatter, correlation_heatmap,
    health_score_bars, ratio_trend, outlier_table,
    plot_ratio_scorecard, plot_peer_stats_heatmap,
    DARK_BG, CARD_BG, SURFACE, ACCENT, SECONDARY, GREEN, RED, YELLOW, TEXT, BODY_TEXT, MUTED, GRID, PRIMARY
)
from modules.ai_handler import AIHandler
from modules.utils import setup_logging, format_pct, safe_divide

from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

setup_logging()
logger = logging.getLogger(__name__)

# Must be the very first Streamlit execution call
st.set_page_config(
    page_title="FinMetrics Suite — Institutional Investment Diagnostics",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ──────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS — Abyss Teal Institutional Palette (Widescreen 96%)
# ──────────────────────────────────────────────────────────────────────────────
def inject_custom_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css?family=Google+Sans:400,500,700');

        /* ── Full Widescreen Layout ────────────────────────────── */
        .main .block-container {
            max-width: 96% !important;
            padding-top: 1.25rem !important;
            padding-right: 1.75rem !important;
            padding-left: 1.75rem !important;
            padding-bottom: 2rem !important;
        }

        html, body, [class*="css"], .stMarkdown, .stButton, .stTextInput,
        .stSelectbox, .stRadio, .stSlider, .stNumberInput, .stTextArea {
            font-family: 'Google Sans', sans-serif !important;
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Google Sans', sans-serif !important;
            font-weight: 700 !important;
            color: #d4f0ec !important;
        }

        [data-testid="stSidebar"] {
            background-color: #001f1e !important;
            border-right: 1px solid #1a3a37 !important;
        }

        .metric-card {
            background-color: #002623;
            border: 1px solid #1a3a37;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
        }

        .verdict-banner-pass {
            background: linear-gradient(90deg, rgba(0, 196, 167, 0.15) 0%, rgba(0, 38, 35, 0.8) 100%);
            border-left: 5px solid #00c4a7;
            border-radius: 6px;
            padding: 16px 20px;
            margin-bottom: 20px;
        }

        .verdict-banner-watch {
            background: linear-gradient(90deg, rgba(210, 153, 34, 0.15) 0%, rgba(0, 38, 35, 0.8) 100%);
            border-left: 5px solid #d29922;
            border-radius: 6px;
            padding: 16px 20px;
            margin-bottom: 20px;
        }

        .verdict-banner-red {
            background: linear-gradient(90deg, rgba(248, 81, 73, 0.15) 0%, rgba(0, 38, 35, 0.8) 100%);
            border-left: 5px solid #f85149;
            border-radius: 6px;
            padding: 16px 20px;
            margin-bottom: 20px;
        }

        .diagnostic-card {
            background-color: #002623;
            border: 1px solid #1a3a37;
            border-radius: 8px;
            padding: 14px 18px;
            margin-bottom: 10px;
        }

        /* ── Institutional Text Badges & Status Dots ───────────── */
        .badge-pass {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: #00c4a7;
            background: rgba(0, 196, 167, 0.12);
            border: 1px solid rgba(0, 196, 167, 0.35);
            border-radius: 4px;
            padding: 2px 7px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .badge-fail {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: #f85149;
            background: rgba(248, 81, 73, 0.12);
            border: 1px solid rgba(248, 81, 73, 0.35);
            border-radius: 4px;
            padding: 2px 7px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .badge-watch {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: #d29922;
            background: rgba(210, 153, 34, 0.12);
            border: 1px solid rgba(210, 153, 34, 0.35);
            border-radius: 4px;
            padding: 2px 7px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .status-dot-pass {
            display: inline-block;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background-color: #00c4a7;
        }

        .status-dot-fail {
            display: inline-block;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background-color: #f85149;
        }

        .status-dot-watch {
            display: inline-block;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background-color: #d29922;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def clean_sector_display_name(raw_name: str) -> str:
    """Normalizes raw sector names or cache directory slugs to clean institutional labels."""
    if not raw_name:
        return ""
    mapping = {
        "ai: minerals": "Minerals & Mining",
        "ai__minerals": "Minerals & Mining",
        "minerals": "Minerals & Mining",
        "ai: fmcg": "FMCG",
        "ai__fmcg": "FMCG",
        "ai: power": "Power & Energy",
        "ai: power_": "Power & Energy",
        "ai__power_": "Power & Energy",
        "power": "Power & Energy",
        "ai: electronics": "Electronics & Hardware",
        "ai__electronics": "Electronics & Hardware",
        "electronics": "Electronics & Hardware",
        "ai: banking": "Banking & Finance",
        "ai__banking": "Banking & Finance",
        "banking": "Banking & Finance",
        "automobile": "Automobile",
        "it": "Information Technology",
        "information technology": "Information Technology",
        "pharmaceuticals": "Pharmaceuticals",
        "pharma": "Pharmaceuticals",
        "metals & mining": "Metals & Mining",
        "metals": "Metals & Mining",
    }
    cleaned = raw_name.strip()
    return mapping.get(cleaned.lower(), cleaned)


# ──────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ──────────────────────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "parsed_data": None,
        "market_info": {},
        "selected_sector": "Automobile",
        "tickers_used": [],
        "growth_df": None,
        "anomaly_scores": None,
        "benchmark_result": None,
        "sector_checks": {},         # Dict[sector_name, List[CompanyHealthCheck]]
        "sector_summaries": [],      # List[SectorCompassSummary]
        "gemini_api_key": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ──────────────────────────────────────────────────────────────────────────────
# SINGLETON CACHES
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_sector_loader(): return SectorLoader()

@st.cache_resource
def get_fetcher(): return DataFetcher(use_cache=True, cache_ttl_hours=24, delay_seconds=0.3)

@st.cache_resource
def get_parser(): return FinancialParser()

@st.cache_resource
def get_ratio_engine(): return RatioEngine()

@st.cache_resource
def get_report_gen(): return ReportGenerator()

@st.cache_resource
def get_benchmark_store(): return BenchmarkStore()


# ──────────────────────────────────────────────────────────────────────────────
# HELPER: ROTATIONAL GEMINI API KEY POOL
# ──────────────────────────────────────────────────────────────────────────────
def get_rotational_api_keys() -> List[str]:
    """Retrieves API keys from environment (GEMINI_API_KEY or numbered rotation)."""
    keys = []
    # 1. Comma separated GEMINI_API_KEY
    env_key = os.environ.get("GEMINI_API_KEY", "")
    if env_key:
        keys.extend([k.strip() for k in env_key.split(",") if k.strip()])
    
    # 2. Numbered keys (GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.)
    for i in range(1, 10):
        k = os.environ.get(f"GEMINI_API_KEY_{i}")
        if k and k.strip() and k.strip() not in keys:
            keys.append(k.strip())

    # 3. Streamlit secrets fallback (guarded against missing secrets.toml)
    if not keys:
        try:
            if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                val = st.secrets["GEMINI_API_KEY"]
                if val:
                    keys.extend([k.strip() for k in str(val).split(",") if k.strip()])
        except Exception:
            pass

    return keys


# ──────────────────────────────────────────────────────────────────────────────
# HEALTH MODEL SUITE COMPUTATION
# ──────────────────────────────────────────────────────────────────────────────
def compute_sector_health_suite(
    sector: str,
    benchmark_result: BenchmarkCoreResult,
    parsed_data: Optional[Dict] = None,
    market_info: Optional[Dict] = None,
) -> List[CompanyHealthCheck]:
    """
    Computes institutional health models (Piotroski F-Score, Altman Z'', DuPont, Valuation Overlay)
    for each company in the sector benchmark.
    """
    health_checks: List[CompanyHealthCheck] = []
    if benchmark_result is None or benchmark_result.clean_matrix is None:
        return health_checks

    clean_df = benchmark_result.clean_matrix
    peer_stats = benchmark_result.peer_stats_df
    pillar_summary = benchmark_result.pillar_summary_df

    sector_medians = {}
    if peer_stats is not None and not peer_stats.empty and "median" in peer_stats.columns:
        sector_medians = peer_stats["median"].to_dict()

    for ticker in clean_df.index:
        ratios = clean_df.loc[ticker].to_dict()
        comp_score = 50.0
        if pillar_summary is not None and ticker in pillar_summary.index:
            comp_score = float(pillar_summary.loc[ticker].get("composite_score", 50.0))

        # Check parsed statement history
        p_ticker = (parsed_data or {}).get(ticker, {})
        inc_df = p_ticker.get("income_statement", pd.DataFrame())
        bal_df = p_ticker.get("balance_sheet", pd.DataFrame())
        cf_df = p_ticker.get("cash_flow", pd.DataFrame())

        if not inc_df.empty and not bal_df.empty:
            inc_curr = inc_df.iloc[-1]
            bal_curr = bal_df.iloc[-1]
            cf_curr = cf_df.iloc[-1] if not cf_df.empty else pd.Series()

            inc_prev = inc_df.iloc[-2] if len(inc_df) >= 2 else None
            bal_prev = bal_df.iloc[-2] if len(bal_df) >= 2 else None
            cf_prev = cf_df.iloc[-2] if len(cf_df) >= 2 else None

            piotroski = compute_piotroski_f_score(inc_curr, bal_curr, cf_curr, inc_prev, bal_prev, cf_prev)
            altman_z = compute_altman_z_score(bal_curr, inc_curr)
            dupont = compute_dupont_decomposition(inc_curr, bal_curr)
        else:
            # Fallback estimation using computed ratios in clean_matrix
            net_margin = float(ratios.get("net_margin", 10.0) or 10.0)
            asset_turnover = float(ratios.get("asset_turnover", 1.0) or 1.0)
            d_to_e = float(ratios.get("debt_to_equity", 0.5) or 0.5)
            equity_mult = round(1.0 + d_to_e, 2)
            roe = float(ratios.get("roe", net_margin * asset_turnover * equity_mult) or (net_margin * asset_turnover * equity_mult))

            dupont = DuPontResult(
                roe=round(roe, 2),
                net_profit_margin=round(net_margin, 2),
                asset_turnover=round(asset_turnover, 2),
                equity_multiplier=round(equity_mult, 2),
                primary_driver="Margin Power (Pricing Moat)" if net_margin >= 18.0 else ("Asset Velocity (Capital Efficiency)" if asset_turnover >= 1.2 else "Balanced Operational Model"),
                driver_narrative=f"ROE of {roe:.1f}% combines net margin ({net_margin:.1f}%), asset turnover ({asset_turnover:.2f}x), and equity multiplier ({equity_mult:.2f}x).",
            )

            curr_ratio = float(ratios.get("current_ratio", 1.5) or 1.5)
            op_margin = float(ratios.get("operating_margin", 12.0) or 12.0)
            x1 = max(0.0, (curr_ratio - 1.0) * 0.2)
            x2 = 0.35
            x3 = max(0.0, op_margin / 100.0 * asset_turnover)
            x4 = 1.0 / max(d_to_e, 0.1)
            z_est = round(6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4, 2)
            zone = DistressZone.SAFE if z_est > 2.60 else (DistressZone.GREY if z_est >= 1.10 else DistressZone.DISTRESS)
            altman_z = AltmanZResult(
                z_score=z_est,
                zone=zone,
                x1_working_capital_to_assets=round(x1, 3),
                x2_retained_earnings_to_assets=round(x2, 3),
                x3_ebit_to_assets=round(x3, 3),
                x4_equity_to_liabilities=round(x4, 3),
                interpretation="Synthesized from solvency and liquidity metrics.",
            )

            # Piotroski approximation
            score = 5
            if roe > 15: score += 1
            if op_margin > 15: score += 1
            if d_to_e < 0.5: score += 1
            if curr_ratio > 1.5: score += 1
            piotroski = PiotroskiResult(
                score=min(9, score),
                rating="High Quality (Tier 1)" if score >= 8 else ("Moderate Quality" if score >= 5 else "Weak / Low Quality"),
                signals=[],
                profitability_score=3,
                leverage_liquidity_score=2,
                operating_efficiency_score=1,
            )

        m_info = (market_info or {}).get(ticker, {})
        val = compute_valuation_overlay(
            market_info=m_info,
            ratios=ratios,
            sector_medians=sector_medians,
            piotroski_score=piotroski.score if piotroski else None,
            altman_zone=altman_z.zone if altman_z else None,
        )

        check = evaluate_company_health(
            ticker=ticker,
            sector=sector,
            ratios=ratios,
            fundamental_composite=comp_score,
            piotroski=piotroski,
            altman_z=altman_z,
            dupont=dupont,
            valuation=val,
        )
        health_checks.append(check)

    return health_checks


# ──────────────────────────────────────────────────────────────────────────────
# BENCHMARK PIPELINE EXECUTOR
# ──────────────────────────────────────────────────────────────────────────────
def run_sector_pipeline(sector: str, tickers: List[str], use_cache: bool = True):
    """Executes full data ingestion, parsing, ratio computation, and benchmarking."""
    fetcher = DataFetcher(use_cache=use_cache, delay_seconds=0.3)
    parser = get_parser()
    ratio_engine = get_ratio_engine()
    outlier_engine = OutlierEngine(iqr_multiplier=1.5, zscore_threshold=3.5)
    store = get_benchmark_store()
    benchmark_core = BenchmarkCore()

    progress = st.progress(0)
    status = st.empty()

    status.info(f"Ingesting statements for {len(tickers)} companies in {sector}...")
    raw_data = fetcher.fetch_all(tickers, progress_callback=lambda d, t, tick: progress.progress(int(d / t * 40)))

    if not raw_data:
        status.error(f"Failed to fetch data for {sector}.")
        return

    status.info("Retrieving live market valuations...")
    market_info = {}
    for i, t in enumerate(tickers):
        market_info[t] = fetcher.fetch_market_info(t)
        progress.progress(40 + int(i / len(tickers) * 15))

    status.info("Parsing canonical statements...")
    parsed = parser.parse_all(raw_data)
    progress.progress(60)

    status.info("Computing sector ratios...")
    ratio_df = ratio_engine.compute_all(parsed, market_info, requested_tickers=tickers)
    growth_df = ratio_engine.compute_growth_metrics(parsed)
    progress.progress(75)

    if ratio_df.empty:
        status.warning(f"No ratios computed for {sector}.")
        return

    failed_tickers = ratio_df.attrs.get("failed_tickers", [])
    merged = ratio_df.join(growth_df, how="left") if not growth_df.empty else ratio_df
    merged.attrs["failed_tickers"] = failed_tickers
    merged.attrs["requested_tickers"] = tickers

    status.info("Detecting anomalies and scoring pillars...")
    outlier_df = outlier_engine.detect(merged)
    anomaly_scores = outlier_engine.detect_multivariate(merged, contamination=0.10)
    progress.progress(85)

    benchmark_result = benchmark_core.run(merged, outlier_df)
    store.save(sector, benchmark_result.peer_stats_df, merged)
    progress.progress(95)

    # Compute Health Suite
    health_checks = compute_sector_health_suite(sector, benchmark_result, parsed, market_info)

    # Persist in session state
    st.session_state.parsed_data = parsed
    st.session_state.market_info = market_info
    st.session_state.selected_sector = sector
    st.session_state.tickers_used = list(ratio_df.index)
    st.session_state.benchmark_result = benchmark_result
    st.session_state.growth_df = growth_df
    st.session_state.anomaly_scores = anomaly_scores
    st.session_state.sector_checks[sector] = health_checks

    status.success(f"Benchmark & Health Suite generated for {sector} ({len(ratio_df)} companies processed)!")
    progress.progress(100)
    time.sleep(1)
    progress.empty()
    status.empty()
    st.rerun()


def load_cached_sector(sector: str) -> bool:
    """Loads a sector benchmark from store and populates session state."""
    store = get_benchmark_store()
    loaded = store.load(sector)
    if loaded is None:
        return False
    peer_stats_df, clean_matrix, metadata = loaded
    core = BenchmarkCore()
    res = core.run(clean_matrix, pd.DataFrame())

    # Try loading cached statements from DataFetcher without network calls
    fetcher = DataFetcher(use_cache=True)
    tickers = list(clean_matrix.index)
    raw_data = fetcher.fetch_all(tickers)
    parsed = get_parser().parse_all(raw_data) if raw_data else {}
    market_info = {t: fetcher.fetch_market_info(t) for t in tickers}

    checks = compute_sector_health_suite(sector, res, parsed, market_info)

    st.session_state.selected_sector = sector
    st.session_state.benchmark_result = res
    st.session_state.parsed_data = parsed
    st.session_state.market_info = market_info
    st.session_state.tickers_used = tickers
    st.session_state.sector_checks[sector] = checks
    return True


# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR NAVIGATION & SETTINGS
# ──────────────────────────────────────────────────────────────────────────────
def render_sidebar() -> Dict[str, Any]:
    with st.sidebar:
        st.markdown(
            '<div style="font-size:1.15rem;font-weight:700;color:#00c4a7;margin-bottom:12px;">'
            'Investment Diagnostics</div>',
            unsafe_allow_html=True,
        )

        # Primary non-financial sector list
        supported_sectors = list_supported_sectors()
        all_sectors = get_sector_loader().get_sectors()
        combined_sector_choices = supported_sectors + [s for s in all_sectors if s not in supported_sectors]

        current_sector = st.session_state.get("selected_sector", "Automobile")
        idx = combined_sector_choices.index(current_sector) if current_sector in combined_sector_choices else 0

        chosen_sector = st.selectbox(
            "Target Investment Sector:",
            combined_sector_choices,
            index=idx,
            help="Select the NSE sector universe to evaluate. Archetype scoring rules will automatically adapt."
        )

        profile = get_sector_profile(chosen_sector)
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="color:#00c4a7;font-weight:600;font-size:0.85rem;">SECTOR OPERATING ARCHETYPE</div>
                <div style="color:#d4f0ec;font-weight:700;font-size:0.95rem;">{profile.archetype}</div>
                <div style="color:#7ab8b2;font-size:0.80rem;margin-top:6px;">{profile.description}</div>
                <div style="color:#5a8a85;font-size:0.75rem;margin-top:8px;">
                    Anchor Multiple: <b>{profile.valuation_benchmark_metric.upper()}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        store = get_benchmark_store()
        is_stored = chosen_sector in store.list_available() or store._sector_slug(chosen_sector) in [store._sector_slug(s) for s in store.list_available()]

        c_btn1, c_btn2 = st.columns(2)
        build_clicked = c_btn1.button("Build / Fetch", type="primary", use_container_width=True)
        load_clicked = c_btn2.button("Load Stored", disabled=not is_stored, use_container_width=True)

        if build_clicked:
            tickers = get_sector_loader().get_tickers(chosen_sector)
            run_sector_pipeline(chosen_sector, tickers, use_cache=True)

        if load_clicked:
            success = load_cached_sector(chosen_sector)
            if success:
                st.success(f"Loaded {chosen_sector} from store!")
                st.rerun()

        st.divider()

        # AI Rotation Status
        st.markdown("### AI Executive Engine")
        keys = get_rotational_api_keys()
        if keys:
            st.success(f"API Key Pool Active ({len(keys)} rotational keys).")
        else:
            st.caption("AI insights offline (add GEMINI_API_KEY in .env).")

        st.divider()
        use_cache = st.toggle("Use Disk Cache", value=True)

        if st.button("Clear Cache & Storage", use_container_width=True):
            import shutil
            from modules.utils import DATA_CACHE
            if DATA_CACHE.exists():
                shutil.rmtree(DATA_CACHE)
                DATA_CACHE.mkdir(parents=True, exist_ok=True)
            st.success("Cache cleared!")
            time.sleep(0.5)
            st.rerun()

    return {
        "sector": chosen_sector,
        "profile": profile,
        "use_cache": use_cache,
    }


# ──────────────────────────────────────────────────────────────────────────────
# TAB 1: SECTOR COMPASS (Macro View & Cross-Sector Ranking)
# ──────────────────────────────────────────────────────────────────────────────
def page_sector_compass():
    st.markdown("## Macro Sector Compass")
    st.caption("Cross-sector fundamental health, balance sheet resilience, and valuation buffers across NSE sectors.")

    store = get_benchmark_store()
    available_sectors = store.list_available()

    # Ensure current sector has checks
    curr_sector = st.session_state.selected_sector
    if curr_sector and curr_sector not in st.session_state.sector_checks:
        res = st.session_state.benchmark_result
        if res is not None:
            st.session_state.sector_checks[curr_sector] = compute_sector_health_suite(
                curr_sector, res, st.session_state.parsed_data, st.session_state.market_info
            )

    # Synthesize summaries for available sectors
    summaries: List[SectorCompassSummary] = []
    for sec_name in available_sectors:
        # Load or use cached checks
        checks = st.session_state.sector_checks.get(sec_name)
        if not checks:
            loaded = store.load(sec_name)
            if loaded:
                peer_stats_df, clean_matrix, _ = loaded
                core = BenchmarkCore()
                res = core.run(clean_matrix, pd.DataFrame())
                checks = compute_sector_health_suite(sec_name, res)
                st.session_state.sector_checks[sec_name] = checks

        if checks:
            display_name = clean_sector_display_name(sec_name)
            prof = get_sector_profile(sec_name)
            summary = SectorCompassEngine.evaluate_sector(display_name, prof.archetype, checks)
            if summary:
                summaries.append(summary)

    if not summaries:
        st.info("No sector benchmarks loaded yet. Select a sector in the sidebar and click **'Build / Fetch'** or **'Load Stored'**.")
        return

    leaderboard = SectorCompassEngine.rank_sectors(summaries)

    # Key Metrics Bar
    top_sector = leaderboard.iloc[0]["Sector"] if not leaderboard.empty else "N/A"
    top_score = leaderboard.iloc[0]["Attractiveness Score"] if not leaderboard.empty else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Highest Attractiveness Sector", clean_sector_display_name(top_sector))
    c2.metric("Top Sector Score", f"{top_score}/100")
    c3.metric("Evaluated Sectors", len(summaries))
    c4.metric("Active Benchmark", clean_sector_display_name(curr_sector))

    st.markdown("### Cross-Sector Attractiveness Leaderboard")
    st.dataframe(leaderboard, use_container_width=True)

    # Visual Attractiveness Ranking & Breadth Charts
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=[s.sector_name for s in summaries],
            y=[s.attractiveness_score for s in summaries],
            marker_color=[GREEN if s.attractiveness_score >= 70 else (YELLOW if s.attractiveness_score >= 55 else RED) for s in summaries],
            text=[f"{s.attractiveness_score:.1f}" for s in summaries],
            textposition="auto",
        ))
        fig_bar.update_layout(
            title="Sector Attractiveness Score (0 to 100)",
            paper_bgcolor=DARK_BG,
            plot_bgcolor=CARD_BG,
            font=dict(color=TEXT, family="Google Sans"),
            yaxis=dict(range=[0, 100], gridcolor=GRID),
            xaxis=dict(gridcolor=GRID),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart2:
        fig_quad = go.Figure()
        for s in summaries:
            color = GREEN if s.distress_risk_pct <= 10 else (YELLOW if s.distress_risk_pct <= 25 else RED)
            fig_quad.add_trace(go.Scatter(
                x=[s.distress_risk_pct],
                y=[s.sector_breadth_pct],
                mode="markers+text",
                name=s.sector_name,
                text=[s.sector_name],
                textposition="top center",
                marker=dict(size=14, color=color, line=dict(width=1, color=TEXT)),
            ))
        fig_quad.update_layout(
            title="Quality Breadth (%) vs. Distress Risk (%)",
            xaxis_title="Distress Risk (% in Altman Distress Zone - Lower is Better)",
            yaxis_title="Quality Breadth (% Healthy - Higher is Better)",
            paper_bgcolor=DARK_BG,
            plot_bgcolor=CARD_BG,
            font=dict(color=TEXT, family="Google Sans"),
            yaxis=dict(range=[0, 105], gridcolor=GRID),
            xaxis=dict(range=[-5, 105], gridcolor=GRID),
            showlegend=False,
        )
        st.plotly_chart(fig_quad, use_container_width=True)

    # Sector Operating Archetype Guides
    st.markdown("### Institutional Sector Operating Archetypes")
    cols_arch = st.columns(len(SECTOR_PROFILES))
    for col, (s_name, p) in zip(cols_arch, SECTOR_PROFILES.items()):
        with col:
            st.markdown(
                f"""
                <div class="diagnostic-card">
                    <div style="color:#00c4a7;font-weight:700;font-size:0.90rem;">{s_name}</div>
                    <div style="color:#d4f0ec;font-weight:600;font-size:0.80rem;margin-top:4px;">{p.archetype}</div>
                    <div style="color:#7ab8b2;font-size:0.75rem;margin-top:6px;">{p.description}</div>
                    <div style="color:#5a8a85;font-size:0.70rem;margin-top:8px;">
                        Key Metrics: {", ".join(p.key_focus_ratios[:3])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ──────────────────────────────────────────────────────────────────────────────
# TAB 2: COMPANY HEALTH DIAGNOSTICS (Micro View)
# ──────────────────────────────────────────────────────────────────────────────
def page_company_health(result: BenchmarkCoreResult):
    st.markdown("## Company Financial Health Checkup")
    st.caption("Comprehensive fundamental quality diagnostics: Piotroski 9-Point Score, Altman Z''-Score, DuPont ROE, and Valuation Multiples.")

    sector = st.session_state.selected_sector
    checks = st.session_state.sector_checks.get(sector, [])

    if not checks and result is not None:
        checks = compute_sector_health_suite(sector, result, st.session_state.parsed_data, st.session_state.market_info)
        st.session_state.sector_checks[sector] = checks

    if not checks:
        st.info("Run or load a sector benchmark to diagnose company financial health.")
        return

    tickers = [c.ticker for c in checks]
    selected_ticker = st.selectbox("Select Company to Inspect:", tickers, index=0)

    company_check = next((c for c in checks if c.ticker == selected_ticker), checks[0])

    # 1. Headline Verdict Banner
    banner_class = "verdict-banner-pass" if company_check.verdict == HealthVerdict.PASS else (
        "verdict-banner-watch" if company_check.verdict == HealthVerdict.WATCH else "verdict-banner-red"
    )
    badge_label = f"HEALTH VERDICT: {company_check.verdict.value}"

    st.markdown(
        f"""
        <div class="{banner_class}">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div style="font-size:1.2rem;font-weight:700;color:#d4f0ec;">{company_check.ticker} — {badge_label}</div>
                <div style="font-size:1.1rem;font-weight:700;color:#00c4a7;">Fundamental Score: {company_check.composite_health_score}/100</div>
            </div>
            <div style="font-size:0.95rem;color:#d4f0ec;margin-top:6px;">{company_check.headline_rationale}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Key Diagnostic Metrics Row
    m1, m2, m3, m4, m5 = st.columns(5)
    f_score_val = f"{company_check.piotroski.score}/9" if company_check.piotroski else "N/A"
    z_score_val = f"{company_check.altman_z.z_score} ({company_check.altman_z.zone.value})" if company_check.altman_z else "N/A"
    roe_val = f"{company_check.dupont.roe:.1f}%" if company_check.dupont else "N/A"
    pe_val = f"{company_check.valuation.pe_ratio:.1f}x" if company_check.valuation and company_check.valuation.pe_ratio else "N/A"
    val_posture = company_check.valuation.posture if company_check.valuation else "N/A"

    m1.metric("Piotroski F-Score", f_score_val)
    m2.metric("Altman Z'' Distress", z_score_val)
    m3.metric("DuPont ROE", roe_val)
    m4.metric("P/E Ratio", pe_val)
    m5.metric("Valuation Posture", val_posture)

    st.divider()

    # Detailed Sub-tabs for Models
    tab_f, tab_z, tab_dupont, tab_val, tab_swot = st.tabs([
        "Piotroski F-Score (9-Point)",
        "Altman Z''-Score (Solvency)",
        "DuPont 3-Stage ROE",
        "Valuation vs Sector",
        "SWOT Fundamental Matrix",
    ])

    # ── Piotroski 9-Point Tab ────────────────────────────────────────────────
    with tab_f:
        if company_check.piotroski and company_check.piotroski.signals:
            p = company_check.piotroski
            st.markdown(f"### Piotroski F-Score: **{p.score} / 9** — *{p.rating}*")
            st.caption("Joseph Piotroski's 9 binary accounting tests assessing profitability, financial leverage, and operating efficiency.")

            c_p1, c_p2, c_p3 = st.columns(3)
            with c_p1:
                st.markdown(f"#### Profitability ({p.profitability_score}/4)")
                for sig in p.signals[:4]:
                    badge_html = (
                        '<span class="badge-pass"><span class="status-dot-pass"></span>PASS</span>'
                        if sig.passed
                        else '<span class="badge-fail"><span class="status-dot-fail"></span>FAIL</span>'
                    )
                    st.markdown(
                        f"""
                        <div class="diagnostic-card">
                            <div style="display:flex;justify-content:space-between;align-items:center;">
                                <div style="font-weight:600;font-size:0.85rem;color:#d4f0ec;">{sig.name}</div>
                                <div>{badge_html}</div>
                            </div>
                            <div style="font-size:0.80rem;color:#7ab8b2;margin-top:6px;">{sig.description}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            with c_p2:
                st.markdown(f"#### Leverage & Liquidity ({p.leverage_liquidity_score}/3)")
                for sig in p.signals[4:7]:
                    badge_html = (
                        '<span class="badge-pass"><span class="status-dot-pass"></span>PASS</span>'
                        if sig.passed
                        else '<span class="badge-fail"><span class="status-dot-fail"></span>FAIL</span>'
                    )
                    st.markdown(
                        f"""
                        <div class="diagnostic-card">
                            <div style="display:flex;justify-content:space-between;align-items:center;">
                                <div style="font-weight:600;font-size:0.85rem;color:#d4f0ec;">{sig.name}</div>
                                <div>{badge_html}</div>
                            </div>
                            <div style="font-size:0.80rem;color:#7ab8b2;margin-top:6px;">{sig.description}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            with c_p3:
                st.markdown(f"#### Operating Efficiency ({p.operating_efficiency_score}/2)")
                for sig in p.signals[7:]:
                    badge_html = (
                        '<span class="badge-pass"><span class="status-dot-pass"></span>PASS</span>'
                        if sig.passed
                        else '<span class="badge-fail"><span class="status-dot-fail"></span>FAIL</span>'
                    )
                    st.markdown(
                        f"""
                        <div class="diagnostic-card">
                            <div style="display:flex;justify-content:space-between;align-items:center;">
                                <div style="font-weight:600;font-size:0.85rem;color:#d4f0ec;">{sig.name}</div>
                                <div>{badge_html}</div>
                            </div>
                            <div style="font-size:0.80rem;color:#7ab8b2;margin-top:6px;">{sig.description}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.info("Piotroski signals require multi-period financial statements.")

    # ── Altman Z'' Tab ───────────────────────────────────────────────────────
    with tab_z:
        if company_check.altman_z:
            z = company_check.altman_z
            zone_color = GREEN if z.zone == DistressZone.SAFE else (YELLOW if z.zone == DistressZone.GREY else RED)
            st.markdown(f"### Altman Z''-Score: <span style='color:{zone_color};font-weight:700;'>{z.z_score}</span> ({z.zone.value})", unsafe_allow_html=True)
            st.write(z.interpretation)

            st.markdown("#### Formula Components & Weights (Emerging Markets Model)")
            st.caption("Z'' = 6.56*X1 + 3.26*X2 + 6.72*X3 + 1.05*X4")

            z_components = pd.DataFrame([
                {"Component": "X1: Working Capital / Assets", "Weight": "6.56x", "Ratio Value": f"{z.x1_working_capital_to_assets:.3f}", "Contribution": f"{6.56 * z.x1_working_capital_to_assets:.2f}"},
                {"Component": "X2: Retained Earnings / Assets", "Weight": "3.26x", "Ratio Value": f"{z.x2_retained_earnings_to_assets:.3f}", "Contribution": f"{3.26 * z.x2_retained_earnings_to_assets:.2f}"},
                {"Component": "X3: Operating EBIT / Assets", "Weight": "6.72x", "Ratio Value": f"{z.x3_ebit_to_assets:.3f}", "Contribution": f"{6.72 * z.x3_ebit_to_assets:.2f}"},
                {"Component": "X4: Book Equity / Total Liabilities", "Weight": "1.05x", "Ratio Value": f"{z.x4_equity_to_liabilities:.3f}", "Contribution": f"{1.05 * z.x4_equity_to_liabilities:.2f}"},
            ])
            st.dataframe(z_components, use_container_width=True, hide_index=True)

            # Visual Zones Gauge
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=z.z_score,
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, 6], 'tickcolor': TEXT},
                    'bar': {'color': zone_color},
                    'steps': [
                        {'range': [0, 1.10], 'color': "rgba(248, 81, 73, 0.3)"},
                        {'range': [1.10, 2.60], 'color': "rgba(210, 153, 34, 0.3)"},
                        {'range': [2.60, 6], 'color': "rgba(0, 196, 167, 0.3)"},
                    ],
                    'threshold': {
                        'line': {'color': TEXT, 'width': 3},
                        'thickness': 0.75,
                        'value': z.z_score,
                    }
                }
            ))
            fig_gauge.update_layout(
                paper_bgcolor=DARK_BG,
                plot_bgcolor=CARD_BG,
                font=dict(color=TEXT, family="Google Sans"),
                height=220,
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

    # ── DuPont 3-Stage Tab ───────────────────────────────────────────────────
    with tab_dupont:
        if company_check.dupont:
            d = company_check.dupont
            st.markdown(f"### DuPont ROE: **{d.roe:.1f}%**")
            st.markdown(
                f"""
                <div class="diagnostic-card">
                    <div style="color:#00c4a7;font-weight:700;">Primary Return Driver: {d.primary_driver}</div>
                    <div style="color:#d4f0ec;margin-top:4px;">{d.driver_narrative}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            d1, d2, d3, d4 = st.columns(4)
            d1.metric("ROE (%)", f"{d.roe:.1f}%")
            d2.metric("Net Margin (Pricing Power)", f"{d.net_profit_margin:.1f}%")
            d3.metric("Asset Turnover (Velocity)", f"{d.asset_turnover:.2f}x")
            d4.metric("Equity Multiplier (Leverage)", f"{d.equity_multiplier:.2f}x")

            dupont_df = pd.DataFrame({
                "DuPont Stage": ["1. Net Profit Margin", "2. Asset Turnover", "3. Equity Multiplier"],
                "Operational Meaning": ["Pricing Moat / Cost Efficiency", "Capital Velocity per Rupee of Assets", "Financial Leverage Multiplier"],
                "Metric Value": [f"{d.net_profit_margin:.1f}%", f"{d.asset_turnover:.2f}x", f"{d.equity_multiplier:.2f}x"],
            })
            st.dataframe(dupont_df, use_container_width=True, hide_index=True)

    # ── Valuation vs Sector Tab ──────────────────────────────────────────────
    with tab_val:
        if company_check.valuation:
            v = company_check.valuation
            st.markdown(f"### Valuation Posture: **{v.posture}**")

            val_metrics = pd.DataFrame([
                {"Multiple": "Price to Earnings (P/E)", "Company Multiple": f"{v.pe_ratio:.1f}x" if v.pe_ratio else "N/A", "Gap vs Sector Median": f"{v.pe_vs_sector_pct:+.1f}%" if v.pe_vs_sector_pct is not None else "N/A"},
                {"Multiple": "Price to Book (P/B)", "Company Multiple": f"{v.pb_ratio:.1f}x" if v.pb_ratio else "N/A", "Gap vs Sector Median": f"{v.pb_vs_sector_pct:+.1f}%" if v.pb_vs_sector_pct is not None else "N/A"},
                {"Multiple": "EV / EBITDA", "Company Multiple": f"{v.ev_ebitda:.1f}x" if v.ev_ebitda else "N/A", "Gap vs Sector Median": f"{v.ev_ebitda_vs_sector_pct:+.1f}%" if v.ev_ebitda_vs_sector_pct is not None else "N/A"},
                {"Multiple": "Free Cash Flow Yield", "Company Multiple": f"{v.fcf_yield_pct:.1f}%" if v.fcf_yield_pct else "N/A", "Gap vs Sector Median": "N/A"},
            ])
            st.dataframe(val_metrics, use_container_width=True, hide_index=True)

    # ── SWOT Diagnostic Tab ──────────────────────────────────────────────────
    with tab_swot:
        if result and result.ratio_scorecard_df is not None:
            comp_scorecard = result.ratio_scorecard_df[result.ratio_scorecard_df["ticker"] == selected_ticker]
            swot = get_report_gen().generate_swot(comp_scorecard, selected_ticker)

            sw1, sw2 = st.columns(2)
            with sw1:
                st.markdown("#### Strengths (Moats & Outperformance)")
                for s in swot.get("strengths", []):
                    st.success(f"**{s['ratio']}**: {s['narrative']}")

                st.markdown("#### Opportunities (Turnaround & Upside)")
                for o in swot.get("opportunities", []):
                    st.info(f"**{o['ratio']}**: {o['narrative']}")

            with sw2:
                st.markdown("#### Weaknesses (Underperformance vs Peers)")
                for w in swot.get("weaknesses", []):
                    st.warning(f"**{w['ratio']}**: {w['narrative']}")

                st.markdown("#### Threats (Solvency & Structural Risks)")
                for t in swot.get("threats", []):
                    st.error(f"**{t['ratio']}**: {t['narrative']}")


# ──────────────────────────────────────────────────────────────────────────────
# TAB 3: SECTOR LEADERBOARD & SCREENER
# ──────────────────────────────────────────────────────────────────────────────
def page_sector_screener(result: BenchmarkCoreResult):
    st.markdown("## Sector Fundamental Screener & AI Synthesis")
    st.caption("Filter and screen companies across fundamental health, Piotroski scores, Altman distress, and valuation multiples.")

    sector = st.session_state.selected_sector
    checks = st.session_state.sector_checks.get(sector, [])

    if not checks and result is not None:
        checks = compute_sector_health_suite(sector, result, st.session_state.parsed_data, st.session_state.market_info)
        st.session_state.sector_checks[sector] = checks

    if not checks:
        st.info("Run or load a sector benchmark to use the screener.")
        return

    # Screener Filters
    c_f1, c_f2, c_f3 = st.columns(3)
    verdict_filter = c_f1.multiselect("Filter Verdict:", ["PASS", "WATCH", "RED_FLAG"], default=["PASS", "WATCH", "RED_FLAG"])
    min_f_score = c_f2.slider("Min Piotroski F-Score:", 0, 9, 0)
    zone_filter = c_f3.multiselect("Distress Zone:", ["Safe Zone", "Grey Zone", "Distress Zone"], default=["Safe Zone", "Grey Zone", "Distress Zone"])

    # Filtered Records
    filtered = []
    for c in checks:
        if c.verdict.value not in verdict_filter:
            continue
        if c.piotroski and c.piotroski.score < min_f_score:
            continue
        if c.altman_z and c.altman_z.zone.value not in zone_filter:
            continue

        filtered.append({
            "Ticker": c.ticker,
            "Verdict": c.verdict.value,
            "Health Score": c.composite_health_score,
            "Piotroski F-Score": f"{c.piotroski.score}/9" if c.piotroski else "N/A",
            "Altman Z''": f"{c.altman_z.z_score} ({c.altman_z.zone.value})" if c.altman_z else "N/A",
            "DuPont ROE (%)": f"{c.dupont.roe:.1f}%" if c.dupont else "N/A",
            "Net Margin (%)": f"{c.dupont.net_profit_margin:.1f}%" if c.dupont else "N/A",
            "P/E": f"{c.valuation.pe_ratio:.1f}x" if c.valuation and c.valuation.pe_ratio else "N/A",
            "Valuation Posture": c.valuation.posture if c.valuation else "N/A",
        })

    df_screened = pd.DataFrame(filtered)
    if not df_screened.empty:
        df_screened = df_screened.sort_values(by="Health Score", ascending=False).reset_index(drop=True)
        df_screened.index = df_screened.index + 1
        df_screened.index.name = "Rank"

    st.markdown(f"### Screened Results ({len(df_screened)} of {len(checks)} companies)")
    st.dataframe(df_screened, use_container_width=True)

    st.divider()

    # AI Sector Synthesis
    st.markdown("### AI Executive Sector Synthesis")
    st.caption("Generate an institutional-grade fundamental brief synthesizing top quality picks, solvency cushions, and valuation dispersion.")

    keys = get_rotational_api_keys()
    if not keys:
        st.info("Add GEMINI_API_KEY to .env to unlock AI executive briefings.")
        return

    if st.button("Generate Sector Investment Briefing", type="primary"):
        with st.spinner("Synthesizing fundamental thesis via Gemini..."):
            try:
                ai = AIHandler(keys)
                pass_tickers = [c.ticker for c in checks if c.verdict == HealthVerdict.PASS]
                red_tickers = [c.ticker for c in checks if c.verdict == HealthVerdict.RED_FLAG]

                prompt = (
                    f"You are a Senior Equity Research Director covering Indian NSE equities. "
                    f"Provide an institutional investment brief for the {sector} sector.\n"
                    f"- High Quality PASS Companies: {', '.join(pass_tickers[:5])}\n"
                    f"- Watch / Elevated Risk Companies: {', '.join(red_tickers[:5])}\n"
                    f"Structure your briefing with:\n"
                    f"1. Executive Summary & Sector Operating Dynamics\n"
                    f"2. Top Fundamental Quality Picks (Capital Allocation & Margin Moats)\n"
                    f"3. Distress Risk & Solvency Warning Flags\n"
                    f"4. Valuation Posture & Sector Allocation Recommendation\n"
                    f"Keep it concise, rigorous, and professional. Avoid generic boilerplate."
                )

                response = ai.model.generate_content(prompt)
                text = ai._safe_extract_text(response)
                st.markdown(text)
            except Exception as e:
                st.error(f"AI generation failed: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# TAB 4: PEER BENCHMARKING & DISTRIBUTIONS
# ──────────────────────────────────────────────────────────────────────────────
def page_peer_benchmarking(result: BenchmarkCoreResult):
    st.markdown("## Peer Benchmarking & Outlier Analysis")
    st.caption("Statistical distributions, percentile curves, and outlier detection across peer companies.")

    peer_stats = result.peer_stats_df
    if peer_stats is None or peer_stats.empty:
        st.info("No peer statistics available.")
        return

    # Peer Stats Heatmap
    st.plotly_chart(plot_peer_stats_heatmap(peer_stats), use_container_width=True)

    # Boxplots & Outliers
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Ratio Scorecard Matrix")
        scorecard = result.ratio_scorecard_df
        tickers = scorecard["ticker"].unique().tolist()
        sel_t = st.selectbox("Select Company for Scorecard Radar:", tickers, key="sel_radar_tick")
        st.plotly_chart(plot_ratio_scorecard(scorecard, sel_t), use_container_width=True)

    with c2:
        st.markdown("### Multivariate Outliers")
        outliers = result.outlier_df
        if outliers is not None and not outliers.empty:
            st.plotly_chart(outlier_scatter(outliers), use_container_width=True)
        else:
            st.success("No extreme statistical outliers detected in peer group.")


# ──────────────────────────────────────────────────────────────────────────────
# TAB 5: AUDIT & EXPORT
# ──────────────────────────────────────────────────────────────────────────────
def page_audit_export(result: BenchmarkCoreResult):
    st.markdown("## Audit & Export Reports")
    st.caption("Download institutional Excel workbooks and audit data packages.")

    sector = st.session_state.selected_sector
    checks = st.session_state.sector_checks.get(sector, [])

    c_ex1, c_ex2 = st.columns(2)

    with c_ex1:
        st.markdown("### Excel Financial Health Report")
        st.caption("Multi-tab institutional workbook with scorecards, peer distributions, Altman Z, DuPont, and Piotroski checklists.")

        if st.button("Generate Excel Report", use_container_width=True):
            with st.spinner("Compiling workbook..."):
                rep_gen = get_report_gen()
                exp_df = rep_gen.explain_all(result.ratio_scorecard_df)
                excel_path = rep_gen.export_excel(
                    result.ratio_scorecard_df,
                    result.peer_stats_df,
                    result.outlier_df if result.outlier_df is not None else pd.DataFrame(),
                    result.pillar_summary_df,
                    exp_df,
                    sector=sector,
                )
                with open(excel_path, "rb") as f:
                    st.download_button(
                        "Download Excel File",
                        f.read(),
                        file_name=excel_path.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

    with c_ex2:
        st.markdown("### CSV Health Check Summary")
        st.caption("Download structured tabular data of all company health verdicts.")

        if checks:
            records = []
            for c in checks:
                records.append({
                    "ticker": c.ticker,
                    "sector": c.sector,
                    "verdict": c.verdict.value,
                    "composite_score": c.composite_health_score,
                    "piotroski_f_score": c.piotroski.score if c.piotroski else np.nan,
                    "altman_z_score": c.altman_z.z_score if c.altman_z else np.nan,
                    "altman_zone": c.altman_z.zone.value if c.altman_z else "",
                    "dupont_roe": c.dupont.roe if c.dupont else np.nan,
                    "dupont_net_margin": c.dupont.net_profit_margin if c.dupont else np.nan,
                    "dupont_asset_turnover": c.dupont.asset_turnover if c.dupont else np.nan,
                    "dupont_equity_multiplier": c.dupont.equity_multiplier if c.dupont else np.nan,
                    "dupont_primary_driver": c.dupont.primary_driver if c.dupont else "",
                    "valuation_posture": c.valuation.posture if c.valuation else "",
                })
            df_out = pd.DataFrame(records)
            csv_data = df_out.to_csv(index=False)
            st.download_button(
                "Download CSV Summary",
                csv_data,
                file_name=f"{sector}_health_summary.csv",
                mime="text/csv",
                use_container_width=True,
            )


# ──────────────────────────────────────────────────────────────────────────────
# MAIN APP ROUTER
# ──────────────────────────────────────────────────────────────────────────────
def main():
    inject_custom_css()
    sidebar_cfg = render_sidebar()

    tabs = st.tabs([
        "Sector Compass",
        "Company Health Diagnostics",
        "Sector Leaderboard & Screener",
        "Peer Benchmarking & Outliers",
        "Audit & Export",
    ])

    result = st.session_state.get("benchmark_result")

    # If result is not yet in session state, attempt to load cached sector on startup
    if result is None:
        store = get_benchmark_store()
        avail = store.list_available()
        target = sidebar_cfg["sector"]
        if target in avail or store._sector_slug(target) in [store._sector_slug(s) for s in avail]:
            load_cached_sector(target)
            result = st.session_state.get("benchmark_result")

    with tabs[0]:
        page_sector_compass()

    with tabs[1]:
        if result is not None:
            page_company_health(result)
        else:
            st.info("Build or load a sector benchmark to view company health diagnostics.")

    with tabs[2]:
        if result is not None:
            page_sector_screener(result)
        else:
            st.info("Build or load a sector benchmark to screen companies.")

    with tabs[3]:
        if result is not None:
            page_peer_benchmarking(result)
        else:
            st.info("Build or load a sector benchmark to view peer distributions.")

    with tabs[4]:
        if result is not None:
            page_audit_export(result)
        else:
            st.info("Build or load a sector benchmark to export reports.")


if __name__ == "__main__":
    main()