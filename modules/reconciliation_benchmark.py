"""
reconciliation_benchmark.py
===========================
Generates verified synthetic reconciliation test batches with ground-truth labels and pairings.
Evaluates engine precision, recall, pair accuracy, and confusion matrix against known ground truth.
Includes both a standard clean evaluation batch and an adversarial stress-test batch with decoys,
same-amount/same-day duplicates, timing discrepancies, and orphan records.
"""

from datetime import date, timedelta
import random
from typing import Dict, List, Tuple, Any, Optional

import pandas as pd

from modules.bank_statement_loader import StandardizedRecord, Direction, RecordSource
from modules.reconciliation_engine import ReconciliationEngine, MatchStatus, ExceptionSeverity


def generate_synthetic_benchmark_batch(
    base_date: date = date(2026, 4, 1),
    seed: int = 42,
    invert_direction: bool = True,
    return_pairs: bool = False,
) -> Any:
    """
    Constructs a 60-record synthetic ground truth test batch:
    - 40 Exact Matches (identical amount, date, direction)
    - 10 Fuzzy Matches (slight amount rounding ±₹0.50, date lag 1-2 days, narration abbreviation)
    - 5 Split Matches (1 ledger entry split across 2 bank entries)
    - 5 Deliberate Exceptions (missing records, unrecorded charges)

    If invert_direction=True (standard double-entry bookkeeping convention),
    Ledger Dr -> Bank Cr and Ledger Cr -> Bank Dr.
    """
    random.seed(seed)
    source_a: List[StandardizedRecord] = []
    source_b: List[StandardizedRecord] = []
    ground_truth_labels: Dict[str, str] = {}
    ground_truth_pairs: Dict[str, List[str]] = {}

    vendors = [
        "Reliance Retail Ltd", "Tata Consumer Products", "Hindustan Unilever",
        "Nestle India Ltd", "ITC Infotech", "Adani Wilmar", "Dabur India",
        "Godrej Consumer", "Marico Ltd", "Britannia Industries", "Apex Wholesale",
        "National Logistics Corp", "Metro Distribution", "Blue Dart Express"
    ]

    record_counter = 1

    def _bank_dir(lead_dir: Direction) -> Direction:
        if invert_direction:
            return Direction.CREDIT if lead_dir == Direction.DEBIT else Direction.DEBIT
        return lead_dir

    # 1. 40 Exact Matches
    for i in range(40):
        v = random.choice(vendors)
        amt = round(random.uniform(5000.0, 150000.0), 2)
        d = base_date + timedelta(days=(i % 25))
        lead_dir = Direction.DEBIT if (i % 3 != 0) else Direction.CREDIT
        bk_dir = _bank_dir(lead_dir)

        rec_a_id = f"TLY-EX-{record_counter:04d}"
        rec_b_id = f"BNK-EX-{record_counter:04d}"

        rec_a = StandardizedRecord(
            record_id=rec_a_id,
            source=RecordSource.TALLY,
            date=d,
            account_label=v,
            amount=amt,
            direction=lead_dir,
            description=f"Payment for invoice #{1000+i} to {v}",
            account_code=f"INV-{1000+i}",
        )
        rec_b = StandardizedRecord(
            record_id=rec_b_id,
            source=RecordSource.BANK,
            date=d,
            account_label=v,
            amount=amt,
            direction=bk_dir,
            description=f"NEFT/RTGS to {v} INV-{1000+i}",
            account_code=f"INV-{1000+i}",
        )

        source_a.append(rec_a)
        source_b.append(rec_b)
        ground_truth_labels[rec_a_id] = "MATCH"
        ground_truth_pairs[rec_a_id] = [rec_b_id]
        record_counter += 1

    # 2. 10 Fuzzy Matches (Date lag 1-2 days, amount diff ₹0.20 - ₹1.20, modified narration)
    for i in range(10):
        v = random.choice(vendors)
        base_amt = round(random.uniform(10000.0, 80000.0), 2)
        diff_amt = round(random.uniform(0.10, 1.20), 2)
        bank_amt = round(base_amt + diff_amt, 2)
        date_a = base_date + timedelta(days=5 + (i * 2))
        date_b = date_a + timedelta(days=random.choice([1, 2]))
        lead_dir = Direction.DEBIT
        bk_dir = _bank_dir(lead_dir)

        rec_a_id = f"TLY-FZ-{record_counter:04d}"
        rec_b_id = f"BNK-FZ-{record_counter:04d}"

        rec_a = StandardizedRecord(
            record_id=rec_a_id,
            source=RecordSource.TALLY,
            date=date_a,
            account_label=v,
            amount=base_amt,
            direction=lead_dir,
            description=f"Vendor disbursement to {v}",
            account_code=f"VEND-{2000+i}",
        )
        rec_b = StandardizedRecord(
            record_id=rec_b_id,
            source=RecordSource.BANK,
            date=date_b,
            account_label=v,
            amount=bank_amt,
            direction=bk_dir,
            description=f"CMS transfer {v[:8]} bank charges inc",
            account_code=f"VEND-{2000+i}",
        )

        source_a.append(rec_a)
        source_b.append(rec_b)
        ground_truth_labels[rec_a_id] = "MATCH"
        ground_truth_pairs[rec_a_id] = [rec_b_id]
        record_counter += 1

    # 3. 5 Split Matches (1 Ledger entry split into 2 bank deposits/payments)
    for i in range(5):
        v = random.choice(vendors)
        total_amt = round(random.uniform(30000.0, 90000.0), 2)
        part1 = round(total_amt * 0.6, 2)
        part2 = round(total_amt - part1, 2)
        d = base_date + timedelta(days=10 + i)
        lead_dir = Direction.CREDIT
        bk_dir = _bank_dir(lead_dir)

        rec_a_id = f"TLY-SP-{record_counter:04d}"
        b1_id = f"BNK-SP1-{record_counter:04d}"
        b2_id = f"BNK-SP2-{record_counter:04d}"

        rec_a = StandardizedRecord(
            record_id=rec_a_id,
            source=RecordSource.TALLY,
            date=d,
            account_label=v,
            amount=total_amt,
            direction=lead_dir,
            description=f"Bulk settlement from {v} invoice series {500+i}",
            account_code=f"SETTLE-{500+i}",
        )
        rec_b1 = StandardizedRecord(
            record_id=b1_id,
            source=RecordSource.BANK,
            date=d,
            account_label=v,
            amount=part1,
            direction=bk_dir,
            description=f"Part remittance 1 from {v}",
            account_code=f"SETTLE-{500+i}",
        )
        rec_b2 = StandardizedRecord(
            record_id=b2_id,
            source=RecordSource.BANK,
            date=d + timedelta(days=1),
            account_label=v,
            amount=part2,
            direction=bk_dir,
            description=f"Part remittance 2 from {v}",
            account_code=f"SETTLE-{500+i}",
        )

        source_a.append(rec_a)
        source_b.extend([rec_b1, rec_b2])
        ground_truth_labels[rec_a_id] = "MATCH"
        ground_truth_pairs[rec_a_id] = [b1_id, b2_id]
        record_counter += 1

    # 4. 5 Deliberate Unmatched Exceptions in Source A
    for i in range(5):
        v = random.choice(vendors)
        amt = round(random.uniform(15000.0, 60000.0), 2)
        d = base_date + timedelta(days=20 + i)

        rec_a_id = f"TLY-EXC-{record_counter:04d}"
        rec_a = StandardizedRecord(
            record_id=rec_a_id,
            source=RecordSource.TALLY,
            date=d,
            account_label=v,
            amount=amt,
            direction=Direction.DEBIT,
            description=f"Unreconciled ledger charge {v} with no bank counterpart",
            account_code=f"ERR-{900+i}",
        )
        source_a.append(rec_a)
        ground_truth_labels[rec_a_id] = "EXCEPTION"
        ground_truth_pairs[rec_a_id] = []
        record_counter += 1

    # Shuffle lists to prevent positional cheating
    random.shuffle(source_a)
    random.shuffle(source_b)

    if return_pairs:
        return source_a, source_b, ground_truth_labels, ground_truth_pairs
    return source_a, source_b, ground_truth_labels


