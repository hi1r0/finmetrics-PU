import io
import pytest
from datetime import date, timedelta
import tempfile
from pathlib import Path
import pandas as pd

from modules.bank_statement_loader import (
    BankStatementLoader,
    StandardizedRecord,
    Direction,
    RecordSource,
)
from modules.reconciliation_config import ReconciliationConfig
from modules.reconciliation_engine import (
    ReconciliationEngine,
    MatchTier,
    MatchStatus,
    ExceptionSeverity,
)
from modules.reconciliation_report import ReconciliationReporter
from modules.reconciliation_benchmark import (
    generate_synthetic_benchmark_batch,
    generate_adversarial_benchmark_batch,
    evaluate_reconciliation_benchmark,
)


def test_bank_statement_loader_credit_column_and_nan():
    """Verify bank loader correctly parses credit column without 'CR' matching in 'DESCRIPTION'."""
    csv_content = (
        "Date,Description,Debit,Credit,Balance\n"
        "2026-04-01,Customer payment from Acme Corp,,50000.00,150000.00\n"
        "2026-04-02,Vendor payout to Supply Co,12000.00,,138000.00\n"
    )
    buffer = io.StringIO(csv_content)
    records = BankStatementLoader.load_bank_statement(buffer)

    assert len(records) == 2

    # Record 1: Deposit / Credit
    rec_cr = records[0]
    assert rec_cr.amount == 50000.00
    assert rec_cr.direction == Direction.CREDIT
    assert "Acme Corp" in rec_cr.description

    # Record 2: Withdrawal / Debit
    rec_dr = records[1]
    assert rec_dr.amount == 12000.00
    assert rec_dr.direction == Direction.DEBIT
    assert "Supply Co" in rec_dr.description


def test_tier_1_exact_match():
    """Verify Tier 1 exact deterministic matching with accounting direction inversion."""
    engine = ReconciliationEngine()
    d = date(2026, 4, 15)

    rec_a = StandardizedRecord(
        record_id="TLY-001",
        source=RecordSource.TALLY,
        date=d,
        account_label="Office Rent Expense",
        amount=50000.0,
        direction=Direction.DEBIT,
        description="April 2026 Office Rent",
    )
    rec_b = StandardizedRecord(
        record_id="BNK-001",
        source=RecordSource.BANK,
        date=d,
        account_label="Commercial Landlord",
        amount=50000.0,
        direction=Direction.CREDIT,  # Inverted for bank statement
        description="NEFT RENT APR 2026",
    )

    result = engine.reconcile([rec_a], [rec_b])

    assert result.total_records_a == 1
    assert result.match_rate == 100.0
    assert len(result.matches) == 1
    m = result.matches[0]
    assert m.tier == MatchTier.TIER_1_EXACT
    assert m.confidence == 1.0
    assert m.status == MatchStatus.MATCHED
    assert m.amount_diff == 0.0


def test_tier_1_ambiguous_multi_match_disambiguation():
    """Verify Tier 1 uses description similarity to avoid pairing wrong records when date & amount are identical."""
    engine = ReconciliationEngine()
    d = date(2026, 4, 15)
    amt = 10000.00

    # Two distinct ledger disbursements on the same day for the same amount
    tly_rent = StandardizedRecord(
        record_id="TLY-RENT",
        source=RecordSource.TALLY,
        date=d,
        account_label="Office Rent",
        amount=amt,
        direction=Direction.DEBIT,
        description="Monthly office rent payment Landlord Sharma",
    )
    tly_salary = StandardizedRecord(
        record_id="TLY-SALARY",
        source=RecordSource.TALLY,
        date=d,
        account_label="Salary Expense",
        amount=amt,
        direction=Direction.DEBIT,
        description="Monthly salary disbursement to Ramesh Kumar",
    )

    # Bank records in swapped order
    bnk_salary = StandardizedRecord(
        record_id="BNK-SALARY",
        source=RecordSource.BANK,
        date=d,
        account_label="Ramesh Kumar",
        amount=amt,
        direction=Direction.CREDIT,
        description="IMPS Salary disbursement Ramesh Kumar",
    )
    bnk_rent = StandardizedRecord(
        record_id="BNK-RENT",
        source=RecordSource.BANK,
        date=d,
        account_label="Landlord Sharma",
        amount=amt,
        direction=Direction.CREDIT,
        description="NEFT Rent payout Landlord Sharma",
    )

    # Reconcile with shuffled bank records
    result = engine.reconcile([tly_rent, tly_salary], [bnk_salary, bnk_rent])

    assert len(result.matches) == 2
    match_map = {m.record_a.record_id: m.records_b[0].record_id for m in result.matches if m.record_a}

    # Verify correct pairings by narration rather than arbitrary pop(0)
    assert match_map["TLY-RENT"] == "BNK-RENT"
    assert match_map["TLY-SALARY"] == "BNK-SALARY"


