"""
sector_profiles.py
==================
Defines specialized fundamental scoring recipes and ratio weights tailored to
specific NSE sector operating models (e.g. asset-light IT vs. capital-intensive Metals).
Eliminates one-size-fits-all scoring distortions across diverse industry structures.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class SectorProfile:
    """
    Configuration specification for sector-tailored fundamental scoring.
    """
    name: str
    archetype: str
    description: str
    pillars: Dict[str, List[Tuple[str, float, bool]]]  # (ratio_name, weight, higher_is_better)
    pillar_weights: Dict[str, float]
    valuation_benchmark_metric: str  # Primary valuation anchor (e.g. 'pe' vs 'ev_ebitda')
    min_data_coverage_pct: float = 0.60
    key_focus_ratios: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# 1. INFORMATION TECHNOLOGY (Asset-Light, ROCE & FCF Driven)
# ─────────────────────────────────────────────────────────────────────────────
IT_PROFILE = SectorProfile(
    name="Information Technology",
    archetype="Asset-Light Human Capital",
    description="High cash conversion, negative net debt, premium ROCE, zero working capital drag.",
    pillars={
        "Profitability": [
            ("operating_margin", 0.35, True),
            ("net_margin",       0.25, True),
            ("roe",              0.20, True),
            ("roce",             0.20, True),
        ],
        "Cash Generation": [
            ("fcf_margin",        0.50, True),
            ("cash_ratio",        0.30, True),
            ("ocf_growth",        0.20, True),
        ],
        "Operating Efficiency": [
            ("receivables_turnover", 0.50, True),
            ("asset_turnover",       0.50, True),
        ],
        "Growth Velocity": [
            ("revenue_growth",    0.50, True),
            ("net_income_growth", 0.50, True),
        ],
        "Solvency": [
            ("debt_to_equity",    0.50, False),
            ("interest_coverage", 0.50, True),
        ],
    },
    pillar_weights={
        "Profitability": 0.35,
        "Cash Generation": 0.25,
        "Growth Velocity": 0.20,
        "Operating Efficiency": 0.15,
        "Solvency": 0.05,
    },
    valuation_benchmark_metric="pe_ratio",
    key_focus_ratios=["operating_margin", "fcf_margin", "roce", "revenue_growth"],
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. FMCG (Brand Moat, High ROE, Negative Working Capital)
# ─────────────────────────────────────────────────────────────────────────────
FMCG_PROFILE = SectorProfile(
    name="FMCG",
    archetype="Consumer Franchise & Brand Moat",
    description="High gross margins, rapid inventory velocity, negative cash cycles, resilient ROE.",
    pillars={
        "Profitability": [
            ("gross_margin",     0.30, True),
            ("operating_margin", 0.30, True),
            ("roe",              0.25, True),
            ("roce",             0.15, True),
        ],
        "Working Capital Velocity": [
            ("inventory_turnover",   0.45, True),
            ("receivables_turnover", 0.35, True),
            ("cash_ratio",           0.20, True),
        ],
        "Cash Resilience": [
            ("fcf_margin", 0.60, True),
            ("ocf_growth", 0.40, True),
        ],
        "Growth": [
            ("revenue_growth",    0.55, True),
            ("net_income_growth", 0.45, True),
        ],
        "Capital Structure": [
            ("debt_to_equity",    0.60, False),
            ("interest_coverage", 0.40, True),
        ],
    },
    pillar_weights={
        "Profitability": 0.35,
        "Working Capital Velocity": 0.25,
        "Cash Resilience": 0.20,
        "Growth": 0.15,
        "Capital Structure": 0.05,
    },
    valuation_benchmark_metric="pe_ratio",
    key_focus_ratios=["gross_margin", "inventory_turnover", "roe", "fcf_margin"],
)

# ─────────────────────────────────────────────────────────────────────────────
# 3. PHARMACEUTICALS (R&D CapEx, Global Compliance, Operating Margin)
# ─────────────────────────────────────────────────────────────────────────────
PHARMA_PROFILE = SectorProfile(
    name="Pharmaceuticals",
    archetype="Regulated Manufacturing & Innovation",
    description="Complex formulation CapEx, steady gross margin, moderate working capital buffers.",
    pillars={
        "Profitability": [
            ("gross_margin",     0.30, True),
            ("operating_margin", 0.35, True),
            ("net_margin",       0.20, True),
            ("roce",             0.15, True),
        ],
        "Operating Quality": [
            ("asset_turnover",       0.40, True),
            ("receivables_turnover", 0.35, True),
            ("inventory_turnover",   0.25, True),
        ],
        "Liquidity & Solvency": [
            ("current_ratio",     0.35, True),
            ("debt_to_equity",    0.35, False),
            ("interest_coverage", 0.30, True),
        ],
        "Growth & Reinvestment": [
            ("revenue_growth",    0.40, True),
            ("net_income_growth", 0.35, True),
            ("ocf_growth",        0.25, True),
        ],
    },
    pillar_weights={
        "Profitability": 0.35,
        "Growth & Reinvestment": 0.25,
        "Operating Quality": 0.20,
        "Liquidity & Solvency": 0.20,
    },
    valuation_benchmark_metric="pe_ratio",
    key_focus_ratios=["operating_margin", "roce", "current_ratio", "revenue_growth"],
)

# ─────────────────────────────────────────────────────────────────────────────
# 4. AUTOMOBILE (Cyclical CapEx, Operating Leverage, Supply Chain Velocity)
# ─────────────────────────────────────────────────────────────────────────────
AUTO_PROFILE = SectorProfile(
    name="Automobile",
    archetype="Cyclical Heavy Assembly & OEM Network",
    description="Intensive tooling CapEx, operating leverage swings, strict inventory cycles.",
    pillars={
        "Operating Efficiency": [
            ("asset_turnover",       0.40, True),
            ("inventory_turnover",   0.35, True),
            ("receivables_turnover", 0.25, True),
        ],
        "Profitability": [
            ("operating_margin", 0.40, True),
            ("gross_margin",     0.25, True),
            ("roce",             0.20, True),
            ("roe",              0.15, True),
        ],
        "Solvency & Coverage": [
            ("debt_to_equity",    0.40, False),
            ("interest_coverage", 0.35, True),
            ("debt_ratio",        0.25, False),
        ],
        "Growth & Cash Flow": [
            ("revenue_growth",    0.40, True),
            ("net_income_growth", 0.35, True),
            ("fcf_margin",        0.25, True),
        ],
        "Liquidity": [
            ("current_ratio", 0.55, True),
            ("quick_ratio",   0.45, True),
        ],
    },
    pillar_weights={
        "Operating Efficiency": 0.30,
        "Profitability": 0.25,
        "Solvency & Coverage": 0.20,
        "Growth & Cash Flow": 0.15,
        "Liquidity": 0.10,
    },
    valuation_benchmark_metric="ev_ebitda",
    key_focus_ratios=["operating_margin", "inventory_turnover", "debt_to_equity", "roce"],
)

# ─────────────────────────────────────────────────────────────────────────────
# 5. METALS & MINING (Commodity Price Taker, High Debt Capacity, Asset Heavy)
# ─────────────────────────────────────────────────────────────────────────────
METALS_PROFILE = SectorProfile(
    name="Metals & Mining",
    archetype="Capital-Intensive Commodity Producer",
    description="Heavy fixed-asset footprint, high leverage tolerances, debt repayment via EBITDA.",
    pillars={
        "Balance Sheet & Solvency": [
            ("debt_to_equity",    0.40, False),
            ("interest_coverage", 0.35, True),
            ("debt_ratio",        0.25, False),
        ],
        "Profitability & Spread": [
            ("operating_margin", 0.40, True),
            ("roce",             0.35, True),
            ("net_margin",       0.25, True),
        ],
        "Capital Efficiency": [
            ("asset_turnover", 0.55, True),
            ("fcf_margin",     0.45, True),
        ],
        "Growth & Cycle Momentum": [
            ("revenue_growth",    0.45, True),
            ("net_income_growth", 0.35, True),
            ("ocf_growth",        0.20, True),
        ],
        "Liquidity Buffer": [
            ("current_ratio", 0.60, True),
            ("cash_ratio",    0.40, True),
        ],
    },
    pillar_weights={
        "Balance Sheet & Solvency": 0.35,
        "Profitability & Spread": 0.25,
        "Capital Efficiency": 0.20,
        "Liquidity Buffer": 0.10,
        "Growth & Cycle Momentum": 0.10,
    },
    valuation_benchmark_metric="ev_ebitda",
    key_focus_ratios=["debt_to_equity", "interest_coverage", "operating_margin", "asset_turnover"],
)

# ─────────────────────────────────────────────────────────────────────────────
# GENERIC FALLBACK PROFILE (For unmapped or general non-financial sectors)
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_SECTOR_PROFILE = SectorProfile(
    name="General Non-Financial",
    archetype="Diversified Corporate",
    description="Balanced five-pillar fundamental framework across profitability, solvency and growth.",
    pillars={
        "Profitability": [
            ("gross_margin",     0.20, True),
            ("operating_margin", 0.25, True),
            ("net_margin",       0.25, True),
            ("roe",              0.15, True),
            ("roa",              0.15, True),
        ],
        "Liquidity": [
            ("current_ratio", 0.40, True),
            ("quick_ratio",   0.35, True),
            ("cash_ratio",    0.25, True),
        ],
        "Solvency": [
            ("debt_to_equity",    0.40, False),
            ("debt_ratio",        0.35, False),
            ("interest_coverage", 0.25, True),
        ],
        "Efficiency": [
            ("asset_turnover",       0.40, True),
            ("inventory_turnover",   0.30, True),
            ("receivables_turnover", 0.30, True),
        ],
        "Growth": [
            ("revenue_growth",    0.35, True),
            ("net_income_growth", 0.35, True),
            ("ocf_growth",        0.30, True),
        ],
    },
    pillar_weights={
        "Profitability": 0.30,
        "Liquidity":     0.15,
        "Solvency":      0.20,
        "Efficiency":    0.15,
        "Growth":        0.20,
    },
    valuation_benchmark_metric="pe_ratio",
    key_focus_ratios=["operating_margin", "roe", "debt_to_equity", "current_ratio"],
)

SECTOR_PROFILES_MAP: Dict[str, SectorProfile] = {
    "Information Technology": IT_PROFILE,
    "FMCG": FMCG_PROFILE,
    "Pharmaceuticals": PHARMA_PROFILE,
    "Automobile": AUTO_PROFILE,
    "Metals & Mining": METALS_PROFILE,
}
SECTOR_PROFILES = SECTOR_PROFILES_MAP


def get_sector_profile(sector_name: Optional[str]) -> SectorProfile:
    """Retrieves sector-specific scoring profile with fallback to default corporate profile."""
    if not sector_name:
        return DEFAULT_SECTOR_PROFILE
    
    if sector_name in SECTOR_PROFILES_MAP:
        return SECTOR_PROFILES_MAP[sector_name]

    slug = sector_name.strip().lower().replace("_", " ").replace("-", " ")
    for name, profile in SECTOR_PROFILES_MAP.items():
        if name.lower() == slug:
            return profile

    alias_map = {
        "it": IT_PROFILE,
        "tech": IT_PROFILE,
        "information technology": IT_PROFILE,
        "fmcg": FMCG_PROFILE,
        "consumer": FMCG_PROFILE,
        "pharma": PHARMA_PROFILE,
        "pharmaceuticals": PHARMA_PROFILE,
        "auto": AUTO_PROFILE,
        "automobile": AUTO_PROFILE,
        "automotive": AUTO_PROFILE,
        "metals": METALS_PROFILE,
        "metals & mining": METALS_PROFILE,
        "metals and mining": METALS_PROFILE,
    }
    return alias_map.get(slug, DEFAULT_SECTOR_PROFILE)


def list_supported_sectors() -> List[str]:
    """Returns list of primary supported non-financial investment sectors."""
    return list(SECTOR_PROFILES_MAP.keys())
