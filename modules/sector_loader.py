"""
sector_loader.py
================
Loads NSE-listed companies grouped by sector and industry.
Provides a curated, maintainable sector→company mapping with .NS suffix.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CURATED NSE SECTOR MAP
# Keys  = sector labels shown in the UI
# Values = list of NSE tickers (with .NS suffix)
# ─────────────────────────────────────────────────────────────────────────────
NSE_SECTOR_MAP: Dict[str, List[str]] = {
    "Information Technology": [
        "TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS",
        "LTIM.NS", "MPHASIS.NS", "COFORGE.NS", "PERSISTENT.NS", "OFSS.NS",
    ],
    "Banking & Finance": [
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS",
        "INDUSINDBK.NS", "BANKBARODA.NS", "PNB.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS",
    ],
    "Pharmaceuticals": [
        "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS",
        "BIOCON.NS", "TORNTPHARM.NS", "LUPIN.NS", "AUROPHARMA.NS", "ALKEM.NS",
    ],
    "FMCG": [
        "HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS",
        "GODREJCP.NS", "MARICO.NS", "COLPAL.NS", "EMAMILTD.NS", "VBL.NS",
    ],
    "Automobile": [
        "MARUTI.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS",
        "EICHERMOT.NS", "ASHOKLEY.NS", "TVSMOTOR.NS", "BALKRISIND.NS", "MOTHERSON.NS",
    ],
    "Metals & Mining": [
        "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "VEDL.NS", "SAIL.NS",
        "NMDC.NS", "NATIONALUM.NS", "HINDCOPPER.NS", "APLAPOLLO.NS", "RATNAMANI.NS",
    ],
    "Energy & Oil": [
        "RELIANCE.NS", "ONGC.NS", "BPCL.NS", "IOC.NS", "GAIL.NS",
        "PETRONET.NS", "MGL.NS", "IGL.NS", "ADANIGREEN.NS", "TATAPOWER.NS",
    ],
    "Infrastructure & Construction": [
        "LT.NS", "ULTRACEMCO.NS", "GRASIM.NS", "SHREECEM.NS", "AMBUJACEM.NS",
        "ACC.NS", "DALMIACEMBE.NS", "JKCEMENT.NS", "RAMCOCEM.NS", "KNRCON.NS",
    ],
    "Consumer Durables": [
        "TITAN.NS", "HAVELLS.NS", "VOLTAS.NS", "WHIRLPOOL.NS", "BLUESTARCO.NS",
        "VGUARD.NS", "POLYCAB.NS", "CROMPTON.NS", "SYMPHONY.NS", "ORIENTELEC.NS",
    ],
    "Telecom": [
        "BHARTIARTL.NS", "IDEA.NS", "TATACOMM.NS", "HFCL.NS", "STLTECH.NS",
    ],
    "Real Estate": [
        "DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "PRESTIGE.NS", "PHOENIXLTD.NS",
        "SOBHA.NS", "BRIGADE.NS", "MAHLIFE.NS",
    ],
    "Aviation & Logistics": [
        "INDIGO.NS", "BLUEDART.NS", "DELHIVERY.NS", "VRL.NS", "GATI.NS",
    ],
    "Insurance": [
        "SBILIFE.NS", "HDFCLIFE.NS", "ICICIGI.NS", "ICICIPRULI.NS", "LICI.NS",
    ],
}

# Industry sub-map (optional granularity)
NSE_INDUSTRY_MAP: Dict[str, List[str]] = {
    "Large-cap IT Services": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    "Mid-cap IT": ["MPHASIS.NS", "COFORGE.NS", "PERSISTENT.NS", "LTIM.NS"],
    "Private Banks": ["HDFCBANK.NS", "ICICIBANK.NS", "KOTAKBANK.NS", "AXISBANK.NS"],
    "PSU Banks": ["SBIN.NS", "BANKBARODA.NS", "PNB.NS"],
    "Pharma - Generics": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "LUPIN.NS"],
    "Pharma - APIs": ["DIVISLAB.NS", "AUROPHARMA.NS", "ALKEM.NS"],
    "FMCG - Household": ["HINDUNILVR.NS", "GODREJCP.NS", "MARICO.NS"],
    "FMCG - Foods": ["NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS"],
    "4-Wheelers": ["MARUTI.NS", "TATAMOTORS.NS", "M&M.NS"],
    "2-Wheelers": ["BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "EICHERMOT.NS", "TVSMOTOR.NS"],
}


class SectorLoader:
    """Loads and provides NSE sector / industry company lists."""

    def __init__(self) -> None:
        self._sector_map: Dict[str, List[str]] = NSE_SECTOR_MAP
        self._industry_map: Dict[str, List[str]] = NSE_INDUSTRY_MAP
        logger.info("SectorLoader initialised with %d sectors.", len(self._sector_map))

    # ── Public API ────────────────────────────────────────────────────────────

    def get_sectors(self) -> List[str]:
        """Return sorted list of available sectors."""
        return sorted(self._sector_map.keys())

    def get_industries(self) -> List[str]:
        """Return sorted list of available industries."""
        return sorted(self._industry_map.keys())

    def get_companies_by_sector(self, sector: str) -> List[str]:
        """Return ticker list for a sector (empty list if not found)."""
        tickers = self._sector_map.get(sector, [])
        if not tickers:
            logger.warning("Sector '%s' not found or has no tickers.", sector)
        return list(tickers)

    def get_companies_by_industry(self, industry: str) -> List[str]:
        """Return ticker list for an industry."""
        tickers = self._industry_map.get(industry, [])
        if not tickers:
            logger.warning("Industry '%s' not found or has no tickers.", industry)
        return list(tickers)

    def get_all_tickers(self) -> List[str]:
        """Return de-duplicated list of all tickers across all sectors."""
        seen: set = set()
        result: List[str] = []
        for tickers in self._sector_map.values():
            for t in tickers:
                if t not in seen:
                    seen.add(t)
                    result.append(t)
        return result

    def get_sector_for_ticker(self, ticker: str) -> Optional[str]:
        """Reverse-lookup: return sector name for a given ticker."""
        for sector, tickers in self._sector_map.items():
            if ticker in tickers:
                return sector
        return None

    def get_sector_map(self) -> Dict[str, List[str]]:
        return dict(self._sector_map)

    def get_all_sectors(self) -> Dict[str, List[str]]:
        """Return dict of {sector_name: tickers}."""
        return dict(self._sector_map)

    def get_tickers(self, sector: str) -> List[str]:
        """Convenience alias for get_companies_by_sector."""
        return self.get_companies_by_sector(sector)

    def get_industry_map(self) -> Dict[str, List[str]]:
        return dict(self._industry_map)

    # ── Utility ───────────────────────────────────────────────────────────────

    @staticmethod
    def normalise_ticker(ticker: str) -> str:
        """Ensure ticker ends with .NS."""
        ticker = ticker.strip().upper()
        if not ticker.endswith(".NS"):
            ticker += ".NS"
        return ticker

    def summary(self) -> Dict[str, int]:
        """Return {sector: company_count} summary dict."""
        return {s: len(t) for s, t in self._sector_map.items()}