def test_tier_2_fuzzy_match():
    """Verify Tier 2 fuzzy matching with date lag and slight rounding."""
    cfg = ReconciliationConfig(epsilon_abs=2.0, date_window_days=3)
    engine = ReconciliationEngine(config=cfg)

    d_a = date(2026, 4, 10)
    d_b = date(2026, 4, 12)  # 2 days lag

    rec_a = StandardizedRecord(
        record_id="TLY-002",
        source=RecordSource.TALLY,
        date=d_a,
        account_label="Tata Consumer Products Ltd",
        amount=25000.0,
        direction=Direction.DEBIT,
        description="Payment to Tata Consumer Products invoice 450",
    )
    rec_b = StandardizedRecord(
        record_id="BNK-002",
        source=RecordSource.BANK,
        date=d_b,
        account_label="Tata Consumer",
        amount=25001.20,  # ₹1.20 bank charge diff
        direction=Direction.CREDIT,  # Inverted for bank statement
        description="RTGS to Tata Consumer Products",
    )

    result = engine.reconcile([rec_a], [rec_b])

    assert len(result.matches) == 1
    m = result.matches[0]
    assert m.tier == MatchTier.TIER_2_FUZZY
    assert m.confidence >= cfg.tau_low
    assert m.status in [MatchStatus.MATCHED, MatchStatus.PARTIAL_MATCH]
    assert m.date_diff_days == 2


def test_tier_3_split_match():
    """Verify Tier 3 subset sum split transaction detection (1 to 2 records)."""
    cfg = ReconciliationConfig(epsilon_abs=1.0, date_window_days=3)
    engine = ReconciliationEngine(config=cfg)

    d = date(2026, 4, 20)

    # 1 invoice of ₹60,000 paid in two tranches of ₹35,000 and ₹25,000
    rec_a = StandardizedRecord(
        record_id="TLY-INV-100",
        source=RecordSource.TALLY,
        date=d,
        account_label="Apex Wholesale",
        amount=60000.0,
        direction=Direction.CREDIT,
        description="Settlement invoice 100",
    )
    rec_b1 = StandardizedRecord(
        record_id="BNK-PART-1",
        source=RecordSource.BANK,
        date=d,
        account_label="Apex Wholesale",
        amount=35000.0,
        direction=Direction.DEBIT,  # Inverted for bank
        description="Apex tranche 1",
    )
    rec_b2 = StandardizedRecord(
        record_id="BNK-PART-2",
        source=RecordSource.BANK,
        date=d + timedelta(days=1),
        account_label="Apex Wholesale",
        amount=25000.0,
        direction=Direction.DEBIT,  # Inverted for bank
        description="Apex tranche 2",
    )

    result = engine.reconcile([rec_a], [rec_b1, rec_b2])

    assert len(result.matches) == 1
    m = result.matches[0]
    assert m.tier == MatchTier.TIER_3_SPLIT
    assert len(m.records_b) == 2
    # No shared reference on the parts: amounts reconcile exactly, but the split is not
    # auto-approved; it is routed to the review queue.
    assert m.status == MatchStatus.PARTIAL_MATCH
    assert m.reason_code == "SPLIT_WEAK_EVIDENCE"
    assert m.amount_diff == 0.0


def test_tier_3_split_match_auto_approved_with_shared_reference():
    d = date(2026, 4, 20)
    rec_a = StandardizedRecord("TLY-INV-100", RecordSource.TALLY, d, "Apex", 60000.0,
                               Direction.CREDIT, "Settlement invoice 100", account_code="INV-100")
    parts = [
        StandardizedRecord("BNK-PART-1", RecordSource.BANK, d, "Apex", 35000.0, Direction.DEBIT,
                           "Apex tranche 1", account_code="INV-100"),
        StandardizedRecord("BNK-PART-2", RecordSource.BANK, d + timedelta(days=1), "Apex", 25000.0,
                           Direction.DEBIT, "Apex tranche 2", account_code="INV-100"),
    ]
    m = ReconciliationEngine().reconcile([rec_a], parts).matches[0]
    assert m.tier == MatchTier.TIER_3_SPLIT
    assert m.status == MatchStatus.MATCHED


