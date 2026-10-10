"""
reconciliation_config.py
========================
Configuration parameters and thresholds for the Multi-Source Reconciliation Engine.
Centralizes all tolerance values, weights, and decision boundaries per Blueprint 2.
"""

from dataclasses import dataclass
from typing import Dict

@dataclass
class ReconciliationConfig:
    """
    Configuration parameters for 3-tier multi-source financial reconciliation.
    """
    # Amount tolerance: greater of absolute amount or percentage of source record
    epsilon_abs: float = 1.0       # e.g., ₹1 rounding buffer
    epsilon_pct: float = 0.001     # 0.1% buffer for bank charges / withholding

    # Date matching window (clearing lag in business days)
    date_window_days: int = 3

    # Tier 2 fuzzy scoring weights (w1 + w2 + w3 == 1.0)
    w_amount: float = 0.5
    w_date: float = 0.3
    w_desc: float = 0.2

    # Tier 2 acceptance thresholds
    tau_high: float = 0.85         # Score >= tau_high -> Accepted Auto-Match
    tau_low: float = 0.55          # tau_low <= Score < tau_high -> Partial Match (Review)

    # Tier 3 subset-sum bounds (split transaction detection)
    max_split_k: int = 4           # Maximum records to combine in subset-sum
    split_confidence: float = 0.85 # Fixed confidence score for split matches

    # Exception severity thresholds
    high_amount_discrepancy_pct: float = 0.05  # >5% discrepancy -> HIGH severity
    timing_discrepancy_days: int = 7           # >7 days delay -> MEDIUM severity

DEFAULT_RECON_CONFIG = ReconciliationConfig()
