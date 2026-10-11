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
    assert m.status == MatchStatus.MATCHED
    assert m.amount_diff == 0.0


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
