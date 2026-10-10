"""
reconciliation_benchmark.py
===========================
Generates a verified 60-record synthetic reconciliation batch with ground-truth labels.
Evaluates engine precision, recall, and confusion matrix against known ground truth.
"""

from datetime import date, timedelta
import random
from typing import Dict, List, Tuple, Any

import pandas as pd

from modules.bank_statement_loader import StandardizedRecord, Direction, RecordSource
from modules.reconciliation_engine import ReconciliationEngine, MatchStatus

def generate_synthetic_benchmark_batch(
    base_date: date = date(2026, 4, 1),
    seed: int = 42,
) -> Tuple[List[StandardizedRecord], List[StandardizedRecord], Dict[str, str]]:
    """
    Constructs a 60-record synthetic ground truth test batch:
    - 40 Exact Matches (identical amount, date, direction)
    - 10 Fuzzy Matches (slight amount rounding ±₹0.50, date lag 1-2 days, narration abbreviation)
    - 5 Split Matches (1 ledger entry split across 2 bank entries)
    - 5 Deliberate Exceptions (missing records, severe data entry mismatch)

    Returns:
    (source_a, source_b, ground_truth_labels)
    """
    random.seed(seed)
    source_a: List[StandardizedRecord] = []
    source_b: List[StandardizedRecord] = []
    ground_truth: Dict[str, str] = {}

    vendors = [
        "Reliance Retail Ltd", "Tata Consumer Products", "Hindustan Unilever",
        "Nestle India Ltd", "ITC Infotech", "Adani Wilmar", "Dabur India",
        "Godrej Consumer", "Marico Ltd", "Britannia Industries", "Apex Wholesale",
        "National Logistics Corp", "Metro Distribution", "Blue Dart Express"
    ]

    record_counter = 1

    # 1. 40 Exact Matches
    for i in range(40):
        v = random.choice(vendors)
        amt = round(random.uniform(5000.0, 150000.0), 2)
        d = base_date + timedelta(days=(i % 25))
        direction = Direction.DEBIT if (i % 3 != 0) else Direction.CREDIT

        rec_a_id = f"TLY-EX-{record_counter:04d}"
        rec_b_id = f"BNK-EX-{record_counter:04d}"

        rec_a = StandardizedRecord(
            record_id=rec_a_id,
            source=RecordSource.TALLY,
            date=d,
            account_label=v,
            amount=amt,
            direction=direction,
            description=f"Payment for invoice #{1000+i} to {v}",
            account_code=f"INV-{1000+i}",
        )
        rec_b = StandardizedRecord(
            record_id=rec_b_id,
            source=RecordSource.BANK,
            date=d,
            account_label=v,
            amount=amt,
            direction=direction,
            description=f"NEFT/RTGS to {v} INV-{1000+i}",
            account_code=f"INV-{1000+i}",
        )

        source_a.append(rec_a)
        source_b.append(rec_b)
        ground_truth[rec_a_id] = "MATCH"
        record_counter += 1

    # 2. 10 Fuzzy Matches (Date lag 1-2 days, amount diff ₹0.20 - ₹1.50, modified narration)
    for i in range(10):
        v = random.choice(vendors)
        base_amt = round(random.uniform(10000.0, 80000.0), 2)
        diff_amt = round(random.uniform(0.10, 1.20), 2)
        bank_amt = round(base_amt + diff_amt, 2)
        date_a = base_date + timedelta(days=5 + (i * 2))
        date_b = date_a + timedelta(days=random.choice([1, 2]))
        direction = Direction.DEBIT

        rec_a_id = f"TLY-FZ-{record_counter:04d}"
        rec_b_id = f"BNK-FZ-{record_counter:04d}"

        rec_a = StandardizedRecord(
            record_id=rec_a_id,
            source=RecordSource.TALLY,
            date=date_a,
            account_label=v,
            amount=base_amt,
            direction=direction,
            description=f"Vendor disbursement to {v}",
            account_code=f"VEND-{2000+i}",
        )
        rec_b = StandardizedRecord(
            record_id=rec_b_id,
            source=RecordSource.BANK,
            date=date_b,
            account_label=v,
            amount=bank_amt,
            direction=direction,
            description=f"CMS transfer {v[:8]} bank charges inc",
            account_code=f"VEND-{2000+i}",
        )

        source_a.append(rec_a)
        source_b.append(rec_b)
        ground_truth[rec_a_id] = "MATCH"
        record_counter += 1

    # 3. 5 Split Matches (1 Ledger entry split into 2 bank deposits/payments)
    for i in range(5):
        v = random.choice(vendors)
        total_amt = round(random.uniform(30000.0, 90000.0), 2)
        part1 = round(total_amt * 0.6, 2)
        part2 = round(total_amt - part1, 2)
        d = base_date + timedelta(days=10 + i)
        direction = Direction.CREDIT

        rec_a_id = f"TLY-SP-{record_counter:04d}"
        b1_id = f"BNK-SP1-{record_counter:04d}"
        b2_id = f"BNK-SP2-{record_counter:04d}"

        rec_a = StandardizedRecord(
            record_id=rec_a_id,
            source=RecordSource.TALLY,
            date=d,
            account_label=v,
            amount=total_amt,
            direction=direction,
            description=f"Bulk settlement from {v} invoice series {500+i}",
            account_code=f"SETTLE-{500+i}",
        )
        rec_b1 = StandardizedRecord(
            record_id=b1_id,
            source=RecordSource.BANK,
            date=d,
            account_label=v,
            amount=part1,
            direction=direction,
            description=f"Part remittance 1 from {v}",
            account_code=f"SETTLE-{500+i}",
        )
        rec_b2 = StandardizedRecord(
            record_id=b2_id,
            source=RecordSource.BANK,
            date=d + timedelta(days=1),
            account_label=v,
            amount=part2,
            direction=direction,
            description=f"Part remittance 2 from {v}",
            account_code=f"SETTLE-{500+i}",
        )

        source_a.append(rec_a)
        source_b.extend([rec_b1, rec_b2])
        ground_truth[rec_a_id] = "MATCH"
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
        ground_truth[rec_a_id] = "EXCEPTION"
        record_counter += 1

    # Shuffle lists to prevent positional cheating
    random.shuffle(source_a)
    random.shuffle(source_b)

    return source_a, source_b, ground_truth


