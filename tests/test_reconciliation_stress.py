"""
Randomized robustness tests for the reconciliation engine.

Unlike the hand-built benchmark batches, these generate many noisy ledgers with heavy
amount collisions (round-number payments), date jitter, noisy narrations and unrecorded
ledger entries, and measure the property that matters most to a controller: a wrong
pairing must (almost) never be auto-approved.
"""
import random
from datetime import date, timedelta

import pytest

from modules.bank_statement_loader import StandardizedRecord, Direction, RecordSource
from modules.reconciliation_engine import ReconciliationEngine, MatchStatus

NAMES = ["Sharma", "Kumar", "Iyer", "Reddy", "Gupta", "Nair", "Singh", "Das"]
KINDS = ["rent", "salary", "freight", "utility", "insurance", "legal fees"]


def _make_batch(seed, use_refs, collide=0.5, noisy_p=0.35, miss=0.12, n=60):
    r = random.Random(seed)
    a_recs, b_recs, truth = [], [], {}
    base = date(2026, 4, 1)
    pool = [10000.0, 25000.0, 12500.0]
    for i in range(n):
        amt = r.choice(pool) if r.random() < collide else round(r.uniform(5000, 90000), 2)
        d = base + timedelta(days=r.randint(0, 6))
        nm, kd = r.choice(NAMES), r.choice(KINDS)
        ref = f"REF-{i:04d}" if use_refs else None
        a = StandardizedRecord(f"A{i}", RecordSource.TALLY, d, nm, amt, Direction.DEBIT,
                               f"{kd} payment {nm}", account_code=ref)
        a_recs.append(a)
        if r.random() < miss:
            continue                                   # ledger entry with no bank counterpart
        jit = timedelta(days=r.choice([0, 0, 1, 2]))
        b_amt = amt if r.random() < 0.7 else round(amt + r.uniform(-0.9, 0.9), 2)
        desc = f"NEFT {r.randint(1000, 9999)}" if r.random() < noisy_p else f"NEFT {nm} {kd}"
        b = StandardizedRecord(f"B{i}", RecordSource.BANK, d + jit, nm, b_amt, Direction.CREDIT,
                               desc, account_code=ref)
        b_recs.append(b)
        truth[a.record_id] = b.record_id
    r.shuffle(a_recs)
    r.shuffle(b_recs)
    return a_recs, b_recs, truth


def _tally(use_refs, trials=25):
    auto = silent = review = review_wrong = 0
    engine = ReconciliationEngine()
    for seed in range(trials):
        a_recs, b_recs, truth = _make_batch(seed, use_refs)
        for m in engine.reconcile(a_recs, b_recs).matches:
            if not m.record_a or m.status == MatchStatus.UNMATCHED:
                continue
            rid = m.record_a.record_id
            ok = rid in truth and {b.record_id for b in m.records_b} == {truth[rid]}
            if m.status == MatchStatus.MATCHED:
                auto += 1
                silent += 0 if ok else 1
            else:
                review += 1
                review_wrong += 0 if ok else 1
    return auto, silent, review, review_wrong


def test_stress_with_references_has_no_silent_errors():
    auto, silent, _, _ = _tally(use_refs=True)
    assert auto > 0
    assert silent == 0


def test_stress_without_references_silent_error_rate_below_one_percent():
    auto, silent, review, review_wrong = _tally(use_refs=False)
    assert auto > 0 and review > 0
    assert silent / auto < 0.01
    # most uncertain pairings are surfaced for review rather than auto-approved
    assert review_wrong > silent


def test_exact_hit_with_nearby_competitor_is_not_auto_approved_without_evidence():
    """Same amount/date as one bank line, but another bank line one day away competes."""
    d = date(2026, 4, 1)
    a = StandardizedRecord("A1", RecordSource.TALLY, d, "x", 10000.0, Direction.DEBIT, "Payment")
    b1 = StandardizedRecord("B1", RecordSource.BANK, d, "x", 10000.0, Direction.CREDIT, "NEFT 5521")
    b2 = StandardizedRecord("B2", RecordSource.BANK, d + timedelta(days=1), "x", 10000.0,
                            Direction.CREDIT, "NEFT 7734")
    res = ReconciliationEngine().reconcile([a], [b1, b2])
    m = next(m for m in res.matches if m.record_a)
    assert m.status == MatchStatus.PARTIAL_MATCH


def test_isolated_exact_hit_is_auto_approved():
    d = date(2026, 4, 1)
    a = StandardizedRecord("A1", RecordSource.TALLY, d, "x", 10000.0, Direction.DEBIT, "Payment")
    b = StandardizedRecord("B1", RecordSource.BANK, d, "x", 10000.0, Direction.CREDIT, "NEFT 5521")
    m = next(m for m in ReconciliationEngine().reconcile([a], [b]).matches if m.record_a)
    assert m.status == MatchStatus.MATCHED
