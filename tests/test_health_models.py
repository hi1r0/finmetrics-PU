"""
test_health_models.py
=====================
Unit tests for the Institutional Health & Fundamental Diagnostics models:
- Piotroski F-Score (9 points)
- Altman Z''-Score (Emerging Market non-financial distress)
- DuPont 3-Stage ROE Decomposition
- Valuation Overlay vs Sector Medians
- Consolidated Company Health Synthesis (PASS / WATCH / RED_FLAG)
"""

import pandas as pd
import pytest

from modules.health_models import (
    compute_piotroski_f_score,
    compute_altman_z_score,
    compute_dupont_decomposition,
    compute_valuation_overlay,
    evaluate_company_health,
    HealthVerdict,
    DistressZone,
)


def test_piotroski_f_score_high_quality():
    """Verify that a stellar financial profile receives high Piotroski F-Score."""
    income_curr = pd.Series({
        "net_income": 1000.0,
        "total_revenue": 5000.0,
        "gross_profit": 2500.0,
    })
    balance_curr = pd.Series({
        "total_assets": 10000.0,
        "current_assets": 4000.0,
        "current_liabilities": 2000.0,
        "long_term_debt": 1000.0,
        "shares_outstanding": 100.0,
    })
    cashflow_curr = pd.Series({
        "operating_cashflow": 1200.0,  # CFO > PAT
    })

    # Prior year had slightly lower performance
    income_prev = pd.Series({
        "net_income": 800.0,
        "total_revenue": 4500.0,
        "gross_profit": 2000.0,
    })
    balance_prev = pd.Series({
        "total_assets": 9500.0,
        "current_assets": 3500.0,
        "current_liabilities": 2000.0,
        "long_term_debt": 1200.0,  # debt decreased
        "shares_outstanding": 100.0,
    })

    res = compute_piotroski_f_score(
        income_curr=income_curr,
        balance_curr=balance_curr,
        cashflow_curr=cashflow_curr,
        income_prev=income_prev,
        balance_prev=balance_prev,
    )

    assert res is not None
    assert res.score == 9
    assert res.rating == "High Quality (Tier 1)"
    assert res.profitability_score == 4
    assert res.leverage_liquidity_score == 3
    assert res.operating_efficiency_score == 2
    assert len(res.signals) == 9
    assert all(s.passed for s in res.signals)


def test_piotroski_f_score_distressed():
    """Verify that an unprofitable, deteriorating firm receives low score."""
    income_curr = pd.Series({
        "net_income": -500.0,
        "total_revenue": 3000.0,
        "gross_profit": 300.0,
    })
    balance_curr = pd.Series({
        "total_assets": 8000.0,
        "current_assets": 1000.0,
        "current_liabilities": 2500.0,
        "long_term_debt": 5000.0,
        "shares_outstanding": 150.0,  # diluted from 100
    })
    cashflow_curr = pd.Series({
        "operating_cashflow": -600.0,
    })

    income_prev = pd.Series({
        "net_income": 200.0,
        "total_revenue": 3500.0,
        "gross_profit": 700.0,
    })
    balance_prev = pd.Series({
        "total_assets": 8000.0,
        "current_assets": 1500.0,
        "current_liabilities": 2000.0,
        "long_term_debt": 3000.0,
        "shares_outstanding": 100.0,
    })

    res = compute_piotroski_f_score(
        income_curr=income_curr,
        balance_curr=balance_curr,
        cashflow_curr=cashflow_curr,
        income_prev=income_prev,
        balance_prev=balance_prev,
    )

    assert res is not None
    assert res.score <= 2
    assert res.rating == "Weak / Low Quality"


def test_piotroski_missing_assets():
    """Verify graceful handling when total_assets is 0 or negative."""
    res = compute_piotroski_f_score(
        pd.Series({"net_income": 100}),
        pd.Series({"total_assets": 0}),
        pd.Series({"operating_cashflow": 100}),
    )
    assert res is None


def test_altman_z_score_safe_and_distress():
    """Verify Altman Z'' Emerging Markets formula and zone classifications."""
    # Robust safe firm
    safe_balance = pd.Series({
        "total_assets": 10000.0,
        "current_assets": 5000.0,
        "current_liabilities": 2000.0,  # WC = 3000 -> X1 = 0.3
        "total_equity": 7000.0,         # Liab = 3000 -> X4 = 2.33
        "retained_earnings": 4000.0,    # X2 = 0.4
    })
    safe_income = pd.Series({
        "operating_income": 1500.0,     # X3 = 0.15
    })

    safe_res = compute_altman_z_score(safe_income, safe_balance)
    assert safe_res is not None
    assert safe_res.zone == DistressZone.SAFE
    assert safe_res.z_score > 2.60

    # Distressed firm
    distress_balance = pd.Series({
        "total_assets": 10000.0,
        "current_assets": 1000.0,
        "current_liabilities": 3000.0,  # WC = -2000 -> X1 = -0.2
        "total_equity": 1000.0,         # Liab = 9000 -> X4 = 0.11
        "retained_earnings": -1000.0,   # X2 = -0.1
    })
    distress_income = pd.Series({
        "operating_income": -200.0,     # X3 = -0.02
    })

    dist_res = compute_altman_z_score(distress_income, distress_balance)
    assert dist_res is not None
    assert dist_res.zone == DistressZone.DISTRESS
    assert dist_res.z_score < 1.10