def test_direction_inversion_config_toggle():
    """Verify invert_comparator_direction configuration behaves correctly."""
    d = date(2026, 4, 1)
    rec_a = StandardizedRecord(
        record_id="A-1",
        source=RecordSource.TALLY,
        date=d,
        account_label="Test",
        amount=100.0,
        direction=Direction.DEBIT,
        description="Test Dr",
    )
    rec_b_credit = StandardizedRecord(
        record_id="B-1",
        source=RecordSource.BANK,
        date=d,
        account_label="Test",
        amount=100.0,
        direction=Direction.CREDIT,
        description="Test Cr",
    )

    # Default engine (invert_comparator_direction=True): DEBIT matches CREDIT
    engine_inverted = ReconciliationEngine()
    res1 = engine_inverted.reconcile([rec_a], [rec_b_credit])
    assert res1.match_rate == 100.0

    # Non-inverted engine (invert_comparator_direction=False): DEBIT does not match CREDIT
    cfg_direct = ReconciliationConfig(invert_comparator_direction=False)
    engine_direct = ReconciliationEngine(config=cfg_direct)
    res2 = engine_direct.reconcile([rec_a], [rec_b_credit])
    assert res2.match_rate == 0.0


def test_exception_classification():
    """Verify that unmatchable records are classified as severity-ranked exceptions."""
    engine = ReconciliationEngine()
    d = date(2026, 4, 1)

    rec_a = StandardizedRecord(
        record_id="TLY-ERR-999",
        source=RecordSource.TALLY,
        date=d,
        account_label="Ghost Supplier",
        amount=85000.0,
        direction=Direction.DEBIT,
        description="Phantom expense entry",
    )

    result = engine.reconcile([rec_a], [])

    assert result.match_rate == 0.0
    assert result.exception_rate == 100.0
    assert len(result.matches) == 1
    exc = result.matches[0]
    assert exc.tier == MatchTier.UNRESOLVED
    assert exc.status == MatchStatus.UNMATCHED
    assert exc.severity in [ExceptionSeverity.HIGH, ExceptionSeverity.MEDIUM]
    assert exc.reason_code is not None


def test_synthetic_60_record_benchmark_evaluation():
    """Verify 60-record synthetic ground truth evaluation achieves high precision, recall, and pair accuracy."""
    engine = ReconciliationEngine()
    eval_res = evaluate_reconciliation_benchmark(engine, batch_type="standard")

    metrics = eval_res["metrics"]
    assert metrics["total_records"] == 60
    assert metrics["precision"] >= 0.90
    assert metrics["recall"] >= 0.90
    assert metrics["accuracy"] >= 0.90
    assert metrics["pair_accuracy"] >= 0.90

    # Ensure all four decomposed rates are computed
    result = eval_res["result"]
    assert result.match_rate > 80.0
    assert result.auto_resolved_rate >= 65.0
    assert result.exception_rate < 20.0
    assert not eval_res["confusion_matrix"].empty


def test_adversarial_benchmark_evaluation():
    """Verify adversarial stress-test benchmark measures pair accuracy and honestly flags exceptions."""
    engine = ReconciliationEngine()
    eval_res = evaluate_reconciliation_benchmark(engine, batch_type="adversarial")

    metrics = eval_res["metrics"]
    assert metrics["total_records"] > 40
    # Adversarial dataset has severe timing delays and amount discrepancies that must be flagged
    assert metrics["actual_exceptions"] >= 10
    assert metrics["pair_accuracy"] > 0.80

    result = eval_res["result"]
    # Decomposed rates must hold mathematically
    assert abs((result.match_rate + result.exception_rate) - 100.0) < 0.1
    assert abs(result.match_rate - (result.auto_resolved_rate + result.review_required_rate)) < 0.1


