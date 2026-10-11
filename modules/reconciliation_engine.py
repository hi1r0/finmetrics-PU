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
from collections import Counter
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
    Executes the multi-tier cascade matching across two transaction record streams.

    Order of operations (each stage only sees records earlier stages left unresolved):
      Tier 1   exact hash join, disambiguated by reference / narration
      Tier 2a  fuzzy assignment, auto-accept only (score >= tau_high)
      Tier 3   split detection (1 ledger entry -> N bank entries), evidence-gated
      Tier 2b  fuzzy assignment, review band (tau_low <= score < tau_high)
      Exceptions with bounded, evidence-based reason codes
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

    def _dir_ok(self, dir_a: Direction, dir_b: Direction) -> bool:
        """Checks direction compatibility according to double-entry bookkeeping convention."""
        if self.cfg.invert_comparator_direction:
            return dir_a != dir_b
        return dir_a == dir_b

    def _expected_b_dir(self, dir_a: Direction) -> Direction:
        """Determines expected comparator direction for a given source_a direction."""
        if self.cfg.invert_comparator_direction:
            return Direction.CREDIT if dir_a == Direction.DEBIT else Direction.DEBIT
        return dir_a

    # ── Reference Evidence ─────────────────────────────────────────────────────

    _GENERIC_REFS = {"NAN", "NA", "NIL", "NONE", "NULL", "N/A"}

    @classmethod
    def _norm_ref(cls, value: Optional[str]) -> str:
        ref = (value or "").strip().upper()
        return "" if (len(ref) < 3 or ref in cls._GENERIC_REFS) else ref

    @classmethod
    def _ref_match(cls, a: StandardizedRecord, b: StandardizedRecord) -> bool:
        """
        True when the two records carry the same business reference (invoice no., UTR,
        cheque no.), either as equal reference fields or one reference quoted inside the
        other record's narration. Positive evidence only: differing references never
        veto a match, because ledger voucher numbers and bank UTRs rarely coincide.
        """
        ra, rb = cls._norm_ref(a.account_code), cls._norm_ref(b.account_code)
        if ra and ra == rb:
            return True
        da, db = (a.description or "").upper(), (b.description or "").upper()
        return (bool(ra) and ra in db) or (bool(rb) and rb in da)

    # ── Neighborhood gate shared by Tier 1 and Tier 2 ─────────────────────────

    def _compat_matrix(
        self,
        source_a: List[StandardizedRecord],
        source_b: List[StandardizedRecord],
    ) -> np.ndarray:
        """Boolean (n_a x n_b): direction-compatible, amount within 5x tolerance, date within window."""
        if not source_a or not source_b:
            return np.zeros((len(source_a), len(source_b)), dtype=bool)
        amt_a = np.array([a.amount for a in source_a], dtype=float)
        amt_b = np.array([b.amount for b in source_b], dtype=float)
        ord_a = np.array([a.date.toordinal() for a in source_a])
        ord_b = np.array([b.date.toordinal() for b in source_b])
        exp_a = np.array([self._expected_b_dir(a.direction) == Direction.DEBIT for a in source_a])
        dir_b = np.array([b.direction == Direction.DEBIT for b in source_b])
        eps_a = np.maximum(self.cfg.epsilon_abs, amt_a * self.cfg.epsilon_pct)
        return (
            (exp_a[:, None] == dir_b[None, :])
            & (np.abs(amt_a[:, None] - amt_b[None, :]) <= 5.0 * eps_a[:, None])
            & (np.abs(ord_a[:, None] - ord_b[None, :]) <= self.cfg.date_window_days)
        )

    # ── Tier 2 assignment pass ─────────────────────────────────────────────────

    def _fuzzy_pass(
        self,
        source_a: List[StandardizedRecord],
        source_b: List[StandardizedRecord],
        a_indices: List[int],
        b_indices: List[int],
        min_score: float,
    ) -> List[Tuple[int, int, float, bool]]:
        """
        Optimal one-to-one assignment (Hungarian) over pairs whose composite similarity is
        >= min_score. Returns (idx_a, idx_b, score, decisive) where `decisive` means the pair
        is reference-linked or beats the best competing candidate (any gate-compatible pair
        sharing either record) by at least cfg.decisive_margin.
        """
        if not a_indices or not b_indices:
            return []

        n, m = len(a_indices), len(b_indices)
        cost = np.full((n, m), 1e6)
        score_m = np.zeros((n, m))
        cand = np.zeros((n, m), dtype=bool)
        ref_m = np.zeros((n, m), dtype=bool)

        for i, ia in enumerate(a_indices):
            rec_a = source_a[ia]
            eps = self._amount_tolerance(rec_a.amount)
            for j, ib in enumerate(b_indices):
                rec_b = source_b[ib]
                if not self._dir_ok(rec_a.direction, rec_b.direction):
                    continue
                amt_diff = abs(rec_a.amount - rec_b.amount)
                date_diff = abs((rec_a.date - rec_b.date).days)
                if amt_diff <= eps * 5 and date_diff <= self.cfg.date_window_days:
                    s_amt = 1.0 if amt_diff <= eps else max(0.0, 1.0 - (amt_diff / (eps * 5)))
                    s_date = max(0.0, 1.0 - (date_diff / max(self.cfg.date_window_days, 1)))
                    s_desc = self.jaccard_similarity(rec_a.description, rec_b.description)
                    composite = (
                        self.cfg.w_amount * s_amt
                        + self.cfg.w_date * s_date
                        + self.cfg.w_desc * s_desc
                    )
                    is_ref = self._ref_match(rec_a, rec_b)
                    if is_ref:
                        floor = (
                            self.cfg.ref_match_floor
                            if amt_diff <= eps
                            else self.cfg.ref_match_floor_out_of_tol
                        )
                        composite = max(composite, floor)
                    cand[i, j] = True
                    ref_m[i, j] = is_ref
                    score_m[i, j] = composite
                    if composite >= min_score:
                        # Reference-linked pairs win assignment ties against look-alike decoys;
                        # the reported confidence stays the composite score.
                        cost[i, j] = 1.0 - composite - (self.cfg.ref_assignment_preference if is_ref else 0.0)

        if not (cost < 1e5).any():
            return []

        rows, cols = linear_sum_assignment(cost)
        out: List[Tuple[int, int, float, bool]] = []
        for r, c in zip(rows, cols):
            if cost[r, c] >= 1e5:
                continue
            row_alt = max([score_m[r, j] for j in range(m) if j != c and cand[r, j]] + [0.0])
            col_alt = max([score_m[i, c] for i in range(n) if i != r and cand[i, c]] + [0.0])
            alt = max(row_alt, col_alt)
            alt_ref = any(ref_m[r, j] for j in range(m) if j != c) or any(ref_m[i, c] for i in range(n) if i != r)
            if ref_m[r, c]:
                decisive = not alt_ref
            else:
                decisive = (not alt_ref) and (score_m[r, c] - alt) >= self.cfg.decisive_margin
            out.append((a_indices[r], b_indices[c], float(score_m[r, c]), bool(decisive)))
        return out

    # ── Main Reconciliation Entry Point ───────────────────────────────────────

    def reconcile(
        self,
        source_a: List[StandardizedRecord],
        source_b: List[StandardizedRecord],
    ) -> ReconciliationResult:
        """
        Executes the matching pipeline:
        Tier 1 exact join -> Tier 2a auto fuzzy -> Tier 3 splits -> Tier 2b review fuzzy
        -> bounded exception diagnosis.
        """
        logger.info(f"Starting reconciliation: Source A={len(source_a)}, Source B={len(source_b)}")

        matches: List[ReconciliationMatch] = []
        matched_a_indices: Set[int] = set()
        matched_b_indices: Set[int] = set()
        match_counter = 1

        # ----------------------------------------------------------------------
        # Tier 1: Deterministic Exact Match (disambiguated by reference, then narration)
        # ----------------------------------------------------------------------
        lookup_b: Dict[Tuple[str, float, date], List[Tuple[int, StandardizedRecord]]] = {}
        for idx_b, b in enumerate(source_b):
            key = (str(b.direction.value), round(b.amount, 2), b.date)
            lookup_b.setdefault(key, []).append((idx_b, b))

        # Neighborhood compatibility (same gate as Tier 2). An exact (amount, date) hit is only
        # auto-accepted in Tier 1 when it is decisive: reference-linked, or isolated, meaning
        # neither record has any other plausible candidate in the date/amount neighborhood.
        compat = self._compat_matrix(source_a, source_b)
        a_deg = compat.sum(axis=1)
        b_deg = compat.sum(axis=0)

        a_groups: Dict[Tuple[str, float, date], List[int]] = {}
        for idx_a, a in enumerate(source_a):
            key = (str(self._expected_b_dir(a.direction).value), round(a.amount, 2), a.date)
            a_groups.setdefault(key, []).append(idx_a)

        for key, a_idxs in a_groups.items():
            b_items = lookup_b.get(key)
            if not b_items:
                continue
            n_a, n_b = len(a_idxs), len(b_items)

            ref = np.zeros((n_a, n_b))
            jac = np.zeros((n_a, n_b))
            for i, ia in enumerate(a_idxs):
                for j, (_, b_rec) in enumerate(b_items):
                    ref[i, j] = 1.0 if self._ref_match(source_a[ia], b_rec) else 0.0
                    jac[i, j] = self.jaccard_similarity(source_a[ia].description, b_rec.description)

            rows, cols = linear_sum_assignment(-(ref * 2.0 + jac))
            for r, c in zip(rows, cols):
                idx_a = a_idxs[r]
                idx_b, b = b_items[c]
                a = source_a[idx_a]

                comp_ref = max(
                    [ref[r, j] for j in range(n_b) if j != c] + [ref[i, c] for i in range(n_a) if i != r] + [0.0]
                )
                ref_decisive = ref[r, c] == 1.0 and comp_ref < 1.0
                isolated = a_deg[idx_a] == 1 and b_deg[idx_b] == 1
                if not (ref_decisive or isolated):
                    continue   # deferred: Tier 2 weighs it against every competing candidate

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
                        jaccard_similarity=float(jac[r, c]),
                        severity=ExceptionSeverity.NONE,
                        reason_code=None,
                        notes=(
                            "Exact match on date, amount and direction; reference-linked."
                            if ref_decisive
                            else "Exact match on date, amount and direction; no competing candidate in the date/amount neighborhood."
                        ),
                    )
                )
                match_counter += 1

        logger.info(f"Tier 1 resolved: {len(matches)}")

        def _apply_fuzzy(pairs: List[Tuple[int, int, float, bool]]) -> None:
            nonlocal match_counter
            for idx_a, idx_b, score, decisive in pairs:
                rec_a, rec_b = source_a[idx_a], source_b[idx_b]
                is_auto = score >= self.cfg.tau_high and decisive
                matched_a_indices.add(idx_a)
                matched_b_indices.add(idx_b)
                amt_diff = abs(rec_a.amount - rec_b.amount)
                date_diff = abs((rec_a.date - rec_b.date).days)
                ref_note = ", reference-linked" if self._ref_match(rec_a, rec_b) else ""
                if is_auto:
                    reason = None
                elif score >= self.cfg.tau_high:
                    reason = "AMBIGUOUS_MULTI_MATCH"
                else:
                    reason = "BELOW_AUTO_THRESHOLD"
                matches.append(
                    ReconciliationMatch(
                        match_id=f"MCH-{match_counter:05d}",
                        tier=MatchTier.TIER_2_FUZZY,
                        status=MatchStatus.MATCHED if is_auto else MatchStatus.PARTIAL_MATCH,
                        confidence=round(score, 4) if is_auto else round(min(score, self.cfg.tau_high - 0.01), 4),
                        record_a=rec_a,
                        records_b=[rec_b],
                        amount_diff=amt_diff,
                        date_diff_days=date_diff,
                        jaccard_similarity=self.jaccard_similarity(rec_a.description, rec_b.description),
                        severity=ExceptionSeverity.NONE if is_auto else ExceptionSeverity.LOW,
                        reason_code=reason,
                        notes=(
                            f"Fuzzy match (Score={score:.2f}, amt_diff=₹{amt_diff:.2f}, "
                            f"date_diff={date_diff}d{ref_note}"
                            + ("" if (is_auto or score < self.cfg.tau_high) else "; competing candidates, no decisive evidence")
                            + ")"
                        ),
                    )
                )
                match_counter += 1

        # ----------------------------------------------------------------------
        # Tier 2a: auto-accept fuzzy pass (score >= tau_high only)
        # ----------------------------------------------------------------------
        ua = [i for i in range(len(source_a)) if i not in matched_a_indices]
        ub = [i for i in range(len(source_b)) if i not in matched_b_indices]
        _apply_fuzzy([
            p for p in self._fuzzy_pass(source_a, source_b, ua, ub, self.cfg.tau_high)
            if p[2] >= self.cfg.tau_high and p[3]
        ])
        logger.info(f"After Tier 2a, total matches: {len(matches)}")

        # ----------------------------------------------------------------------
        # Tier 3: Subset-Sum Split Matching (1 ledger entry -> many comparator entries)
        # Runs BEFORE the review-band fuzzy pass so a weak 1:1 candidate cannot consume
        # one part of a split.
        # ----------------------------------------------------------------------
        still_unresolved_a = [i for i in range(len(source_a)) if i not in matched_a_indices]
        still_unresolved_b = [i for i in range(len(source_b)) if i not in matched_b_indices]

        for idx_a in list(still_unresolved_a):
            rec_a = source_a[idx_a]
            eps = self._amount_tolerance(rec_a.amount)

            candidates_b = [
                i for i in still_unresolved_b
                if self._dir_ok(rec_a.direction, source_b[i].direction)
                and abs((source_b[i].date - rec_a.date).days) <= self.cfg.date_window_days * 2
                and source_b[i].amount < rec_a.amount + eps
            ]
            # Reference-linked candidates first, then date proximity; cap to bound the search.
            candidates_b.sort(
                key=lambda i: (
                    not self._ref_match(rec_a, source_b[i]),
                    abs((source_b[i].date - rec_a.date).days),
                )
            )
            candidates_b = candidates_b[:20]

            best = None
            for k in range(2, min(self.cfg.max_split_k + 1, len(candidates_b) + 1)):
                # Tight per-part tolerance: a split must add up almost exactly.
                split_eps = min(eps, self.cfg.split_eps_per_part * k)
                for combo in itertools.combinations(candidates_b, k):
                    total_split = sum(source_b[i].amount for i in combo)
                    diff = abs(total_split - rec_a.amount)
                    if diff > split_eps:
                        continue
                    parts = [source_b[i] for i in combo]
                    ref_hits = sum(1 for b in parts if self._ref_match(rec_a, b))
                    mean_jac = sum(self.jaccard_similarity(rec_a.description, b.description) for b in parts) / k
                    max_gap = max(abs((b.date - rec_a.date).days) for b in parts)
                    rank = (ref_hits, mean_jac, -max_gap, -diff)
                    if best is None or rank > best[0]:
                        best = (rank, combo, diff, ref_hits, mean_jac, max_gap)
                if best is not None:
                    break  # prefer the split with the fewest parts

            if best is None:
                continue

            _, combo, diff, ref_hits, mean_jac, max_gap = best
            strong = ref_hits == len(combo)   # every part carries the ledger entry's reference
            matched_a_indices.add(idx_a)
            for i in combo:
                matched_b_indices.add(i)
                still_unresolved_b.remove(i)

            matches.append(
                ReconciliationMatch(
                    match_id=f"MCH-{match_counter:05d}",
                    tier=MatchTier.TIER_3_SPLIT,
                    status=MatchStatus.MATCHED if strong else MatchStatus.PARTIAL_MATCH,
                    confidence=self.cfg.split_confidence if strong else self.cfg.split_partial_confidence,
                    record_a=rec_a,
                    records_b=[source_b[i] for i in combo],
                    amount_diff=diff,
                    date_diff_days=max_gap,
                    jaccard_similarity=mean_jac,
                    severity=ExceptionSeverity.LOW,
                    reason_code=None if strong else "SPLIT_WEAK_EVIDENCE",
                    notes=(
                        f"Split match: 1 entry in A = {len(combo)} entries in B "
                        + ("(all parts reference-linked)." if strong
                           else "(amounts reconcile but no shared reference; flagged for review).")
                    ),
                )
            )
            match_counter += 1

        logger.info(f"After Tier 3, total matches: {len(matches)}")

        # ----------------------------------------------------------------------
        # Tier 2b: review-band fuzzy pass (tau_low <= score < tau_high) on what remains
        # ----------------------------------------------------------------------
        ua = [i for i in range(len(source_a)) if i not in matched_a_indices]
        ub = [i for i in range(len(source_b)) if i not in matched_b_indices]
        _apply_fuzzy(self._fuzzy_pass(source_a, source_b, ua, ub, self.cfg.tau_low))
        logger.info(f"After Tier 2b, total matches: {len(matches)}")

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

        tier_1_count = sum(1 for m in matches if m.tier == MatchTier.TIER_1_EXACT and m.status == MatchStatus.MATCHED)
        tier_2_count = sum(1 for m in matches if m.tier == MatchTier.TIER_2_FUZZY and m.status == MatchStatus.MATCHED)
        tier_3_count = sum(1 for m in matches if m.tier == MatchTier.TIER_3_SPLIT and m.status == MatchStatus.MATCHED)
        partial_count = sum(1 for m in matches if m.status == MatchStatus.PARTIAL_MATCH)
        unmatched_a_count = len(final_unresolved_a)

        # Decomposed rates: auto_resolved (Tiers 1-3 fully matched) + review_required (partial matches) == match_rate
        auto_resolved_count = tier_1_count + tier_2_count + tier_3_count
        match_count = auto_resolved_count + partial_count

        match_rate = round((match_count / n_total) * 100, 2)
        auto_resolved_rate = round((auto_resolved_count / n_total) * 100, 2)
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
        """
        Diagnoses an unmatched ledger record. A variance diagnosis (timing delay or amount
        discrepancy) requires evidence that a specific comparator record is the counterpart:
        a shared reference, or corroborating narration/date within bounded limits. Anything
        else is reported as a missing counterpart rather than a misleading variance.
        """
        cfg = self.cfg
        valid_b = [b for b in candidates_b if self._dir_ok(rec_a.direction, b.direction)]
        if not valid_b:
            return (
                ExceptionSeverity.HIGH,
                "MISSING_CORRESPONDING_RECORD",
                "No transaction with corresponding accounting direction found in comparator record set.",
            )

        tol = self._amount_tolerance(rec_a.amount)
        ref_linked = [b for b in valid_b if self._ref_match(rec_a, b)]
        others = [b for b in valid_b if b not in ref_linked]

        # 1) A reference-linked counterpart exists: diagnose the variance against it.
        for b in ref_linked:
            amt_diff = abs(rec_a.amount - b.amount)
            days = abs((rec_a.date - b.date).days)
            if amt_diff <= tol and days > cfg.timing_discrepancy_days:
                return (
                    ExceptionSeverity.MEDIUM,
                    "TIMING_DELAY",
                    f"Reference-linked candidate {b.record_id} matches in amount, but dated {days} days apart.",
                )
            pct = amt_diff / max(rec_a.amount, 1.0)
            if amt_diff > tol and pct > cfg.high_amount_discrepancy_pct:
                return (
                    ExceptionSeverity.HIGH,
                    "AMOUNT_DISCREPANCY",
                    f"Reference-linked candidate {b.record_id} differs in amount by {pct*100:.1f}%.",
                )

        # 2) No reference link: require corroborating, bounded evidence.
        for b in others:
            amt_diff = abs(rec_a.amount - b.amount)
            days = abs((rec_a.date - b.date).days)
            if amt_diff <= tol and cfg.timing_discrepancy_days < days <= cfg.timing_max_days:
                return (
                    ExceptionSeverity.MEDIUM,
                    "TIMING_DELAY",
                    f"Amount matches candidate {b.record_id}, but date discrepancy is {days} days.",
                )

        for b in others:
            days = abs((rec_a.date - b.date).days)
            if days > cfg.date_window_days:
                continue
            pct = abs(rec_a.amount - b.amount) / max(rec_a.amount, 1.0)
            if (
                cfg.high_amount_discrepancy_pct < pct <= cfg.amount_discrepancy_max_pct
                and self.jaccard_similarity(rec_a.description, b.description) >= cfg.discrepancy_min_jaccard
            ):
                return (
                    ExceptionSeverity.HIGH,
                    "AMOUNT_DISCREPANCY",
                    f"Date and narration align with candidate {b.record_id}, but amount differs by {pct*100:.1f}%.",
                )

        return (
            ExceptionSeverity.HIGH,
            "MISSING_CORRESPONDING_RECORD",
            "No plausible counterpart (no shared reference, matching amount, or corroborated variance) in comparator set.",
        )
