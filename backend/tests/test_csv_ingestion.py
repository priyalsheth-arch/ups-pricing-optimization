"""Tests for CSV ingestion: validation, parsing, normalization."""

import pytest
from decimal import Decimal

from app.services.csv_ingestion import validate_and_preview, _parse_date, _build_transaction
from app.utils.csv_mappings import (
    parse_currency, parse_weight, parse_zone,
    normalize_department, normalize_service_level,
)

# ---------------------------------------------------------------------------
# parse_currency
# ---------------------------------------------------------------------------

def test_parse_currency_plain():
    assert parse_currency("12.50") == Decimal("12.50")

def test_parse_currency_with_dollar_sign():
    assert parse_currency("$1,234.56") == Decimal("1234.56")

def test_parse_currency_negative_parens():
    assert parse_currency("(5.00)") == Decimal("-5.00")

def test_parse_currency_empty_returns_none():
    assert parse_currency("") is None
    assert parse_currency(None) is None
    assert parse_currency("N/A") is None

def test_parse_currency_dash_returns_none():
    assert parse_currency("-") is None


# ---------------------------------------------------------------------------
# parse_weight / parse_zone
# ---------------------------------------------------------------------------

def test_parse_weight_valid():
    assert parse_weight("3.5") == Decimal("3.5")

def test_parse_weight_zero_returns_none():
    assert parse_weight("0") is None
    assert parse_weight("0.0") is None

def test_parse_weight_blank_returns_none():
    assert parse_weight("") is None
    assert parse_weight("N/A") is None

def test_parse_zone_valid():
    assert parse_zone("4") == 4
    assert parse_zone("5.0") == 5

def test_parse_zone_zero_returns_none():
    assert parse_zone("0") is None

def test_parse_zone_blank_returns_none():
    assert parse_zone("") is None


# ---------------------------------------------------------------------------
# normalize_department / normalize_service_level
# ---------------------------------------------------------------------------

def test_normalize_department_shipping():
    assert normalize_department("SHIP") == "shipping"
    assert normalize_department("Shipping") == "shipping"

def test_normalize_department_printing():
    assert normalize_department("PRINT") == "printing"
    assert normalize_department("COPY") == "printing"

def test_normalize_department_unknown():
    assert normalize_department("XYZ") == "other"
    assert normalize_department(None) == "other"

def test_normalize_service_level_ground():
    assert normalize_service_level("Ground") == "ground"
    assert normalize_service_level("UPS GROUND") == "ground"

def test_normalize_service_level_2day():
    assert normalize_service_level("2nd Day Air") == "2day"
    assert normalize_service_level("2DAY") == "2day"

def test_normalize_service_level_overnight():
    assert normalize_service_level("Next Day Air") == "overnight"

def test_normalize_service_level_unknown_returns_none():
    assert normalize_service_level("Super Saver") is None
    assert normalize_service_level(None) is None


# ---------------------------------------------------------------------------
# _parse_date
# ---------------------------------------------------------------------------

def test_parse_date_mm_dd_yyyy():
    from datetime import date
    result = _parse_date("01/15/2026")
    assert result == date(2026, 1, 15)

def test_parse_date_iso_format():
    from datetime import date
    result = _parse_date("2026-01-15")
    assert result == date(2026, 1, 15)

def test_parse_date_invalid_returns_none():
    assert _parse_date("not-a-date") is None
    assert _parse_date("") is None
    assert _parse_date(None) is None


# ---------------------------------------------------------------------------
# validate_and_preview — full CSV parsing
# ---------------------------------------------------------------------------

VALID_CSV = """\
Transaction ID,Transaction Date,Transaction Time,Store Number,Department,Item Code,Item Description,Quantity,Unit Price,Extended Price,Discount,Net Amount,Carrier,Service Level,Weight,Zone,Ship To State,Customer Account
TXN-001,01/15/2026,09:00:00,4521,SHIP,UPS_GROUND,UPS Ground,1,12.50,12.50,0.00,12.50,UPS,Ground,3.5,4,GA,CUST-1
TXN-002,01/16/2026,10:00:00,4521,PRINT,BW_COPY,B&W Copies,25,0.15,3.75,0.00,3.75,,,,,,
TXN-003,01/17/2026,11:00:00,4521,PACK,PACK_SVC,Packing,1,15.00,15.00,0.00,15.00,,,,,,
"""