def generate_adversarial_benchmark_batch(
    base_date: date = date(2026, 4, 1),
    seed: int = 101,
    invert_direction: bool = True,
    return_pairs: bool = False,
) -> Any:
    """
    Constructs an adversarial stress-test dataset designed to challenge reconciliation algorithms:
    1. 10 Ambiguous same-amount, same-day entries with distinct narrations (e.g. Rent vs Salary).
    2. 20 Standard exact matches.
    3. 10 Fuzzy matches with near-miss bank decoys inside tolerance.
    4. 5 Split transactions (1-to-2 subset-sum).
    5. 5 Severe Amount Discrepancies (>8% gap on matching date/party) -> EXCEPTION (AMOUNT_DISCREPANCY).
    6. 5 Severe Timing Delays (>14 days lag on identical amount) -> EXCEPTION (TIMING_DELAY).
    7. 5 Unrecorded ledger charges in Tally -> EXCEPTION (MISSING_CORRESPONDING_RECORD).
    8. 6 Bank-only orphan transactions (unrecorded bank interest, bank charges, POS fees).
    """
    random.seed(seed)
    source_a: List[StandardizedRecord] = []
    source_b: List[StandardizedRecord] = []
    ground_truth_labels: Dict[str, str] = {}
    ground_truth_pairs: Dict[str, List[str]] = {}

    def _bank_dir(lead_dir: Direction) -> Direction:
        if invert_direction:
            return Direction.CREDIT if lead_dir == Direction.DEBIT else Direction.DEBIT
        return lead_dir

    counter = 1

    # 1. Ambiguous same-day same-amount entries (5 pairs with identical date and amount ₹15,000)
    ambiguous_scenarios = [
        ("Office Rent Landlord Sharma", "NEFT Rent payment Landlord Sharma Apr"),
        ("Salary disbursement Ramesh Kumar", "IMPS Salary disbursement Ramesh Kumar"),
        ("Professional legal fees ABC Advisory", "NEFT Legal consultancy ABC Advisory"),
        ("BESCOM electricity bill payment", "BBPS BESCOM power bill utility payment"),
        ("Blue Dart courier freight charges", "POS Blue Dart Express logistics courier"),
    ]
    amb_date = base_date + timedelta(days=2)
    amb_amt = 15000.00
    for idx, (desc_a, desc_b) in enumerate(ambiguous_scenarios):
        rec_a_id = f"TLY-AMB-{counter:04d}"
        rec_b_id = f"BNK-AMB-{counter:04d}"
        lead_dir = Direction.DEBIT
        bk_dir = _bank_dir(lead_dir)

        rec_a = StandardizedRecord(
            record_id=rec_a_id,
            source=RecordSource.TALLY,
            date=amb_date,
            account_label=desc_a[:30],
            amount=amb_amt,
            direction=lead_dir,
            description=desc_a,
            account_code=f"AMB-{counter}",
        )
        rec_b = StandardizedRecord(
            record_id=rec_b_id,
            source=RecordSource.BANK,
            date=amb_date,
            account_label=desc_b[:30],
            amount=amb_amt,
            direction=bk_dir,
            description=desc_b,
            account_code=f"AMB-{counter}",
        )
        source_a.append(rec_a)
        source_b.append(rec_b)
        ground_truth_labels[rec_a_id] = "MATCH"
        ground_truth_pairs[rec_a_id] = [rec_b_id]
        counter += 1

    # 2. 20 Standard Exact Matches
    for i in range(20):
        amt = round(random.uniform(8000.0, 95000.0), 2)
        d = base_date + timedelta(days=4 + (i % 20))
        lead_dir = Direction.DEBIT if (i % 2 == 0) else Direction.CREDIT
        bk_dir = _bank_dir(lead_dir)

        rec_a_id = f"TLY-EX-{counter:04d}"
        rec_b_id = f"BNK-EX-{counter:04d}"
        vendor = f"Vendor Enterprise {chr(65 + (i % 26))}"

        rec_a = StandardizedRecord(
            record_id=rec_a_id,
            source=RecordSource.TALLY,
            date=d,
            account_label=vendor,
            amount=amt,
            direction=lead_dir,
            description=f"Payment for supply order #{3000+i} {vendor}",
            account_code=f"ORD-{3000+i}",
        )
        rec_b = StandardizedRecord(
            record_id=rec_b_id,
            source=RecordSource.BANK,
            date=d,
            account_label=vendor,
            amount=amt,
            direction=bk_dir,
            description=f"RTGS transfer for order #{3000+i} {vendor}",
            account_code=f"ORD-{3000+i}",
        )
        source_a.append(rec_a)
        source_b.append(rec_b)
        ground_truth_labels[rec_a_id] = "MATCH"
        ground_truth_pairs[rec_a_id] = [rec_b_id]
        counter += 1

    # 3. 10 Fuzzy Matches with near-miss bank decoys
    for i in range(10):
        base_amt = round(random.uniform(20000.0, 75000.0), 2)
        diff_amt = round(random.uniform(0.20, 1.10), 2)
        bk_amt = round(base_amt + diff_amt, 2)
        d_a = base_date + timedelta(days=8 + i)
        d_b = d_a + timedelta(days=1)
        lead_dir = Direction.DEBIT
        bk_dir = _bank_dir(lead_dir)

        rec_a_id = f"TLY-FZ-{counter:04d}"
        rec_b_id = f"BNK-FZ-{counter:04d}"
        vendor = f"Distributor {chr(75 + i)}"

        rec_a = StandardizedRecord(
            record_id=rec_a_id,
            source=RecordSource.TALLY,
            date=d_a,
            account_label=vendor,
            amount=base_amt,
            direction=lead_dir,
            description=f"Remittance to {vendor} invoice {4000+i}",
            account_code=f"INV-{4000+i}",
        )
        rec_b = StandardizedRecord(
            record_id=rec_b_id,
            source=RecordSource.BANK,
            date=d_b,
            account_label=vendor,
            amount=bk_amt,
            direction=bk_dir,
            description=f"CMS vendor payout {vendor[:10]} charges adjusted",
            account_code=f"INV-{4000+i}",
        )
        source_a.append(rec_a)
        source_b.append(rec_b)
        ground_truth_labels[rec_a_id] = "MATCH"
        ground_truth_pairs[rec_a_id] = [rec_b_id]

        # Add Decoy in Bank (near-miss amount on same day for conflicting party)
        if i < 5:
            decoy_id = f"BNK-DCY-{counter:04d}"
            rec_decoy = StandardizedRecord(
                record_id=decoy_id,
                source=RecordSource.BANK,
                date=d_a,
                account_label="Decoy Unrelated Entity",
                amount=round(base_amt + 0.50, 2),
                direction=bk_dir,
                description=f"Unrelated remittance Decoy Entity ref #{8880+i}",
                account_code=f"DCY-{counter}",
            )
            source_b.append(rec_decoy)

        counter += 1

    # 4. 5 Split Matches (1 Ledger to 2 Bank)
    for i in range(5):
        tot_amt = round(random.uniform(40000.0, 100000.0), 2)
        p1 = round(tot_amt * 0.55, 2)
        p2 = round(tot_amt - p1, 2)
        d = base_date + timedelta(days=12 + i)
        lead_dir = Direction.CREDIT
        bk_dir = _bank_dir(lead_dir)

        rec_a_id = f"TLY-SP-{counter:04d}"
        b1_id = f"BNK-SP1-{counter:04d}"
        b2_id = f"BNK-SP2-{counter:04d}"

        rec_a = StandardizedRecord(
            record_id=rec_a_id,
            source=RecordSource.TALLY,
            date=d,
            account_label=f"Wholesale Client {i+1}",
            amount=tot_amt,
            direction=lead_dir,
            description=f"Consolidated payment Wholesale Client {i+1}",
            account_code=f"SPL-{5000+i}",
        )
        rec_b1 = StandardizedRecord(
            record_id=b1_id,
            source=RecordSource.BANK,
            date=d,
            account_label=f"Wholesale Client {i+1}",
            amount=p1,
            direction=bk_dir,
            description=f"Client installment 1 Wholesale {i+1}",
            account_code=f"SPL-{5000+i}",
        )
        rec_b2 = StandardizedRecord(
            record_id=b2_id,
            source=RecordSource.BANK,
            date=d + timedelta(days=1),
            account_label=f"Wholesale Client {i+1}",
            amount=p2,
            direction=bk_dir,
            description=f"Client installment 2 Wholesale {i+1}",
            account_code=f"SPL-{5000+i}",
        )
        source_a.append(rec_a)
        source_b.extend([rec_b1, rec_b2])
        ground_truth_labels[rec_a_id] = "MATCH"
        ground_truth_pairs[rec_a_id] = [b1_id, b2_id]
        counter += 1

    # 5. 5 Severe Amount Discrepancies (>8% error on same date/narration) -> EXCEPTION
    for i in range(5):
        amt_a = 50000.00
        amt_b = 54500.00  # 9% error
        d = base_date + timedelta(days=18 + i)
        lead_dir = Direction.DEBIT
        bk_dir = _bank_dir(lead_dir)

        rec_a_id = f"TLY-ERR-AMT-{counter:04d}"
        rec_b_id = f"BNK-ERR-AMT-{counter:04d}"

        rec_a = StandardizedRecord(
            record_id=rec_a_id,
            source=RecordSource.TALLY,
            date=d,
            account_label="Mismatched Vendor",
            amount=amt_a,
            direction=lead_dir,
            description=f"Discrepancy test vendor payment #{6000+i}",
            account_code=f"MIS-{counter}",
        )
        rec_b = StandardizedRecord(
            record_id=rec_b_id,
            source=RecordSource.BANK,
            date=d,
            account_label="Mismatched Vendor",
            amount=amt_b,
            direction=bk_dir,
            description=f"Discrepancy test vendor payment #{6000+i}",
            account_code=f"MIS-{counter}",
        )
        source_a.append(rec_a)
        source_b.append(rec_b)
        ground_truth_labels[rec_a_id] = "EXCEPTION"
        ground_truth_pairs[rec_a_id] = []
        counter += 1

    # 6. 5 Severe Timing Delays (>14 days lag on identical amount) -> EXCEPTION
    for i in range(5):
        amt = round(random.uniform(22000.0, 48000.0), 2)
        d_a = base_date + timedelta(days=1)
        d_b = d_a + timedelta(days=16)  # 16 days lag
        lead_dir = Direction.DEBIT
        bk_dir = _bank_dir(lead_dir)

        rec_a_id = f"TLY-ERR-LAG-{counter:04d}"
        rec_b_id = f"BNK-ERR-LAG-{counter:04d}"

        rec_a = StandardizedRecord(
            record_id=rec_a_id,
            source=RecordSource.TALLY,
            date=d_a,
            account_label="Delayed Clearance Corp",
            amount=amt,
            direction=lead_dir,
            description=f"Cheque issue Delayed Clearance #{7000+i}",
            account_code=f"LAG-{counter}",
        )
        rec_b = StandardizedRecord(
            record_id=rec_b_id,
            source=RecordSource.BANK,
            date=d_b,
            account_label="Delayed Clearance Corp",
            amount=amt,
            direction=bk_dir,
            description=f"Cheque clearing Delayed Clearance #{7000+i}",
            account_code=f"LAG-{counter}",
        )
        source_a.append(rec_a)
        source_b.append(rec_b)
        ground_truth_labels[rec_a_id] = "EXCEPTION"
        ground_truth_pairs[rec_a_id] = []
        counter += 1

    # 7. 5 Unrecorded Ledger Charges in Tally (Phantom entries) -> EXCEPTION
    for i in range(5):
        amt = round(random.uniform(18000.0, 62000.0), 2)
        d = base_date + timedelta(days=24 + i)

        rec_a_id = f"TLY-ORP-{counter:04d}"
        rec_a = StandardizedRecord(
            record_id=rec_a_id,
            source=RecordSource.TALLY,
            date=d,
            account_label="Unrecorded Ledger Entity",
            amount=amt,
            direction=Direction.DEBIT,
            description=f"Phantom ledger disbursement with no bank counterpart #{8000+i}",
            account_code=f"ORP-{counter}",
        )
        source_a.append(rec_a)
        ground_truth_labels[rec_a_id] = "EXCEPTION"
        ground_truth_pairs[rec_a_id] = []
        counter += 1

    # 8. 5 Bank-Only Orphan Records (Bank interest, bank fees, AMC charges)
    bank_orphans = [
        (1240.50, Direction.CREDIT, "Quarterly Auto Interest Credit SBI Bank"),
        (590.00, Direction.DEBIT, "Annual AMC Account Maintenance Charge"),
        (23.60, Direction.DEBIT, "Quarterly SMS Alert Services Charge"),
        (15000.00, Direction.CREDIT, "Direct customer remittance without reference note"),
        (2100.00, Direction.DEBIT, "GST on consolidated bank service fees"),
    ]
    for idx, (b_amt, b_dir, b_desc) in enumerate(bank_orphans):
        b_id = f"BNK-ORP-{counter:04d}"
        rec_b = StandardizedRecord(
            record_id=b_id,
            source=RecordSource.BANK,
            date=base_date + timedelta(days=26 + idx),
            account_label="State Bank Operations",
            amount=b_amt,
            direction=b_dir,
            description=b_desc,
            account_code=f"BNK-ORP-{idx+1}",
        )
        source_b.append(rec_b)
        counter += 1

    # Shuffle to guarantee non-sequential matching
    random.shuffle(source_a)
    random.shuffle(source_b)

    if return_pairs:
        return source_a, source_b, ground_truth_labels, ground_truth_pairs
    return source_a, source_b, ground_truth_labels