def test_reconciliation_reporter_exports():
    """Verify Excel and JSON report generation."""
    engine = ReconciliationEngine()
    source_a, source_b, _ = generate_synthetic_benchmark_batch(seed=123)
    result = engine.reconcile(source_a, source_b)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        excel_file = tmp_path / "recon_report.xlsx"
        json_file = tmp_path / "recon_report.json"

        ReconciliationReporter.export_excel(result, excel_file)
        ReconciliationReporter.export_json(result, json_file)

        assert excel_file.exists() and excel_file.stat().st_size > 1000
        assert json_file.exists() and json_file.stat().st_size > 1000


# ──────────────────────────────────────────────────────────────────────────────
# Audit round 3: reference evidence, order-independent ambiguity, evidence-gated
# splits, bounded reason codes, and silent-error containment
# ──────────────────────────────────────────────────────────────────────────────

D0 = date(2026, 4, 1)


def _rec(rid, src, desc, amt, dt=D0, direction=Direction.DEBIT, ref=None):
    return StandardizedRecord(
        record_id=rid, source=src, date=dt, account_label=desc[:20],
        amount=amt, direction=direction, description=desc, account_code=ref,
    )


def test_reference_resolves_decoy_over_better_dated_lookalike():
    """A shared reference must beat a same-day, near-amount decoy with a different reference."""
    a = _rec("A1", RecordSource.TALLY, "Remittance to Distributor K invoice 4000", 50000.00, ref="INV-4000")
    b_true = _rec("B-TRUE", RecordSource.BANK, "CMS vendor payout charges adjusted", 50000.60,
                  dt=D0 + timedelta(days=1), direction=Direction.CREDIT, ref="INV-4000")
    b_decoy = _rec("B-DECOY", RecordSource.BANK, "Remittance to Distributor invoice", 50000.50,
                   direction=Direction.CREDIT, ref="DCY-1")
    res = ReconciliationEngine().reconcile([a], [b_true, b_decoy])
    pair = next(m for m in res.matches if m.record_a and m.record_a.record_id == "A1")
    assert [b.record_id for b in pair.records_b] == ["B-TRUE"]
    assert pair.status == MatchStatus.MATCHED


def test_reference_inside_narration_counts_as_link():
    a = _rec("A1", RecordSource.TALLY, "Payment", 12000.0, ref="CHQ778812")
    b = _rec("B1", RecordSource.BANK, "CHQ778812 clearing", 12000.0,
             dt=D0 + timedelta(days=2), direction=Direction.CREDIT, ref=None)
    assert ReconciliationEngine._ref_match(a, b) is True


def test_generic_reference_values_never_link():
    a = _rec("A1", RecordSource.TALLY, "x", 1.0, ref="NIL")
    b = _rec("B1", RecordSource.BANK, "y", 1.0, ref="NIL")
    assert ReconciliationEngine._ref_match(a, b) is False


def test_ambiguity_flag_is_order_independent():
    """Two identical ledger entries vs two uninformative bank lines: BOTH must go to review."""
    a = [_rec(f"A{i}", RecordSource.TALLY, "Payment", 10000.0) for i in (1, 2)]
    b = [_rec("B1", RecordSource.BANK, "NEFT 8841", 10000.0, direction=Direction.CREDIT),
         _rec("B2", RecordSource.BANK, "NEFT 9920", 10000.0, direction=Direction.CREDIT)]
    res = ReconciliationEngine().reconcile(a, b)
    statuses = [m.status for m in res.matches if m.record_a]
    assert statuses == [MatchStatus.PARTIAL_MATCH, MatchStatus.PARTIAL_MATCH]


def test_split_without_shared_reference_goes_to_review():
    a = _rec("A1", RecordSource.TALLY, "Consolidated settlement", 60000.0, direction=Direction.CREDIT)
    b = [_rec("B1", RecordSource.BANK, "Part one", 33000.0, direction=Direction.DEBIT),
         _rec("B2", RecordSource.BANK, "Part two", 27000.0, dt=D0 + timedelta(days=1), direction=Direction.DEBIT)]
    res = ReconciliationEngine().reconcile([a], b)
    m = next(m for m in res.matches if m.record_a)
    assert m.tier == MatchTier.TIER_3_SPLIT
    assert m.status == MatchStatus.PARTIAL_MATCH
    assert m.reason_code == "SPLIT_WEAK_EVIDENCE"


