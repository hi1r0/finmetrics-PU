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

    # Reference evidence (invoice no., UTR, cheque no.): composite-score floors when the
    # two records share a reference (in tolerance / outside tolerance but inside the 5x gate)
    ref_match_floor: float = 0.95
    ref_match_floor_out_of_tol: float = 0.75
    ref_assignment_preference: float = 0.05    # cost bonus so referenced pairs beat equal-score decoys

    # Auto-approval needs decisive evidence: a reference link, or a composite score that beats
    # the best competing candidate in the date/amount neighborhood by at least this margin
    decisive_margin: float = 0.12

    # Tier 3 split evidence: tolerance is per part (not a % of the total); without a shared
    # reference on every part the split is routed to review instead of auto-matched
    split_eps_per_part: float = 1.0
    split_partial_confidence: float = 0.60

    # Exception diagnosis bounds (variance diagnoses need evidence, not just proximity)
    amount_discrepancy_max_pct: float = 0.30   # unreferenced candidates beyond this are not "the same txn"
    discrepancy_min_jaccard: float = 0.10      # minimum narration overlap for unreferenced discrepancy
    timing_max_days: int = 45                  # unreferenced same-amount candidates further apart are not timing

    # Accounting direction inversion (Ledger Dr == Bank Cr; Ledger Cr == Bank Dr)
    # Default is True when reconciling client ledger against bank statements.
    invert_comparator_direction: bool = True

DEFAULT_RECON_CONFIG = ReconciliationConfig()