def test_dupont_decomposition_math_and_driver():
    """Verify DuPont 3-stage identity: ROE = Net Margin * Asset Turnover * Equity Multiplier."""
    income = pd.Series({
        "total_revenue": 10000.0,
        "net_income": 2000.0,  # Net margin = 20%
    })
    balance = pd.Series({
        "total_assets": 8000.0,  # Asset turnover = 1.25x
        "total_equity": 4000.0,  # Equity mult = 2.0x
    })

    res = compute_dupont_decomposition(income, balance)
    assert res is not None
    assert res.net_profit_margin == 20.0
    assert res.asset_turnover == 1.25
    assert res.equity_multiplier == 2.0
    # 20% * 1.25 * 2.0 = 50.0% ROE
    assert res.roe == 50.0
    assert "Margin Power" in res.primary_driver


def test_valuation_overlay_posture():
    """Verify valuation classification including Value Trap and Frothy valuations."""
    sector_medians = {"pe_ratio": 30.0, "pb_ratio": 4.0, "ev_ebitda": 18.0}

    # Value Trap: Cheap P/E (-40%), but distressed Altman Z
    trap_res = compute_valuation_overlay(
        market_info={"pe_ratio": 15.0, "pb_ratio": 2.0, "ev_ebitda": 8.0},
        ratios={},
        sector_medians=sector_medians,
        piotroski_score=2,
        altman_zone=DistressZone.DISTRESS,
    )
    assert "Valuation Trap" in trap_res.posture

    # Quality Discount: Cheap P/E (-40%) with pristine Piotroski 8
    quality_res = compute_valuation_overlay(
        market_info={"pe_ratio": 18.0, "pb_ratio": 2.5, "ev_ebitda": 10.0},
        ratios={},
        sector_medians=sector_medians,
        piotroski_score=8,
        altman_zone=DistressZone.SAFE,
    )
    assert "Deep Value" in quality_res.posture

    # Frothy: +50% P/E above sector
    frothy_res = compute_valuation_overlay(
        market_info={"pe_ratio": 45.0, "pb_ratio": 6.0, "ev_ebitda": 25.0},
        ratios={},
        sector_medians=sector_medians,
        piotroski_score=6,
        altman_zone=DistressZone.SAFE,
    )
    assert "Frothy" in frothy_res.posture


def test_evaluate_company_health_verdict():
    """Verify consolidated diagnosis assigns PASS, WATCH, or RED_FLAG appropriately."""
    # Strong company -> PASS
    check_pass = evaluate_company_health(
        ticker="TCS.NS",
        sector="Information Technology",
        ratios={"pe_ratio": 28.0},
        fundamental_composite=85.0,
        piotroski=compute_piotroski_f_score(
            pd.Series({"net_income": 100, "total_revenue": 500, "gross_profit": 300}),
            pd.Series({"total_assets": 1000, "current_assets": 600, "current_liabilities": 200, "long_term_debt": 0, "shares_outstanding": 100}),
            pd.Series({"operating_cashflow": 120}),
        ),
        altman_z=compute_altman_z_score(
            pd.Series({"operating_income": 120}),
            pd.Series({"total_assets": 1000, "current_assets": 600, "current_liabilities": 200, "total_equity": 800}),
        ),
        dupont=compute_dupont_decomposition(
            pd.Series({"total_revenue": 500, "net_income": 100}),
            pd.Series({"total_assets": 1000, "total_equity": 800}),
        ),
        valuation=None,
    )
    assert check_pass.verdict == HealthVerdict.PASS
    assert check_pass.verdict_badge_color == "green"
    assert len(check_pass.detailed_observations) > 0

    # Distressed company -> RED_FLAG
    check_fail = evaluate_company_health(
        ticker="DISTRESS.NS",
        sector="Metals & Mining",
        ratios={"pe_ratio": 8.0},
        fundamental_composite=32.0,
        piotroski=None,
        altman_z=compute_altman_z_score(
            pd.Series({"operating_income": -50}),
            pd.Series({"total_assets": 1000, "current_assets": 100, "current_liabilities": 400, "total_equity": 100}),
        ),
        dupont=None,
        valuation=None,
    )
    assert check_fail.verdict == HealthVerdict.RED_FLAG
    assert check_fail.verdict_badge_color == "red"
