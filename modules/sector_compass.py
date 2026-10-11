"""
sector_compass.py
=================
Aggregates cross-sector fundamental health, valuation posture, and market breadth
to generate the Macro Sector Compass — guiding sector allocation and relative value decisions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from modules.health_models import CompanyHealthCheck, HealthVerdict, DistressZone


@dataclass
class SectorCompassSummary:
    sector_name: str
    archetype: str
    total_companies: int
    median_composite_score: float
    sector_breadth_pct: float       # % of companies with solid health (Pass/Watch with F-score >= 6)
    distress_risk_pct: float        # % of companies in Altman Z'' Distress Zone
    median_pe: Optional[float]
    median_ev_ebitda: Optional[float]
    median_roe: Optional[float]
    earnings_quality_pct: float     # % of companies with positive cash flow exceeding net income
    attractiveness_score: float     # 0 to 100 composite ranking
    attractiveness_tier: str        # "Top Overweight", "Neutral / Balanced", "Cautious Underweight"
    key_drivers: List[str] = field(default_factory=list)


class SectorCompassEngine:
    """
    Evaluates and ranks sectors across fundamental health, valuation buffers, and financial breadth.
    """

    @staticmethod
    def evaluate_sector(
        sector_name: str,
        archetype: str,
        health_checks: List[CompanyHealthCheck],
    ) -> Optional[SectorCompassSummary]:
        """
        Synthesizes company health checks within a sector into a sector-level compass profile.
        """
        if not health_checks:
            return None

        n = len(health_checks)
        composite_scores = [h.composite_health_score for h in health_checks if not np.isnan(h.composite_health_score)]
        median_composite = float(np.median(composite_scores)) if composite_scores else 50.0

        # Breadth: % of companies with F-score >= 6 or verdict PASS
        healthy_count = sum(
            1 for h in health_checks
            if h.verdict == HealthVerdict.PASS or (h.piotroski and h.piotroski.score >= 6)
        )
        breadth_pct = round((healthy_count / n) * 100, 1)

        # Distress risk: % in Altman Distress Zone
        distress_count = sum(
            1 for h in health_checks
            if h.altman_z and h.altman_z.zone == DistressZone.DISTRESS
        )
        distress_pct = round((distress_count / n) * 100, 1)

        # Cash Flow Quality: CFO > PAT
        cfo_pat_count = sum(
            1 for h in health_checks
            if h.piotroski and any(s.name == "Earnings Quality (CFO > PAT)" and s.passed for s in h.piotroski.signals)
        )
        cfo_pat_pct = round((cfo_pat_count / max(n, 1)) * 100, 1)

        # Valuation Medians
        pe_list = [h.valuation.pe_ratio for h in health_checks if h.valuation and h.valuation.pe_ratio and h.valuation.pe_ratio > 0]
        ev_list = [h.valuation.ev_ebitda for h in health_checks if h.valuation and h.valuation.ev_ebitda and h.valuation.ev_ebitda > 0]
        roe_list = [h.dupont.roe for h in health_checks if h.dupont and not np.isnan(h.dupont.roe)]

        median_pe = round(float(np.median(pe_list)), 1) if pe_list else None
        median_ev = round(float(np.median(ev_list)), 1) if ev_list else None
        median_roe = round(float(np.median(roe_list)), 1) if roe_list else None

        # Attractiveness Index (0 to 100)
        # Weights: Fundamental Score (40%), Breadth (30%), Distress Avoidance (20%), Cash Quality (10%)
        distress_buffer_score = max(0.0, 100.0 - distress_pct * 2)
        attractiveness = (
            0.40 * median_composite
            + 0.30 * breadth_pct
            + 0.20 * distress_buffer_score
            + 0.10 * cfo_pat_pct
        )
        attractiveness = round(attractiveness, 1)

        if attractiveness >= 75.0 and distress_pct <= 10.0:
            tier = "Prime Quality / Overweight"
        elif attractiveness >= 60.0:
            tier = "Neutral / Selective Quality"
        else:
            tier = "Defensive / High Dispersion"

        drivers = [
            f"Median Health Score: {median_composite:.1f}/100",
            f"Sector Quality Breadth: {breadth_pct:.1f}% healthy",
            f"Distress Exposure: {distress_pct:.1f}%",
        ]
        if median_pe:
            drivers.append(f"Median P/E: {median_pe:.1f}x")

        return SectorCompassSummary(
            sector_name=sector_name,
            archetype=archetype,
            total_companies=n,
            median_composite_score=median_composite,
            sector_breadth_pct=breadth_pct,
            distress_risk_pct=distress_pct,
            median_pe=median_pe,
            median_ev_ebitda=median_ev,
            median_roe=median_roe,
            earnings_quality_pct=cfo_pat_pct,
            attractiveness_score=attractiveness,
            attractiveness_tier=tier,
            key_drivers=drivers,
        )

    @classmethod
    def rank_sectors(
        cls,
        sector_summaries: List[SectorCompassSummary],
    ) -> pd.DataFrame:
        """Produces ranked leaderboard table across sectors."""
        records = []
        for s in sector_summaries:
            records.append({
                "Sector": s.sector_name,
                "Archetype": s.archetype,
                "Companies": s.total_companies,
                "Attractiveness Score": s.attractiveness_score,
                "Posture": s.attractiveness_tier,
                "Median Health": s.median_composite_score,
                "Quality Breadth (%)": f"{s.sector_breadth_pct:.1f}%",
                "Distress Risk (%)": f"{s.distress_risk_pct:.1f}%",
                "Median P/E": f"{s.median_pe:.1f}x" if s.median_pe else "N/A",
                "Median ROE": f"{s.median_roe:.1f}%" if s.median_roe else "N/A",
                "CFO > PAT (%)": f"{s.earnings_quality_pct:.1f}%",
            })
        df = pd.DataFrame(records)
        if not df.empty:
            df = df.sort_values(by="Attractiveness Score", ascending=False).reset_index(drop=True)
            df.index = df.index + 1  # 1-based rank
            df.index.name = "Rank"
        return df