def evaluate_reconciliation_benchmark(
    engine: ReconciliationEngine,
    batch_type: str = "standard",
) -> Dict[str, Any]:
    """
    Executes benchmark over the synthetic or adversarial ground-truth dataset.
    Produces objective classification metrics, pair accuracy, and dynamic confusion matrices.
    """
    if batch_type == "adversarial":
        source_a, source_b, ground_truth_labels, ground_truth_pairs = generate_adversarial_benchmark_batch(
            invert_direction=engine.cfg.invert_comparator_direction,
            return_pairs=True,
        )
    else:
        source_a, source_b, ground_truth_labels, ground_truth_pairs = generate_synthetic_benchmark_batch(
            invert_direction=engine.cfg.invert_comparator_direction,
            return_pairs=True,
        )

    result = engine.reconcile(source_a, source_b)

    # Map matched record pairings
    actual_matches_count = sum(1 for v in ground_truth_labels.values() if v == "MATCH")
    actual_exceptions_count = sum(1 for v in ground_truth_labels.values() if v == "EXCEPTION")

    tp, fp, fn, tn = 0, 0, 0, 0
    correctly_paired_count = 0

    # Build match lookup: record_a_id -> list of record_b_ids
    pred_pairs: Dict[str, List[str]] = {}
    for m in result.matches:
        if m.record_a and m.status in [MatchStatus.MATCHED, MatchStatus.PARTIAL_MATCH]:
            pred_pairs[m.record_a.record_id] = [b.record_id for b in m.records_b]

    for rec_a in source_a:
        actual_is_match = (ground_truth_labels.get(rec_a.record_id) == "MATCH")
        pred_is_match = rec_a.record_id in pred_pairs

        if actual_is_match and pred_is_match:
            tp += 1
            # Check pair accuracy: did it pair with the expected bank record(s)?
            expected_b_ids = set(ground_truth_pairs.get(rec_a.record_id, []))
            actual_b_ids = set(pred_pairs.get(rec_a.record_id, []))
            if expected_b_ids and actual_b_ids == expected_b_ids:
                correctly_paired_count += 1
        elif not actual_is_match and pred_is_match:
            fp += 1
        elif actual_is_match and not pred_is_match:
            fn += 1
        else:
            tn += 1

    precision = round(tp / max(tp + fp, 1), 4)
    recall = round(tp / max(tp + fn, 1), 4)
    accuracy = round((tp + tn) / max(tp + tn + fp + fn, 1), 4)
    f1 = round((2 * precision * recall) / max(precision + recall, 1e-6), 4)
    pair_accuracy = round(correctly_paired_count / max(actual_matches_count, 1), 4)

    confusion_matrix = pd.DataFrame([
        {
            "Ground Truth": f"Actual Match ({actual_matches_count})",
            "Pred Match": tp,
            "Pred Exception": fn,
        },
        {
            "Ground Truth": f"Actual Exception ({actual_exceptions_count})",
            "Pred Match": fp,
            "Pred Exception": tn,
        },
    ])

    return {
        "result": result,
        "batch_type": batch_type,
        "metrics": {
            "total_records": len(source_a),
            "actual_matches": actual_matches_count,
            "actual_exceptions": actual_exceptions_count,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "true_negatives": tn,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "accuracy": accuracy,
            "pair_accuracy": pair_accuracy,
            "correctly_paired_records": correctly_paired_count,
        },
        "confusion_matrix": confusion_matrix,
    }
