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
from typing import Any, Dict, List, Optional, Union
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

        # Detect columns
        date_col = next((c for c in df.columns if any(k in c for k in ["DATE", "TXN DATE", "VALUE DATE"])), None)
        desc_col = next((c for c in df.columns if any(k in c for k in ["NARRATION", "DESCRIPTION", "PARTICULARS", "REMARKS"])), None)
        ref_col = next((c for c in df.columns if any(k in c for k in ["CHQ", "REF", "UTR", "TRANSACTION ID", "TXN NO"])), None)
        debit_col = next((c for c in df.columns if any(k in c for k in ["WITHDRAWAL", "DEBIT", "DR"])), None)
        credit_col = next((c for c in df.columns if any(k in c for k in ["DEPOSIT", "CREDIT", "CR"])), None)
        amt_col = next((c for c in df.columns if any(k in c for k in ["AMOUNT", "TXN AMOUNT"])), None)

        records: List[StandardizedRecord] = []
        for idx, row in df.iterrows():
            d = cls._parse_date(row[date_col]) if date_col else date.today()
            desc = str(row[desc_col]).strip() if desc_col and pd.notna(row[desc_col]) else ""
            ref = str(row[ref_col]).strip() if ref_col and pd.notna(row[ref_col]) else f"BNK-{idx+1:05d}"

            dr_val = pd.to_numeric(row.get(debit_col, 0.0), errors="coerce") or 0.0
            cr_val = pd.to_numeric(row.get(credit_col, 0.0), errors="coerce") or 0.0

            if dr_val > 0 or dr_val < 0:
                amt = abs(float(dr_val))
                direction = Direction.DEBIT
            elif cr_val > 0 or cr_val < 0:
                amt = abs(float(cr_val))
                direction = Direction.CREDIT
            elif amt_col and pd.notna(row[amt_col]):
                raw_amt = float(pd.to_numeric(row[amt_col], errors="coerce") or 0.0)
                direction = Direction.DEBIT if raw_amt < 0 else Direction.CREDIT
                amt = abs(raw_amt)
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

            debit = float(pd.to_numeric(row.get("DEBIT", 0.0), errors="coerce") or 0.0)
            credit = float(pd.to_numeric(row.get("CREDIT", 0.0), errors="coerce") or 0.0)

            if debit != 0.0:
                amt = abs(debit)
                direction = Direction.DEBIT
            elif credit != 0.0:
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
