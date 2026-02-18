"""ConnectSuite CSV column constants and normalization utilities."""

import re
from decimal import Decimal, InvalidOperation

# Raw CSV column names from ConnectSuite export
COL_TXN_ID = "Transaction ID"
COL_DATE = "Transaction Date"
COL_TIME = "Transaction Time"
COL_STORE_NUMBER = "Store Number"
COL_DEPARTMENT = "Department"
COL_ITEM_CODE = "Item Code"
COL_ITEM_DESC = "Item Description"
COL_QUANTITY = "Quantity"
COL_UNIT_PRICE = "Unit Price"
COL_EXTENDED_PRICE = "Extended Price"
COL_DISCOUNT = "Discount"
COL_NET_AMOUNT = "Net Amount"
COL_CARRIER = "Carrier"
COL_SERVICE_LEVEL = "Service Level"
COL_WEIGHT = "Weight"
COL_ZONE = "Zone"
COL_SHIP_STATE = "Ship To State"
COL_CUSTOMER = "Customer Account"

REQUIRED_COLUMNS = {COL_TXN_ID, COL_DATE, COL_DEPARTMENT, COL_NET_AMOUNT}

DEPARTMENT_TO_CATEGORY: dict[str, str] = {
    "SHIP": "shipping",
    "SHIPPING": "shipping",
    "PRINT": "printing",
    "PRINTING": "printing",
    "COPY": "printing",
    "COPIES": "printing",
    "MAILBOX": "mailbox",
    "MAIL": "mailbox",
    "PACK": "packing",
    "PACKING": "packing",
    "SUPPLIES": "supplies",
    "SUPPLY": "supplies",
    "NOTARY": "other",
    "SHRED": "other",
    "SHREDDING": "other",
    "OTHER": "other",
}

SERVICE_LEVEL_NORMALIZE: dict[str, str] = {
    "GROUND": "ground",
    "UPS GROUND": "ground",
    "2DAY": "2day",
    "2 DAY": "2day",
    "2ND DAY AIR": "2day",
    "SECOND DAY AIR": "2day",
    "NEXT DAY AIR": "overnight",
    "NDA": "overnight",
    "NEXT DAY": "overnight",
    "OVERNIGHT": "overnight",
    "3 DAY SELECT": "3day",
    "3DAY": "3day",
    "3 DAY": "3day",
    "PRIORITY MAIL": "priority_mail",
    "FIRST CLASS": "first_class",
    "FLAT RATE": "flat_rate",
}

CONTINENTAL_US_STATES = {
    "AL", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI",
    "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
    "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN",
    "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}

BASIC_MAILBOX_CODES = {"MAILBOX_S", "MAILBOX_M", "MAILBOX_BASIC", "MB_SMALL", "MB_MED"}


def parse_currency(val: str | None) -> Decimal | None:
    """Parse currency strings like '$1,234.56' or '(1.00)' to Decimal."""
    if val is None:
        return None
    val = str(val).strip()
    if not val or val in ("N/A", "-", ""):
        return None
    # Handle negative in parentheses: (1.00) → -1.00
    negative = val.startswith("(") and val.endswith(")")
    val = val.strip("()")
    val = re.sub(r"[$,\s]", "", val)
    try:
        result = Decimal(val)
        return -result if negative else result
    except InvalidOperation:
        return None


def parse_weight(val: str | None) -> Decimal | None:
    """Parse weight, coercing N/A, blank, 0 to None."""
    if val is None:
        return None
    val = str(val).strip()
    if val in ("N/A", "", "0", "0.0"):
        return None
    try:
        result = Decimal(val)
        return result if result > 0 else None
    except InvalidOperation:
        return None


def parse_zone(val: str | None) -> int | None:
    if val is None:
        return None
    val = str(val).strip()
    if val in ("N/A", "", "0"):
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def normalize_department(dept: str | None) -> str:
    if dept is None:
        return "other"
    return DEPARTMENT_TO_CATEGORY.get(str(dept).strip().upper(), "other")


def normalize_service_level(level: str | None) -> str | None:
    if level is None:
        return None
    return SERVICE_LEVEL_NORMALIZE.get(str(level).strip().upper())
