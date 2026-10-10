"""
reconciliation_engine.py
========================
Multi-Source Financial Reconciliation Engine.
Executes a 3-tier matching cascade (Exact, Fuzzy, Split) with bipartite assignment,
confidence scoring, exception classification, and transparent match-rate decomposition.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
import itertools
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from modules.bank_statement_loader import StandardizedRecord, Direction, RecordSource
from modules.reconciliation_config import ReconciliationConfig, DEFAULT_RECON_CONFIG

logger = logging.getLogger(__name__)


class MatchTier(str, Enum):
    TIER_1_EXACT = "TIER_1_EXACT"
    TIER_2_FUZZY = "TIER_2_FUZZY"
    TIER_3_SPLIT = "TIER_3_SPLIT"
    UNRESOLVED = "UNRESOLVED"


class MatchStatus(str, Enum):
    MATCHED = "MATCHED"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    UNMATCHED = "UNMATCHED"


class ExceptionSeverity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


@dataclass
class ReconciliationMatch:
    """Represents a matched pair or unresolved exception item."""
    match_id: str
    tier: MatchTier
    status: MatchStatus
    confidence: float
    record_a: Optional[StandardizedRecord]
    records_b: List[StandardizedRecord]
    amount_diff: float
    date_diff_days: int
    jaccard_similarity: float
    severity: ExceptionSeverity
    reason_code: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "match_id": self.match_id,
            "tier": str(self.tier.value),
            "status": str(self.status.value),
            "confidence": round(self.confidence, 4),
            "record_a_id": self.record_a.record_id if self.record_a else None,
            "record_a_desc": self.record_a.description if self.record_a else None,
            "record_a_amount": self.record_a.amount if self.record_a else 0.0,
            "records_b_ids": [b.record_id for b in self.records_b],
            "records_b_desc": "; ".join([b.description for b in self.records_b]),
            "records_b_amount": sum(b.amount for b in self.records_b),
            "amount_diff": round(self.amount_diff, 2),
            "date_diff_days": self.date_diff_days,
            "jaccard_similarity": round(self.jaccard_similarity, 4),
            "severity": str(self.severity.value),
            "reason_code": self.reason_code,
            "notes": self.notes,
        }


@dataclass
class ReconciliationResult:
    """Consolidated reconciliation report containing matches, metrics, and audit tables."""
    matches: List[ReconciliationMatch]
    total_records_a: int
    total_records_b: int
    match_rate: float
    auto_resolved_rate: float
    review_required_rate: float
    exception_rate: float
    matches_df: pd.DataFrame
    exceptions_df: pd.DataFrame
    metrics_summary: Dict[str, Any]


class ReconciliationEngine:
    """
    Executes 3-tier cascade matching across two transaction record streams.
    """

    def __init__(self, config: Optional[ReconciliationConfig] = None):
        self.cfg = config or DEFAULT_RECON_CONFIG

    # ── Tokenization & Similarity Helpers ─────────────────────────────────────

    @staticmethod
    def _tokenize(text: str) -> Set[str]:
        """Lowers text and extracts alphanumeric token set, ignoring stop-words."""
        if not text:
            return set()
        clean = re.sub(r"[^\w\s]", " ", text.lower())
        tokens = clean.split()
        stopwords = {"the", "a", "an", "and", "or", "to", "for", "in", "on", "at", "by", "from", "of", "ac", "a/c", "ltd", "pvt"}
        return {t for t in tokens if len(t) > 1 and t not in stopwords}

    @classmethod
    def jaccard_similarity(cls, text_a: str, text_b: str) -> float:
        """Computes Jaccard index between two description strings."""
        tokens_a = cls._tokenize(text_a)
        tokens_b = cls._tokenize(text_b)
        if not tokens_a and not tokens_b:
            return 1.0
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = tokens_a.intersection(tokens_b)
        union = tokens_a.union(tokens_b)
        return len(intersection) / len(union)

    def _amount_tolerance(self, base_amount: float) -> float:
        """Returns max(epsilon_abs, base_amount * epsilon_pct)."""
        return max(self.cfg.epsilon_abs, base_amount * self.cfg.epsilon_pct)

    # ── Main Reconciliation Entry Point ───────────────────────────────────────

    def reconcile(
        self,
        source_a: List[StandardizedRecord],
        source_b: List[StandardizedRecord],
    ) -> ReconciliationResult:
        """
        Executes the three-tier matching pipeline:
        Tier 1: Exact Hash Join
        Tier 2: Fuzzy Matching with Optimal Bipartite Assignment
        Tier 3: Subset-Sum Split Detection
        Unresolved: Exception Classification
        """
        logger.info(f"Starting reconciliation: Source A={len(source_a)}, Source B={len(source_b)}")
        
        matches: List[ReconciliationMatch] = []
        matched_a_indices: Set[int] = set()
        matched_b_indices: Set[int] = set()
        match_counter = 1

        # ----------------------------------------------------------------------
        # Tier 1: Deterministic Exact Match
        # ----------------------------------------------------------------------
        # Build lookup table on Source B: (direction, round(amount, 2), date) -> list of (idx, record)
        lookup_b: Dict[Tuple[str, float, date], List[Tuple[int, StandardizedRecord]]] = {}
        for idx_b, b in enumerate(source_b):
            key = (str(b.direction.value), round(b.amount, 2), b.date)
            lookup_b.setdefault(key, []).append((idx_b, b))

        for idx_a, a in enumerate(source_a):
            key = (str(a.direction.value), round(a.amount, 2), a.date)
            if key in lookup_b and lookup_b[key]:
                idx_b, b = lookup_b[key].pop(0)
                matched_a_indices.add(idx_a)
                matched_b_indices.add(idx_b)

                matches.append(
                    ReconciliationMatch(
                        match_id=f"MCH-{match_counter:05d}",
                        tier=MatchTier.TIER_1_EXACT,
                        status=MatchStatus.MATCHED,
                        confidence=1.0,
                        record_a=a,
                        records_b=[b],
                        amount_diff=0.0,
                        date_diff_days=0,
                        jaccard_similarity=self.jaccard_similarity(a.description, b.description),
                        severity=ExceptionSeverity.NONE,
                        reason_code=None,
                        notes="Exact match on date, amount, and direction.",
                    )
                )
                match_counter += 1

        logger.info(f"Tier 1 Exact Matches resolved: {len(matches)}")

        # ----------------------------------------------------------------------
        # Tier 2: Fuzzy Matching with Hungarian Bipartite Assignment
        # ----------------------------------------------------------------------
        unresolved_a_indices = [i for i in range(len(source_a)) if i not in matched_a_indices]
        unresolved_b_indices = [i for i in range(len(source_b)) if i not in matched_b_indices]

        if unresolved_a_indices and unresolved_b_indices:
            cost_matrix = np.full((len(unresolved_a_indices), len(unresolved_b_indices)), 1e6)
            score_matrix = np.zeros((len(unresolved_a_indices), len(unresolved_b_indices)))

            for i, idx_a in enumerate(unresolved_a_indices):
                rec_a = source_a[idx_a]
                eps = self._amount_tolerance(rec_a.amount)

                for j, idx_b in enumerate(unresolved_b_indices):
                    rec_b = source_b[idx_b]
                    if rec_a.direction != rec_b.direction:
                        continue

                    amt_diff = abs(rec_a.amount - rec_b.amount)
                    date_diff = abs((rec_a.date - rec_b.date).days)

                    if amt_diff <= eps * 5 and date_diff <= self.cfg.date_window_days:
                        # Compute components
                        s_amt = 1.0 if amt_diff <= eps else max(0.0, 1.0 - (amt_diff / (eps * 5)))
                        s_date = max(0.0, 1.0 - (date_diff / max(self.cfg.date_window_days, 1)))
                        s_desc = self.jaccard_similarity(rec_a.description, rec_b.description)

                        composite = (
                            self.cfg.w_amount * s_amt
                            + self.cfg.w_date * s_date
                            + self.cfg.w_desc * s_desc
                        )
                        score_matrix[i, j] = composite
                        if composite >= self.cfg.tau_low:
                            cost_matrix[i, j] = 1.0 - composite

            # Solve optimal matching if any candidate pairs exist
            valid_pairs = np.where(cost_matrix < 1e5)
            if len(valid_pairs[0]) > 0:
                row_ind, col_ind = linear_sum_assignment(cost_matrix)
                for r, c in zip(row_ind, col_ind):
                    if cost_matrix[r, c] < 1.0:
                        idx_a = unresolved_a_indices[r]
                        idx_b = unresolved_b_indices[c]
                        rec_a = source_a[idx_a]
                        rec_b = source_b[idx_b]
                        score = score_matrix[r, c]

                        is_auto = score >= self.cfg.tau_high
                        status = MatchStatus.MATCHED if is_auto else MatchStatus.PARTIAL_MATCH
                        severity = ExceptionSeverity.NONE if is_auto else ExceptionSeverity.LOW

                        matched_a_indices.add(idx_a)
                        matched_b_indices.add(idx_b)

                        amt_diff = abs(rec_a.amount - rec_b.amount)
                        date_diff = abs((rec_a.date - rec_b.date).days)

                        matches.append(
                            ReconciliationMatch(
                                match_id=f"MCH-{match_counter:05d}",
                                tier=MatchTier.TIER_2_FUZZY,
                                status=status,
                                confidence=round(score, 4),
                                record_a=rec_a,
                                records_b=[rec_b],
                                amount_diff=amt_diff,
                                date_diff_days=date_diff,
                                jaccard_similarity=self.jaccard_similarity(rec_a.description, rec_b.description),
                                severity=severity,
                                reason_code=None if is_auto else "BELOW_AUTO_THRESHOLD",
                                notes=f"Fuzzy match (Score={score:.2f}, amt_diff=₹{amt_diff:.2f}, date_diff={date_diff}d)",
                            )
                        )
                        match_counter += 1

        logger.info(f"After Tier 2, total matches: {len(matches)}")

        # ----------------------------------------------------------------------
        # Tier 3: Subset-Sum Split Matching (1-to-Many)
        # ----------------------------------------------------------------------
        still_unresolved_a = [i for i in range(len(source_a)) if i not in matched_a_indices]
        still_unresolved_b = [i for i in range(len(source_b)) if i not in matched_b_indices]

        for idx_a in list(still_unresolved_a):
            rec_a = source_a[idx_a]
            eps = self._amount_tolerance(rec_a.amount)

            # Restrict candidates in B within date window and matching direction
            candidates_b = [
                i for i in still_unresolved_b
                if source_b[i].direction == rec_a.direction
                and abs((source_b[i].date - rec_a.date).days) <= self.cfg.date_window_days * 2
                and source_b[i].amount < rec_a.amount + eps
            ]

            found_split = False
            for k in range(2, min(self.cfg.max_split_k + 1, len(candidates_b) + 1)):
                for combo in itertools.combinations(candidates_b, k):
                    total_split = sum(source_b[i].amount for i in combo)
                    if abs(total_split - rec_a.amount) <= eps:
                        # Found valid split
                        matched_recs_b = [source_b[i] for i in combo]
                        matched_a_indices.add(idx_a)
                        for i in combo:
                            matched_b_indices.add(i)
                            still_unresolved_b.remove(i)

                        max_date_diff = max(abs((b.date - rec_a.date).days) for b in matched_recs_b)
                        matches.append(
                            ReconciliationMatch(
                                match_id=f"MCH-{match_counter:05d}",
                                tier=MatchTier.TIER_3_SPLIT,
                                status=MatchStatus.MATCHED,
                                confidence=self.cfg.split_confidence,
                                record_a=rec_a,
                                records_b=matched_recs_b,
                                amount_diff=abs(total_split - rec_a.amount),
                                date_diff_days=max_date_diff,
                                jaccard_similarity=0.5,
                                severity=ExceptionSeverity.LOW,
                                reason_code=None,
                                notes=f"Split match: 1 entry in A matched to {len(combo)} entries in B.",
                            )
                        )
                        match_counter += 1
                        found_split = True
                        break
                if found_split:
                    break

        logger.info(f"After Tier 3, total matches: {len(matches)}")

        # ----------------------------------------------------------------------
        # Exceptions: Unmatched Records in Source A & Source B
        # ----------------------------------------------------------------------
        final_unresolved_a = [source_a[i] for i in range(len(source_a)) if i not in matched_a_indices]
        final_unresolved_b = [source_b[i] for i in range(len(source_b)) if i not in matched_b_indices]

        for rec_a in final_unresolved_a:
            # Diagnose reason code and severity
            severity, reason, note = self._classify_exception(rec_a, final_unresolved_b)
            matches.append(
                ReconciliationMatch(
                    match_id=f"EXC-{match_counter:05d}",
                    tier=MatchTier.UNRESOLVED,
                    status=MatchStatus.UNMATCHED,
                    confidence=0.0,
                    record_a=rec_a,
                    records_b=[],
                    amount_diff=rec_a.amount,
                    date_diff_days=0,
                    jaccard_similarity=0.0,
                    severity=severity,
                    reason_code=reason,
                    notes=note,
                )
            )
            match_counter += 1

        for rec_b in final_unresolved_b:
            matches.append(
                ReconciliationMatch(
                    match_id=f"EXC-{match_counter:05d}",
                    tier=MatchTier.UNRESOLVED,
                    status=MatchStatus.UNMATCHED,
                    confidence=0.0,
                    record_a=None,
                    records_b=[rec_b],
                    amount_diff=rec_b.amount,
                    date_diff_days=0,
                    jaccard_similarity=0.0,
                    severity=ExceptionSeverity.MEDIUM,
                    reason_code="UNRECORDED_COMPARATOR_TRANSACTION",
                    notes="Transaction exists in Comparator (Bank/NSE) but is absent in Ledger.",
                )
            )
            match_counter += 1

        # ----------------------------------------------------------------------
        # Aggregation & Metric Calculation
        # ----------------------------------------------------------------------
        total_a = len(source_a)
        total_b = len(source_b)
        n_total = max(total_a, 1)

        tier_1_count = sum(1 for m in matches if m.tier == MatchTier.TIER_1_EXACT)
        tier_2_count = sum(1 for m in matches if m.tier == MatchTier.TIER_2_FUZZY and m.status == MatchStatus.MATCHED)
        tier_3_count = sum(1 for m in matches if m.tier == MatchTier.TIER_3_SPLIT)
        partial_count = sum(1 for m in matches if m.status == MatchStatus.PARTIAL_MATCH)
        unmatched_a_count = len(final_unresolved_a)

        # Total matches resolved across Tiers 1-3 (including partial review matches)
        match_count = tier_1_count + tier_2_count + tier_3_count + partial_count
        match_rate = round((match_count / n_total) * 100, 2)
        auto_resolved_rate = round(((tier_1_count + tier_2_count) / n_total) * 100, 2)
        review_required_rate = round((partial_count / n_total) * 100, 2)
        exception_rate = round((unmatched_a_count / n_total) * 100, 2)

        matches_dict_list = [m.to_dict() for m in matches if m.status != MatchStatus.UNMATCHED]
        exceptions_dict_list = [m.to_dict() for m in matches if m.status != MatchStatus.MATCHED]

        matches_df = pd.DataFrame(matches_dict_list) if matches_dict_list else pd.DataFrame()
        exceptions_df = pd.DataFrame(exceptions_dict_list) if exceptions_dict_list else pd.DataFrame()

        metrics_summary = {
            "total_records_source_a": total_a,
            "total_records_source_b": total_b,
            "tier_1_exact_count": tier_1_count,
            "tier_2_fuzzy_count": tier_2_count,
            "tier_3_split_count": tier_3_count,
            "partial_match_count": partial_count,
            "unresolved_exceptions_count": unmatched_a_count + len(final_unresolved_b),
            "match_rate_pct": match_rate,
            "auto_resolved_rate_pct": auto_resolved_rate,
            "review_required_rate_pct": review_required_rate,
            "exception_rate_pct": exception_rate,
        }

        return ReconciliationResult(
            matches=matches,
            total_records_a=total_a,
            total_records_b=total_b,
            match_rate=match_rate,
            auto_resolved_rate=auto_resolved_rate,
            review_required_rate=review_required_rate,
            exception_rate=exception_rate,
            matches_df=matches_df,
            exceptions_df=exceptions_df,
            metrics_summary=metrics_summary,
        )

    # ── Exception Diagnostic Helper ───────────────────────────────────────────

    def _classify_exception(
        self,
        rec_a: StandardizedRecord,
        candidates_b: List[StandardizedRecord],
    ) -> Tuple[ExceptionSeverity, str, str]:
        """Classifies exception severity and reason per Blueprint 2."""
        if not candidates_b:
            return (
                ExceptionSeverity.HIGH,
                "MISSING_CORRESPONDING_RECORD",
                "No transaction found in comparator record set.",
            )

        # Check for near amount match with large date gap
        for b in candidates_b:
            if abs(rec_a.amount - b.amount) <= self._amount_tolerance(rec_a.amount):
                days = abs((rec_a.date - b.date).days)
                if days > self.cfg.timing_discrepancy_days:
                    return (
                        ExceptionSeverity.MEDIUM,
                        "TIMING_DELAY",
                        f"Amount matches candidate {b.record_id}, but date discrepancy is {days} days.",
                    )

        # Check for matching date/description with large amount gap
        for b in candidates_b:
            if abs((rec_a.date - b.date).days) <= self.cfg.date_window_days:
                amt_pct = abs(rec_a.amount - b.amount) / max(rec_a.amount, 1.0)
                if amt_pct > self.cfg.high_amount_discrepancy_pct:
                    return (
                        ExceptionSeverity.HIGH,
                        "AMOUNT_DISCREPANCY",
                        f"Date aligns with candidate {b.record_id}, but amount differs by {amt_pct*100:.1f}%.",
                    )

        return (
            ExceptionSeverity.MEDIUM,
            "NO_AMOUNT_CANDIDATE",
            "No plausible matching amount or timing candidate found in comparator set.",
        )
