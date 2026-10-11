"""
test_sector_compass.py
======================
Unit tests for Sector Compass Aggregation, Attractiveness Ranking, and Sector Profiles.
"""

import pandas as pd
import pytest

from modules.health_models import (
    CompanyHealthCheck,
    HealthVerdict,
    DistressZone,
    AltmanZResult,
    PiotroskiResult,
)
from modules.sector_compass import SectorCompassEngine, SectorCompassSummary
from modules.sector_profiles import get_sector_profile, SECTOR_PROFILES


def test_sector_profiles_registry():
    """Verify registered sector profiles for the 5 target sectors."""
    assert len(SECTOR_PROFILES) >= 5
    for key in ["it", "fmcg", "pharma", "auto", "metals"]:
        profile = get_sector_profile(key)
        assert profile is not None
        assert profile.name != ""
        assert profile.archetype != ""
        assert len(profile.pillars) > 0
        assert sum(profile.pillar_weights.values()) == pytest.approx(1.0, abs=1e-4)


def test_sector_compass_evaluation_and_ranking():
    """Verify Sector Compass evaluation and relative attractiveness leaderboard."""
    # Create mock checks for Sector A (high health)
    checks_a = [
        CompanyHealthCheck(
            ticker=f"A_{i}",
            sector="Sector A",
            verdict=HealthVerdict.PASS,
            verdict_badge_color="green",
            headline_rationale="Solid",
            piotroski=PiotroskiResult(score=8, rating="High", signals=[], profitability_score=4, leverage_liquidity_score=2, operating_efficiency_score=2),
            altman_z=AltmanZResult(z_score=3.5, zone=DistressZone.SAFE, x1_working_capital_to_assets=0.3, x2_retained_earnings_to_assets=0.4, x3_ebit_to_assets=0.2, x4_equity_to_liabilities=2.0, interpretation="Safe"),
            dupont=None,
            valuation=None,
            composite_health_score=85.0,
            detailed_observations=[],
        )
        for i in range(5)
    ]

    # Create mock checks for Sector B (lower health, higher distress)
    checks_b = [
        CompanyHealthCheck(
            ticker=f"B_{i}",
            sector="Sector B",
            verdict=HealthVerdict.RED_FLAG if i < 3 else HealthVerdict.WATCH,
            verdict_badge_color="red",
            headline_rationale="Weak",
            piotroski=PiotroskiResult(score=3, rating="Weak", signals=[], profitability_score=1, leverage_liquidity_score=1, operating_efficiency_score=1),
            altman_z=AltmanZResult(z_score=0.9, zone=DistressZone.DISTRESS, x1_working_capital_to_assets=-0.1, x2_retained_earnings_to_assets=-0.1, x3_ebit_to_assets=0.01, x4_equity_to_liabilities=0.2, interpretation="Distress"),
            dupont=None,
            valuation=None,
            composite_health_score=40.0,
            detailed_observations=[],
        )
        for i in range(5)
    ]

    summary_a = SectorCompassEngine.evaluate_sector("Sector A", "Archetype A", checks_a)
    summary_b = SectorCompassEngine.evaluate_sector("Sector B", "Archetype B", checks_b)

    assert summary_a is not None
    assert summary_b is not None
    assert summary_a.attractiveness_score > summary_b.attractiveness_score
    assert summary_a.sector_breadth_pct == 100.0
    assert summary_b.distress_risk_pct == 100.0

    # Leaderboard table
    leaderboard = SectorCompassEngine.rank_sectors([summary_a, summary_b])
    assert len(leaderboard) == 2
    assert leaderboard.iloc[0]["Sector"] == "Sector A"
    assert leaderboard.iloc[1]["Sector"] == "Sector B"
