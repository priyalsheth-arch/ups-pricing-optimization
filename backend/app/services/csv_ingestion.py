"""CSV ingestion pipeline: validate → normalize → persist ConnectSuite exports."""

import io
import pandas as pd
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.transaction import Transaction
from app.models.upload import UploadBatch
from app.utils.csv_mappings import (
    COL_TXN_ID, COL_DATE, COL_TIME, COL_STORE_NUMBER,
    COL_DEPARTMENT, COL_ITEM_CODE, COL_ITEM_DESC,
    COL_QUANTITY, COL_UNIT_PRICE, COL_EXTENDED_PRICE,
    COL_DISCOUNT, COL_NET_AMOUNT, COL_CARRIER,
    COL_SERVICE_LEVEL, COL_WEIGHT, COL_ZONE,
    COL_SHIP_STATE, COL_CUSTOMER, REQUIRED_COLUMNS,
    parse_currency, parse_weight, parse_zone,
    normalize_department, normalize_service_level,
)


class IngestionError(Exception):
    pass


def _parse_date(val: str | None) -> date | None:
    if not val or str(val).strip() in ("", "N/A", "nan"):
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(str(val).strip(), fmt).date()
        except ValueError:
            continue
    return None


def validate_and_preview(
    file_bytes: bytes,
    store_id: int,
) -> tuple[pd.DataFrame, dict]:
    """
    Parse CSV bytes, validate structure and rows.
    Returns (cleaned_df, validation_report).
    Raises IngestionError for unrecoverable structural issues.
    """
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), dtype=str, keep_default_na=False)
    except Exception as e:
        raise IngestionError(f"Could not parse CSV file: {e}")

    df.columns = [c.strip() for c in df.columns]

    # Check required columns
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise IngestionError(f"CSV missing required columns: {', '.join(sorted(missing))}")

    errors = []
    warnings = []
    valid_indices = []

    dates_seen = []
    for idx, row in df.iterrows():
        row_num = int(idx) + 2  # 1-based, skip header row

        txn_id = str(row.get(COL_TXN_ID, "")).strip()
        if not txn_id or txn_id == "nan":
            errors.append(f"Row {row_num}: Missing Transaction ID")
            continue

        txn_date = _parse_date(row.get(COL_DATE))
        if txn_date is None:
            errors.append(f"Row {row_num}: Unparseable date '{row.get(COL_DATE)}'")
            continue

        net_revenue = parse_currency(row.get(COL_NET_AMOUNT))
        if net_revenue is None:
            errors.append(f"Row {row_num}: Missing or invalid Net Amount")
            continue

        if net_revenue < 0:
            warnings.append(f"Row {row_num}: Negative net amount (return/void) skipped")
            continue

        dept = str(row.get(COL_DEPARTMENT, "")).strip()
        category = normalize_department(dept)
        if category == "other" and dept.upper() not in ("NOTARY", "SHRED", "SHREDDING", "OTHER"):
            warnings.append(f"Row {row_num}: Unknown department '{dept}', mapped to 'other'")

        valid_indices.append(idx)
        dates_seen.append(txn_date)

    valid_df = df.loc[valid_indices].copy()

    report = {
        "total_rows": len(df),
        "valid_rows": len(valid_df),
        "error_rows": len(df) - len(valid_df),
        "warnings": warnings,
        "errors": errors,
        "date_range_start": min(dates_seen) if dates_seen else None,
        "date_range_end": max(dates_seen) if dates_seen else None,
    }

    return valid_df, report


def _build_transaction(row: pd.Series, store_id: int, batch_id: int) -> dict:
    return {
        "store_id": store_id,
        "upload_batch_id": batch_id,
        "connectsuite_txn_id": str(row.get(COL_TXN_ID, "")).strip() or None,
        "transaction_date": _parse_date(row.get(COL_DATE)),
        "transaction_time": str(row.get(COL_TIME, "")).strip() or None,
        "service_category": normalize_department(row.get(COL_DEPARTMENT)),
        "service_code": str(row.get(COL_ITEM_CODE, "")).strip().upper() or None,
        "service_description": str(row.get(COL_ITEM_DESC, "")).strip() or None,
        "quantity": parse_currency(row.get(COL_QUANTITY)),
        "unit_price": parse_currency(row.get(COL_UNIT_PRICE)),
        "extended_price": parse_currency(row.get(COL_EXTENDED_PRICE)),
        "discount_amount": parse_currency(row.get(COL_DISCOUNT)) or Decimal("0"),
        "net_revenue": parse_currency(row.get(COL_NET_AMOUNT)),
        "carrier": str(row.get(COL_CARRIER, "")).strip().upper() or None,
        "service_level": normalize_service_level(row.get(COL_SERVICE_LEVEL)),
        "weight_lbs": parse_weight(row.get(COL_WEIGHT)),
        "zone": parse_zone(row.get(COL_ZONE)),
        "destination_state": str(row.get(COL_SHIP_STATE, "")).strip().upper() or None,
        "customer_ref": str(row.get(COL_CUSTOMER, "")).strip() or None,
    }


async def persist_batch(
    valid_df: pd.DataFrame,
    store_id: int,
    batch_id: int,
    db: AsyncSession,
) -> int:
    """Insert validated rows into transactions table. Returns count inserted."""
    # Fetch existing txn IDs for this store to skip duplicates
    result = await db.execute(
        select(Transaction.connectsuite_txn_id).where(
            and_(
                Transaction.store_id == store_id,
                Transaction.connectsuite_txn_id.isnot(None),
            )
        )
    )
    existing_ids = {r[0] for r in result.fetchall()}

    rows_to_insert = []
    for _, row in valid_df.iterrows():
        txn_data = _build_transaction(row, store_id, batch_id)
        txn_id = txn_data.get("connectsuite_txn_id")
        if txn_id and txn_id in existing_ids:
            continue
        rows_to_insert.append(Transaction(**txn_data))
        if txn_id:
            existing_ids.add(txn_id)

    if rows_to_insert:
        db.add_all(rows_to_insert)
        await db.flush()

    return len(rows_to_insert)


def get_preview_rows(valid_df: pd.DataFrame, limit: int = 50) -> list[dict]:
    """Return first N rows as preview dicts for the frontend."""
    preview = []
    for i, (_, row) in enumerate(valid_df.head(limit).iterrows()):
        preview.append({
            "row_number": i + 1,
            "transaction_date": str(row.get(COL_DATE, "")),
            "service_category": normalize_department(row.get(COL_DEPARTMENT)),
            "service_code": str(row.get(COL_ITEM_CODE, "")).strip().upper() or None,
            "service_description": str(row.get(COL_ITEM_DESC, "")).strip() or None,
            "quantity": float(parse_currency(row.get(COL_QUANTITY)) or 0) or None,
            "net_revenue": float(parse_currency(row.get(COL_NET_AMOUNT)) or 0),
            "carrier": str(row.get(COL_CARRIER, "")).strip() or None,
            "service_level": normalize_service_level(row.get(COL_SERVICE_LEVEL)),
            "raw_data": {k: str(v) for k, v in row.items()},
        })
    return preview