def test_validate_and_preview_valid_csv():
    df, report = validate_and_preview(VALID_CSV.encode(), store_id=1)
    assert report["total_rows"] == 3
    assert report["valid_rows"] == 3
    assert report["error_rows"] == 0
    assert len(report["errors"]) == 0

def test_validate_and_preview_date_range():
    from datetime import date
    df, report = validate_and_preview(VALID_CSV.encode(), store_id=1)
    assert report["date_range_start"] == date(2026, 1, 15)
    assert report["date_range_end"] == date(2026, 1, 17)

def test_validate_and_preview_missing_required_column():
    from app.services.csv_ingestion import IngestionError
    bad_csv = "Transaction Date,Department,Net Amount\n01/15/2026,SHIP,12.50\n"
    with pytest.raises(IngestionError, match="missing required columns"):
        validate_and_preview(bad_csv.encode(), store_id=1)

def test_validate_and_preview_bad_date_skipped():
    csv = (
        "Transaction ID,Transaction Date,Transaction Time,Store Number,Department,"
        "Item Code,Item Description,Quantity,Unit Price,Extended Price,Discount,Net Amount,"
        "Carrier,Service Level,Weight,Zone,Ship To State,Customer Account\n"
        "TXN-001,not-a-date,09:00:00,4521,SHIP,UPS_GROUND,UPS Ground,1,12.50,12.50,0.00,12.50,UPS,Ground,3.5,4,GA,\n"
    )
    df, report = validate_and_preview(csv.encode(), store_id=1)
    assert report["valid_rows"] == 0
    assert report["error_rows"] == 1
    assert any("Unparseable date" in e for e in report["errors"])

def test_validate_and_preview_negative_net_amount_skipped():
    csv = (
        "Transaction ID,Transaction Date,Transaction Time,Store Number,Department,"
        "Item Code,Item Description,Quantity,Unit Price,Extended Price,Discount,Net Amount,"
        "Carrier,Service Level,Weight,Zone,Ship To State,Customer Account\n"
        "TXN-001,01/15/2026,09:00:00,4521,SHIP,UPS_GROUND,UPS Ground,1,12.50,12.50,0.00,(12.50),UPS,Ground,3.5,4,GA,\n"
    )
    df, report = validate_and_preview(csv.encode(), store_id=1)
    assert report["valid_rows"] == 0
    assert any("Negative" in w for w in report["warnings"])

def test_validate_and_preview_missing_txn_id_skipped():
    csv = (
        "Transaction ID,Transaction Date,Transaction Time,Store Number,Department,"
        "Item Code,Item Description,Quantity,Unit Price,Extended Price,Discount,Net Amount,"
        "Carrier,Service Level,Weight,Zone,Ship To State,Customer Account\n"
        ",01/15/2026,09:00:00,4521,SHIP,UPS_GROUND,UPS Ground,1,12.50,12.50,0.00,12.50,UPS,Ground,3.5,4,GA,\n"
    )
    df, report = validate_and_preview(csv.encode(), store_id=1)
    assert report["valid_rows"] == 0
    assert any("Missing Transaction ID" in e for e in report["errors"])

def test_validate_and_preview_mixed_valid_invalid():
    csv = (
        "Transaction ID,Transaction Date,Transaction Time,Store Number,Department,"
        "Item Code,Item Description,Quantity,Unit Price,Extended Price,Discount,Net Amount,"
        "Carrier,Service Level,Weight,Zone,Ship To State,Customer Account\n"
        "TXN-001,01/15/2026,09:00:00,4521,SHIP,UPS_GROUND,UPS Ground,1,12.50,12.50,0.00,12.50,UPS,Ground,3.5,4,GA,\n"
        ",01/15/2026,09:00:00,4521,SHIP,UPS_GROUND,UPS Ground,1,12.50,12.50,0.00,12.50,UPS,Ground,3.5,4,GA,\n"
        "TXN-003,bad-date,09:00:00,4521,SHIP,UPS_GROUND,UPS Ground,1,12.50,12.50,0.00,12.50,UPS,Ground,3.5,4,GA,\n"
    )
    df, report = validate_and_preview(csv.encode(), store_id=1)
    assert report["total_rows"] == 3
    assert report["valid_rows"] == 1
    assert report["error_rows"] == 2

def test_validate_and_preview_not_a_csv():
    from app.services.csv_ingestion import IngestionError
    with pytest.raises(IngestionError):
        validate_and_preview(b"\x00\x01\x02binary garbage", store_id=1)
