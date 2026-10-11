"""
bank_statement_loader.py
========================
Standardized schema and ingestion adapters for bank statements and Tally exports.
Coerces multi-source transaction inputs into a canonical StandardizedRecord model.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Set, Tuple
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class RecordSource(str, Enum):
    TALLY = "TALLY"
    BANK = "BANK"
    NSE = "NSE"
    CLIENT = "CLIENT"


class Direction(str, Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


@dataclass
class StandardizedRecord:
    """
    Standardized financial transaction model.
    Guarantees structural uniformity across Tally, bank statement, and external records.
    """
    record_id: str
    source: RecordSource
    date: date
    account_label: str
    amount: float
    direction: Direction
    description: str
    account_code: Optional[str] = None
    raw_ref: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "source": str(self.source.value),
            "date": self.date.isoformat(),
            "account_label": self.account_label,
            "account_code": self.account_code,
            "amount": round(self.amount, 2),
            "direction": str(self.direction.value),
            "description": self.description,
            "raw_ref": self.raw_ref,
        }


class BankStatementLoader:
    """
    Parses bank statements (CSV/Excel) and Tally Journal exports into StandardizedRecord lists.
    """

    @staticmethod
    def _parse_date(val: Any) -> date:
        if isinstance(val, (date, datetime)):
            return val.date() if isinstance(val, datetime) else val
        s = str(val).strip()
        for fmt in (
            "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
            "%d-%b-%y", "%d-%b-%Y", "%d %b %Y", "%b %d, %Y"
        ):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        # Fallback to pandas flexible parse
        try:
            return pd.to_datetime(s).date()
        except Exception:
            return date.today()

    @staticmethod
    def _find_col(cols: Any, exact_matches: Set[str], contains_keywords: Tuple[str, ...] = ()) -> Optional[str]:
        """Finds matching column giving strict priority to exact matches before substring checks."""
        for c in cols:
            if c in exact_matches:
                return c
        for c in cols:
            if any(k in c for k in contains_keywords):
                return c
        return None

    @staticmethod
    def _clean_numeric(val: Any) -> float:
        """Safely parses float numeric, replacing NaNs and non-numerics with 0.0."""
        if val is None or pd.isna(val):
            return 0.0
        try:
            num = float(pd.to_numeric(val, errors="coerce"))
            return 0.0 if pd.isna(num) else num
        except Exception:
            return 0.0

    @classmethod
    def load_bank_statement(
        cls,
        file_path_or_buffer: Union[str, Path, Any],
        source_name: RecordSource = RecordSource.BANK,
    ) -> List[StandardizedRecord]:
        """
        Parses a bank statement CSV/Excel into a list of StandardizedRecord objects.
        Auto-detects typical column names across Indian and international banking formats.
        """
        if isinstance(file_path_or_buffer, (str, Path)):
            path = Path(file_path_or_buffer)
            if path.suffix.lower() in [".xlsx", ".xls"]:
                df = pd.read_excel(path)
            else:
                try:
                    df = pd.read_csv(path, encoding="utf-8")
                except UnicodeDecodeError:
                    df = pd.read_csv(path, encoding="latin1")
        elif hasattr(file_path_or_buffer, "name") and file_path_or_buffer.name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_path_or_buffer)
        else:
            try:
                df = pd.read_csv(file_path_or_buffer, encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(file_path_or_buffer, encoding="latin1")

        # Normalize column names
        df.columns = [str(c).strip().upper() for c in df.columns]

        # Detect columns with exact match priority (prevents 'CR' matching in 'DESCRIPTION')
        date_col = cls._find_col(
            df.columns,
            {"DATE", "TXN DATE", "TXN_DATE", "VALUE DATE", "VALUE_DATE", "POSTING DATE"},
            ("DATE",),
        )
        desc_col = cls._find_col(
            df.columns,
            {"DESCRIPTION", "NARRATION", "PARTICULARS", "REMARKS", "TXN DETAILS", "TRANSACTION DETAILS"},
            ("NARRATION", "DESCRIPTION", "PARTICULARS", "REMARKS"),
        )
        ref_col = cls._find_col(
            df.columns,
            {"REF", "REFERENCE", "REF NO", "REF_NO", "CHQ", "CHEQUE", "UTR", "TRANSACTION ID", "TXN NO", "TXN_NO"},
            ("CHQ", "REF", "UTR", "TRANSACTION ID", "TXN NO"),
        )
        debit_col = cls._find_col(
            df.columns,
            {"DEBIT", "DR", "WITHDRAWAL", "WITHDRAWAL AMT.", "WITHDRAWAL AMOUNT", "DR AMOUNT", "DEBIT AMOUNT"},
            ("WITHDRAWAL", "DEBIT"),
        )
        credit_col = cls._find_col(
            df.columns,
            {"CREDIT", "CR", "DEPOSIT", "DEPOSIT AMT.", "DEPOSIT AMOUNT", "CR AMOUNT", "CREDIT AMOUNT"},
            ("DEPOSIT", "CREDIT"),
        )
        amt_col = cls._find_col(
            df.columns,
            {"AMOUNT", "TXN AMOUNT", "TRANSACTION AMOUNT", "NET AMOUNT"},
            ("AMOUNT",),
        )

        records: List[StandardizedRecord] = []
        for idx, row in df.iterrows():
            d = cls._parse_date(row[date_col]) if date_col else date.today()
            desc = str(row[desc_col]).strip() if desc_col and pd.notna(row[desc_col]) else ""
            ref = str(row[ref_col]).strip() if ref_col and pd.notna(row[ref_col]) else f"BNK-{idx+1:05d}"

            dr_val = cls._clean_numeric(row.get(debit_col)) if debit_col else 0.0
            cr_val = cls._clean_numeric(row.get(credit_col)) if credit_col else 0.0

            if dr_val > 0.0 or dr_val < 0.0:
                amt = abs(dr_val)
                direction = Direction.DEBIT
            elif cr_val > 0.0 or cr_val < 0.0:
                amt = abs(cr_val)
                direction = Direction.CREDIT
            elif amt_col and pd.notna(row[amt_col]):
                raw_amt = cls._clean_numeric(row[amt_col])
                if raw_amt < 0.0:
                    direction = Direction.DEBIT
                    amt = abs(raw_amt)
                elif raw_amt > 0.0:
                    direction = Direction.CREDIT
                    amt = raw_amt
                else:
                    continue
            else:
                continue

            if amt == 0:
                continue

            rec = StandardizedRecord(
                record_id=ref,
                source=source_name,
                date=d,
                account_label=desc[:50] if desc else "Bank Transaction",
                amount=round(amt, 2),
                direction=direction,
                description=desc,
                account_code=ref,
                raw_ref=row.dropna().to_dict(),
            )
            records.append(rec)

        logger.info(f"Loaded {len(records)} standardized records from bank statement.")
        return records

    @classmethod
    def load_tally_jv(
        cls,
        jv_path: Union[str, Path, Any],
        source_name: RecordSource = RecordSource.TALLY,
    ) -> List[StandardizedRecord]:
        """
        Parses a Tally Journal Voucher (JV) CSV into a list of StandardizedRecord objects.
        """
        if isinstance(jv_path, (str, Path)):
            path = Path(jv_path)
            try:
                df = pd.read_csv(path, encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(path, encoding="latin1")
        else:
            df = pd.read_csv(jv_path, encoding="latin1")

        records: List[StandardizedRecord] = []
        for idx, row in df.iterrows():
            particulars = str(row.get("PARTICULARS", "")).strip()
            date_val = cls._parse_date(row.get("DATE", date.today()))
            vch_no = str(row.get("VCHNO", f"TLY-JV-{idx+1:05d}")).strip()
            narration = str(row.get("NARRATION", "")).strip()

            debit = cls._clean_numeric(row.get("DEBIT"))
            credit = cls._clean_numeric(row.get("CREDIT"))

            if debit > 0.0 or debit < 0.0:
                amt = abs(debit)
                direction = Direction.DEBIT
            elif credit > 0.0 or credit < 0.0:
                amt = abs(credit)
                direction = Direction.CREDIT
            else:
                continue

            rec = StandardizedRecord(
                record_id=vch_no if vch_no else f"JV-{idx+1:05d}",
                source=source_name,
                date=date_val,
                account_label=particulars,
                amount=round(amt, 2),
                direction=direction,
                description=narration if narration else particulars,
                account_code=str(row.get("REFNO", vch_no)).strip(),
                raw_ref=row.dropna().to_dict(),
            )
            records.append(rec)

        logger.info(f"Loaded {len(records)} standardized records from Tally JV.")
        return records
