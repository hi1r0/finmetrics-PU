"""
health_models.py
================
Institutional-grade financial health and fundamental quality models:
1. Piotroski F-Score (9-point fundamental accounting quality test)
2. Altman Z''-Score (Emerging markets & non-financial corporate distress indicator)
3. DuPont 3-Stage Decomposition (Margin power vs. Asset turnover vs. Leverage)
4. Valuation Overlay vs. Sector Medians (P/E, P/B, EV/EBITDA, FCF Yield)
5. Plain-English Investment Health Verdict (PASS, WATCH, RED_FLAG)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import logging
import math
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class HealthVerdict(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    RED_FLAG = "RED_FLAG"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class DistressZone(str, Enum):
    SAFE = "Safe Zone"
    GREY = "Grey Zone"
    DISTRESS = "Distress Zone"
    UNKNOWN = "Unknown"


@dataclass
class PiotroskiSignal:
    name: str
    category: str
    passed: bool
    description: str
    metric_value: Optional[float] = None
    prior_value: Optional[float] = None


@dataclass
class PiotroskiResult:
    score: int  # 0 to 9
    rating: str  # "High Quality", "Moderate", "Weak"
    signals: List[PiotroskiSignal]
    profitability_score: int  # max 4
    leverage_liquidity_score: int  # max 3
    operating_efficiency_score: int  # max 2


@dataclass
class AltmanZResult:
    z_score: float
    zone: DistressZone
    x1_working_capital_to_assets: float
    x2_retained_earnings_to_assets: float
    x3_ebit_to_assets: float
    x4_equity_to_liabilities: float
    interpretation: str


@dataclass
class DuPontResult:
    roe: float
    net_profit_margin: float  # Margin driver (%)
    asset_turnover: float     # Turnover velocity (x)
    equity_multiplier: float  # Leverage multiplier (x)
    primary_driver: str       # "Margin Power", "Asset Velocity", "Financial Leverage"
    driver_narrative: str


@dataclass
class ValuationOverlayResult:
    pe_ratio: Optional[float]
    pb_ratio: Optional[float]
    ev_ebitda: Optional[float]
    fcf_yield_pct: Optional[float]
    pe_vs_sector_pct: Optional[float]
    pb_vs_sector_pct: Optional[float]
    ev_ebitda_vs_sector_pct: Optional[float]
    posture: str  # "Undervalued (Value)", "Fair Value", "Premium / Frothy", "Valuation Trap"


@dataclass
class CompanyHealthCheck:
    ticker: str
    sector: str
    verdict: HealthVerdict
    verdict_badge_color: str  # "green", "orange", "red", "gray"
    headline_rationale: str
    piotroski: Optional[PiotroskiResult]
    altman_z: Optional[AltmanZResult]
    dupont: Optional[DuPontResult]
    valuation: Optional[ValuationOverlayResult]
    composite_health_score: float  # 0 to 100 normalized score
    detailed_observations: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# 1. PIOTROSKI F-SCORE ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def compute_piotroski_f_score(
    income_curr: pd.Series,
    balance_curr: pd.Series,
    cashflow_curr: pd.Series,
    income_prev: Optional[pd.Series] = None,
    balance_prev: Optional[pd.Series] = None,
    cashflow_prev: Optional[pd.Series] = None,
) -> Optional[PiotroskiResult]:
    """
    Computes Joseph Piotroski's 9 fundamental accounting binary tests.
    Returns None if core financial statement data is unavailable.
    """
    try:
        # Extract Current Period Metrics
        net_inc = float(income_curr.get("net_income", 0.0) or 0.0)
        tot_rev = float(income_curr.get("total_revenue", 0.0) or 0.0)
        tot_assets = float(balance_curr.get("total_assets", 0.0) or 0.0)
        curr_assets = float(balance_curr.get("current_assets", 0.0) or 0.0)
        curr_liab = float(balance_curr.get("current_liabilities", 0.0) or 0.0)
        long_term_debt = float(balance_curr.get("long_term_debt", balance_curr.get("total_debt", 0.0)) or 0.0)
        shares_out = float(balance_curr.get("shares_outstanding", 0.0) or 0.0)
        gross_prof = float(income_curr.get("gross_profit", tot_rev - float(income_curr.get("cogs", 0.0) or 0.0)) or 0.0)
        cfo = float(cashflow_curr.get("operating_cashflow", 0.0) or 0.0)

        if tot_assets <= 0:
            return None

        roa_curr = (net_inc / tot_assets) * 100
        curr_ratio_curr = curr_assets / max(curr_liab, 1.0)
        gross_margin_curr = (gross_prof / max(tot_rev, 1.0)) * 100
        asset_turnover_curr = tot_rev / max(tot_assets, 1.0)

        # Extract Prior Period Metrics (with fallback defaults if single period)
        has_prior = income_prev is not None and balance_prev is not None
        tot_assets_prev = float(balance_prev.get("total_assets", tot_assets) or tot_assets) if has_prior else tot_assets
        net_inc_prev = float(income_prev.get("net_income", 0.0) or 0.0) if has_prior else 0.0
        tot_rev_prev = float(income_prev.get("total_revenue", 0.0) or tot_rev) if has_prior else tot_rev
        curr_assets_prev = float(balance_prev.get("current_assets", curr_assets) or curr_assets) if has_prior else curr_assets
        curr_liab_prev = float(balance_prev.get("current_liabilities", curr_liab) or curr_liab) if has_prior else curr_liab
        lt_debt_prev = float(balance_prev.get("long_term_debt", balance_prev.get("total_debt", long_term_debt)) or long_term_debt) if has_prior else long_term_debt
        shares_prev = float(balance_prev.get("shares_outstanding", shares_out) or shares_out) if has_prior else shares_out
        gross_prof_prev = float(income_prev.get("gross_profit", tot_rev_prev) or gross_prof) if has_prior else gross_prof

        roa_prev = (net_inc_prev / max(tot_assets_prev, 1.0)) * 100
        curr_ratio_prev = curr_assets_prev / max(curr_liab_prev, 1.0)
        gross_margin_prev = (gross_prof_prev / max(tot_rev_prev, 1.0)) * 100
        asset_turnover_prev = tot_rev_prev / max(tot_assets_prev, 1.0)

        signals: List[PiotroskiSignal] = []

        # ── Group 1: Profitability (4 points) ─────────────────────────────────
        # 1. Positive Net Income
        p1 = net_inc > 0
        signals.append(PiotroskiSignal("Positive Net Income", "Profitability", p1, "Net income is positive", net_inc))

        # 2. Positive Operating Cash Flow
        p2 = cfo > 0
        signals.append(PiotroskiSignal("Positive Operating Cash Flow", "Profitability", p2, "Cash from operations is positive", cfo))

        # 3. Higher ROA YoY
        p3 = roa_curr > roa_prev if has_prior else roa_curr > 0
        signals.append(PiotroskiSignal("ROA Expansion", "Profitability", p3, "Return on assets improved year-over-year", roa_curr, roa_prev))

        # 4. Cash Flow Quality (CFO > Net Income / Accruals)
        p4 = cfo > net_inc
        signals.append(PiotroskiSignal("Earnings Quality (CFO > PAT)", "Profitability", p4, "Operating cash flow exceeds net income (low accruals)", cfo, net_inc))

        # ── Group 2: Leverage, Liquidity & Source of Funds (3 points) ─────────
        # 5. Lower Leverage (Debt / Assets decreased)
        lev_curr = long_term_debt / max(tot_assets, 1.0)
        lev_prev = lt_debt_prev / max(tot_assets_prev, 1.0)
        p5 = lev_curr <= lev_prev if has_prior else lev_curr < 0.5
        signals.append(PiotroskiSignal("Debt Discipline", "Leverage & Liquidity", p5, "Long-term debt to assets did not increase", lev_curr, lev_prev))

        # 6. Higher Current Ratio
        p6 = curr_ratio_curr >= curr_ratio_prev if has_prior else curr_ratio_curr >= 1.2
        signals.append(PiotroskiSignal("Liquidity Buffer", "Leverage & Liquidity", p6, "Current ratio strengthened or remained healthy", curr_ratio_curr, curr_ratio_prev))

        # 7. No Share Dilution
        p7 = shares_out <= shares_prev * 1.01 if (has_prior and shares_out > 0 and shares_prev > 0) else True
        signals.append(PiotroskiSignal("No Equity Dilution", "Leverage & Liquidity", p7, "Shares outstanding did not expand significantly", shares_out, shares_prev))

        # ── Group 3: Operating Efficiency (2 points) ──────────────────────────
        # 8. Higher Gross Margin
        p8 = gross_margin_curr >= gross_margin_prev if has_prior else gross_margin_curr >= 20.0
        signals.append(PiotroskiSignal("Gross Margin Expansion", "Operating Efficiency", p8, "Gross margin improved or held firm", gross_margin_curr, gross_margin_prev))

        # 9. Higher Asset Turnover
        p9 = asset_turnover_curr >= asset_turnover_prev if has_prior else asset_turnover_curr >= 0.5
        signals.append(PiotroskiSignal("Asset Velocity", "Operating Efficiency", p9, "Asset turnover increased year-over-year", asset_turnover_curr, asset_turnover_prev))

        prof_score = sum(1 for s in signals[:4] if s.passed)
        lev_score = sum(1 for s in signals[4:7] if s.passed)
        eff_score = sum(1 for s in signals[7:] if s.passed)
        total_score = prof_score + lev_score + eff_score

        if total_score >= 8:
            rating = "High Quality (Tier 1)"
        elif total_score >= 5:
            rating = "Moderate Quality"
        else:
            rating = "Weak / Low Quality"

        return PiotroskiResult(
            score=total_score,
            rating=rating,
            signals=signals,
            profitability_score=prof_score,
            leverage_liquidity_score=lev_score,
            operating_efficiency_score=eff_score,
        )
    except Exception as exc:
        logger.warning("Piotroski computation error: %s", exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 2. ALTMAN Z''-SCORE ENGINE (Emerging Markets & Non-Financials)
# ─────────────────────────────────────────────────────────────────────────────
def compute_altman_z_score(
    balance: pd.Series,
    income: pd.Series,
) -> Optional[AltmanZResult]:
    """
    Computes the Edward Altman Z''-score for emerging markets and non-financials:
      Z'' = 6.56*X1 + 3.26*X2 + 6.72*X3 + 1.05*X4
    Zones:
      Z'' > 2.60 : Safe Zone
      1.10 <= Z'' <= 2.60 : Grey Zone
      Z'' < 1.10 : Distress Zone
    """
    try:
        # Gracefully handle parameter order if caller passed (income, balance)
        if "total_assets" not in balance and "total_assets" in income:
            balance, income = income, balance

        tot_assets = float(balance.get("total_assets", 0.0) or 0.0)
        curr_assets = float(balance.get("current_assets", 0.0) or 0.0)
        curr_liab = float(balance.get("current_liabilities", 0.0) or 0.0)
        tot_equity = float(balance.get("total_equity", balance.get("stockholders_equity", 0.0)) or 0.0)
        tot_liab = float(balance.get("total_liabilities", tot_assets - tot_equity) or (tot_assets - tot_equity))
        retained_earnings = float(balance.get("retained_earnings", tot_equity * 0.5) or (tot_equity * 0.5))
        ebit = float(income.get("operating_income", income.get("ebit", 0.0)) or 0.0)

        if tot_assets <= 0:
            return None

        # Components
        working_capital = curr_assets - curr_liab
        x1 = working_capital / tot_assets
        x2 = retained_earnings / tot_assets
        x3 = ebit / tot_assets
        x4 = tot_equity / max(tot_liab, 1.0)

        z_score = round(6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4, 2)

        if z_score > 2.60:
            zone = DistressZone.SAFE
            interpretation = "Robust solvency buffer; low statistical probability of financial distress."
        elif z_score >= 1.10:
            zone = DistressZone.GREY
            interpretation = "Moderate financial posture; requires active monitoring of working capital & leverage."
        else:
            zone = DistressZone.DISTRESS
            interpretation = "Elevated distress risk; thin working capital buffer and high leverage exposure."

        return AltmanZResult(
            z_score=z_score,
            zone=zone,
            x1_working_capital_to_assets=round(x1, 3),
            x2_retained_earnings_to_assets=round(x2, 3),
            x3_ebit_to_assets=round(x3, 3),
            x4_equity_to_liabilities=round(x4, 3),
            interpretation=interpretation,
        )
    except Exception as exc:
        logger.warning("Altman Z'' computation error: %s", exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 3. DUPONT 3-STAGE ROE DECOMPOSITION
# ─────────────────────────────────────────────────────────────────────────────
def compute_dupont_decomposition(
    income: pd.Series,
    balance: pd.Series,
) -> Optional[DuPontResult]:
    """
    Decomposes Return on Equity (ROE) into 3 multiplicative components:
      ROE = Net Margin (%) * Asset Turnover (x) * Equity Multiplier (x)
    Identifies whether returns stem from Pricing Moat, Velocity, or Debt Leverage.
    """
    try:
        net_inc = float(income.get("net_income", 0.0) or 0.0)
        tot_rev = float(income.get("total_revenue", 0.0) or 0.0)
        tot_assets = float(balance.get("total_assets", 0.0) or 0.0)
        tot_equity = float(balance.get("total_equity", balance.get("stockholders_equity", 0.0)) or 0.0)

        if tot_rev <= 0 or tot_assets <= 0 or tot_equity <= 0:
            return None

        net_margin = (net_inc / tot_rev) * 100
        asset_turnover = tot_rev / tot_assets
        equity_mult = tot_assets / tot_equity
        roe = (net_inc / tot_equity) * 100

        # Diagnose Primary Driver
        if net_margin >= 18.0:
            driver = "Margin Power (Pricing Moat)"
            narrative = f"ROE of {roe:.1f}% is driven primarily by exceptional profit margins ({net_margin:.1f}%), indicating strong customer pricing power."
        elif asset_turnover >= 1.2:
            driver = "Asset Velocity (Capital Efficiency)"
            narrative = f"ROE of {roe:.1f}% is propelled by high asset velocity ({asset_turnover:.2f}x turnover), maximizing revenue per rupee of balance sheet."
        elif equity_mult >= 2.5:
            driver = "Financial Leverage (Gearing Dependent)"
            narrative = f"ROE of {roe:.1f}% is heavily magnified by balance sheet leverage (equity multiplier {equity_mult:.2f}x); watch sensitivity to interest cycles."
        else:
            driver = "Balanced Operational Model"
            narrative = f"ROE of {roe:.1f}% reflects a balanced mix of margin ({net_margin:.1f}%) and moderate asset turnover ({asset_turnover:.2f}x)."

        return DuPontResult(
            roe=round(roe, 2),
            net_profit_margin=round(net_margin, 2),
            asset_turnover=round(asset_turnover, 2),
            equity_multiplier=round(equity_mult, 2),
            primary_driver=driver,
            driver_narrative=narrative,
        )
    except Exception as exc:
        logger.warning("DuPont computation error: %s", exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 4. VALUATION OVERLAY VS SECTOR MEDIANS
# ─────────────────────────────────────────────────────────────────────────────
def compute_valuation_overlay(
    market_info: Dict[str, Any],
    ratios: Dict[str, float],
    sector_medians: Dict[str, float],
    piotroski_score: Optional[int] = None,
    altman_zone: Optional[DistressZone] = None,
) -> ValuationOverlayResult:
    """
    Compares company valuation multiples against sector benchmarks.
    Classifies posture (Deep Value, Fair Value, Premium, or Valuation Trap).
    """
    pe = market_info.get("pe_ratio") or ratios.get("pe_ratio")
    pb = market_info.get("pb_ratio") or ratios.get("pb_ratio")
    ev_ebitda = market_info.get("ev_ebitda") or ratios.get("ev_ebitda")
    fcf_yield = ratios.get("fcf_yield")

    sec_pe = sector_medians.get("pe_ratio")
    sec_pb = sector_medians.get("pb_ratio")
    sec_ev = sector_medians.get("ev_ebitda")

    pe_gap = ((pe - sec_pe) / sec_pe * 100) if (pe and sec_pe and sec_pe > 0) else None
    pb_gap = ((pb - sec_pb) / sec_pb * 100) if (pb and sec_pb and sec_pb > 0) else None
    ev_gap = ((ev_ebitda - sec_ev) / sec_ev * 100) if (ev_ebitda and sec_ev and sec_ev > 0) else None

    # Classify Valuation Posture
    is_distressed = (altman_zone == DistressZone.DISTRESS) or (piotroski_score is not None and piotroski_score <= 3)
    is_high_quality = (piotroski_score is not None and piotroski_score >= 7) and (altman_zone != DistressZone.DISTRESS)

    if pe_gap is not None and pe_gap <= -25.0:
        if is_distressed:
            posture = "Valuation Trap (Cheap but Distressed)"
        elif is_high_quality:
            posture = "Deep Value (Quality at a Discount)"
        else:
            posture = "Undervalued vs Peers"
    elif pe_gap is not None and pe_gap >= 35.0:
        posture = "Frothy Valuation (Substantial Premium)"
    elif pe_gap is not None and pe_gap >= 15.0:
        posture = "Quality Premium"
    elif pe_gap is not None:
        posture = "Fairly Valued"
    else:
        posture = "Multiples Inconclusive"

    return ValuationOverlayResult(
        pe_ratio=round(pe, 2) if pe else None,
        pb_ratio=round(pb, 2) if pb else None,
        ev_ebitda=round(ev_ebitda, 2) if ev_ebitda else None,
        fcf_yield_pct=round(fcf_yield, 2) if fcf_yield else None,
        pe_vs_sector_pct=round(pe_gap, 1) if pe_gap is not None else None,
        pb_vs_sector_pct=round(pb_gap, 1) if pb_gap is not None else None,
        ev_ebitda_vs_sector_pct=round(ev_gap, 1) if ev_gap is not None else None,
        posture=posture,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 5. CONSOLIDATED COMPANY HEALTH SYNTHESIS
# ─────────────────────────────────────────────────────────────────────────────
def evaluate_company_health(
    ticker: str,
    sector: str,
    ratios: Dict[str, float],
    fundamental_composite: float,
    piotroski: Optional[PiotroskiResult],
    altman_z: Optional[AltmanZResult],
    dupont: Optional[DuPontResult],
    valuation: Optional[ValuationOverlayResult],
) -> CompanyHealthCheck:
    """
    Synthesizes fundamental scorecard, Piotroski F-Score, Altman Z'', DuPont, and Valuation
    into an actionable investment diagnostic (PASS / WATCH / RED_FLAG).
    """
    observations: List[str] = []
    red_flag_triggers = 0
    watch_triggers = 0
    positive_drivers = 0

    # 1. Altman Distress Evaluation
    if altman_z:
        if altman_z.zone == DistressZone.DISTRESS:
            red_flag_triggers += 2
            observations.append(f"CRITICAL: Altman Z'' of {altman_z.z_score} indicates balance sheet distress risk.")
        elif altman_z.zone == DistressZone.GREY:
            watch_triggers += 1
            observations.append(f"CAUTION: Altman Z'' of {altman_z.z_score} falls in Grey Zone (watch debt coverage).")
        else:
            positive_drivers += 1
            observations.append(f"SOLVENCY: Altman Z'' of {altman_z.z_score} confirms robust solvency cushion.")

    # 2. Piotroski Quality Evaluation
    if piotroski:
        if piotroski.score <= 3:
            red_flag_triggers += 2
            observations.append(f"QUALITY ALERT: Low Piotroski F-score ({piotroski.score}/9) indicates deteriorating operating health.")
        elif piotroski.score <= 5:
            watch_triggers += 1
            observations.append(f"Moderate Piotroski score ({piotroski.score}/9); check cash conversion and margin stability.")
        elif piotroski.score >= 8:
            positive_drivers += 2
            observations.append(f"EXCEPTIONAL: Piotroski F-score of {piotroski.score}/9 demonstrates top-tier fundamental execution.")
        else:
            positive_drivers += 1

    # 3. DuPont Margin vs Leverage
    if dupont:
        if dupont.equity_multiplier > 3.5:
            watch_triggers += 1
            observations.append(f"LEVERAGE: ROE is significantly geared by {dupont.equity_multiplier:.1f}x equity multiplier.")
        if dupont.net_profit_margin > 15.0:
            positive_drivers += 1
            observations.append(f"PRICING POWER: High net margin of {dupont.net_profit_margin:.1f}% underpins returns.")

    # 4. Valuation Context
    if valuation and valuation.posture == "Valuation Trap (Cheap but Distressed)":
        red_flag_triggers += 1
        observations.append("VALUE TRAP: Discounted multiples mask fundamental deterioration.")
    elif valuation and valuation.posture == "Frothy Valuation (Substantial Premium)":
        watch_triggers += 1
        observations.append(f"VALUATION: Trades at {valuation.pe_vs_sector_pct:+.1f}% premium to sector peers.")
    elif valuation and valuation.posture == "Deep Value (Quality at a Discount)":
        positive_drivers += 2
        observations.append(f"ATTRACTIVE: High fundamental quality trading at {valuation.pe_vs_sector_pct:+.1f}% sector discount.")

    # Determine Verdict
    if red_flag_triggers >= 2 or fundamental_composite < 40.0:
        verdict = HealthVerdict.RED_FLAG
        badge_color = "red"
        headline = "Elevated fundamental distress or deteriorating financial quality."
    elif watch_triggers >= 2 or fundamental_composite < 60.0 or (valuation and "Frothy" in valuation.posture):
        verdict = HealthVerdict.WATCH
        badge_color = "orange"
        headline = "Mixed financial profile; monitor leverage, valuation premium, or working capital."
    else:
        verdict = HealthVerdict.PASS
        badge_color = "green"
        headline = "Strong fundamental health across solvency, earnings quality, and cash generation."

    return CompanyHealthCheck(
        ticker=ticker,
        sector=sector,
        verdict=verdict,
        verdict_badge_color=badge_color,
        headline_rationale=headline,
        piotroski=piotroski,
        altman_z=altman_z,
        dupont=dupont,
        valuation=valuation,
        composite_health_score=round(fundamental_composite, 1),
        detailed_observations=observations,
    )