def evaluate_reconciliation_benchmark(
    engine: ReconciliationEngine,
) -> Dict[str, Any]:
    """
    Executes benchmark over the synthetic 60-record dataset and produces objective
    precision, recall, accuracy, and confusion matrix metrics.
    """
    source_a, source_b, ground_truth = generate_synthetic_benchmark_batch()
    result = engine.reconcile(source_a, source_b)

    # Map engine results
    tp, fp, fn, tn = 0, 0, 0, 0

    # Build match lookup for source A
    matched_a_ids = {m.record_a.record_id for m in result.matches if m.record_a and m.status in [MatchStatus.MATCHED, MatchStatus.PARTIAL_MATCH]}

    for rec_a in source_a:
        actual_is_match = (ground_truth.get(rec_a.record_id) == "MATCH")
        pred_is_match = (rec_a.record_id in matched_a_ids)

        if actual_is_match and pred_is_match:
            tp += 1
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

    confusion_matrix = pd.DataFrame([
        {"Ground Truth": "Actual Match (55)", "Pred Match": tp, "Pred Exception": fn},
        {"Ground Truth": "Actual Exception (5)", "Pred Match": fp, "Pred Exception": tn},
    ])

    return {
        "result": result,
        "metrics": {
            "total_records": len(source_a),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "true_negatives": tn,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "accuracy": accuracy,
        },
        "confusion_matrix": confusion_matrix,
    }