def test_split_cross_pairing_is_prevented():
    """Two splits whose totals differ by <0.1% must not swap bank parts."""
    a1 = _rec("A1", RecordSource.TALLY, "Client one settlement", 60000.00, direction=Direction.CREDIT, ref="SPL-1")
    a2 = _rec("A2", RecordSource.TALLY, "Client two settlement", 60020.00, direction=Direction.CREDIT, ref="SPL-2")
    b = [
        _rec("B1a", RecordSource.BANK, "installment 1", 36000.00, direction=Direction.DEBIT, ref="SPL-1"),
        _rec("B1b", RecordSource.BANK, "installment 2", 24000.00, dt=D0 + timedelta(days=1), direction=Direction.DEBIT, ref="SPL-1"),
        _rec("B2a", RecordSource.BANK, "installment 1", 36020.00, direction=Direction.DEBIT, ref="SPL-2"),
        _rec("B2b", RecordSource.BANK, "installment 2", 24000.00, dt=D0 + timedelta(days=1), direction=Direction.DEBIT, ref="SPL-2"),
    ]
    res = ReconciliationEngine().reconcile([a1, a2], b)
    pairs = {m.record_a.record_id: {x.record_id for x in m.records_b} for m in res.matches if m.record_a}
    assert pairs["A1"] == {"B1a", "B1b"}
    assert pairs["A2"] == {"B2a", "B2b"}


def test_unreferenced_far_amount_is_missing_not_discrepancy():
    """A leftover bank line 3x the amount is a different transaction, not an 'amount discrepancy'."""
    a = _rec("A1", RecordSource.TALLY, "Phantom ledger disbursement", 20000.0)
    b = _rec("B1", RecordSource.BANK, "Unrelated supplier payout", 60000.0, direction=Direction.CREDIT)
    res = ReconciliationEngine().reconcile([a], [b])
    exc = next(m for m in res.matches if m.record_a and m.status == MatchStatus.UNMATCHED)
    assert exc.reason_code == "MISSING_CORRESPONDING_RECORD"


def test_referenced_amount_variance_is_discrepancy():
    a = _rec("A1", RecordSource.TALLY, "Vendor payment", 50000.0, ref="MIS-9")
    b = _rec("B1", RecordSource.BANK, "Vendor payment", 54500.0, direction=Direction.CREDIT, ref="MIS-9")
    res = ReconciliationEngine().reconcile([a], [b])
    exc = next(m for m in res.matches if m.record_a and m.status == MatchStatus.UNMATCHED)
    assert exc.reason_code == "AMOUNT_DISCREPANCY"


def test_referenced_timing_gap_is_timing_delay():
    a = _rec("A1", RecordSource.TALLY, "Cheque issue", 30000.0, ref="LAG-3")
    b = _rec("B1", RecordSource.BANK, "Cheque clearing", 30000.0, dt=D0 + timedelta(days=16),
             direction=Direction.CREDIT, ref="LAG-3")
    res = ReconciliationEngine().reconcile([a], [b])
    exc = next(m for m in res.matches if m.record_a and m.status == MatchStatus.UNMATCHED)
    assert exc.reason_code == "TIMING_DELAY"


@pytest.mark.parametrize("batch_type", ["standard", "adversarial"])
@pytest.mark.parametrize("reference_mode", ["linked", "none"])
def test_no_silent_wrong_auto_matches(batch_type, reference_mode):
    """
    The key safety property: a wrong pairing may exist, but it must never be auto-approved.
    Holds with and without reference evidence.
    """
    out = evaluate_reconciliation_benchmark(
        ReconciliationEngine(), batch_type=batch_type, reference_mode=reference_mode
    )
    m = out["metrics"]
    assert m["silent_wrong_auto_matches"] == 0
    assert m["auto_resolved_precision"] == 1.0
    assert m["reason_code_accuracy"] == 1.0


@pytest.mark.parametrize("batch_type", ["standard", "adversarial"])
def test_linked_benchmark_pair_accuracy_perfect(batch_type):
    out = evaluate_reconciliation_benchmark(ReconciliationEngine(), batch_type=batch_type, reference_mode="linked")
    assert out["metrics"]["pair_accuracy"] == 1.0


def test_unreferenced_adversarial_errors_are_contained_in_review():
    """Without references, decoys can win a pairing, but every such error must sit in the review queue."""
    out = evaluate_reconciliation_benchmark(ReconciliationEngine(), batch_type="adversarial", reference_mode="none")
    m = out["metrics"]
    wrong = m["actual_matches"] - m["correctly_paired_records"]
    assert wrong == m["wrong_pairs_in_review"]
