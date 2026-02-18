from pydantic import BaseModel
from datetime import datetime, date
from typing import Any


class UploadBatchSchema(BaseModel):
    id: int
    store_id: int
    filename: str
    row_count: int | None
    status: str
    error_message: str | None
    date_range_start: date | None
    date_range_end: date | None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class UploadPreviewRow(BaseModel):
    row_number: int
    transaction_date: str | None
    service_category: str | None
    service_code: str | None
    service_description: str | None
    quantity: float | None
    net_revenue: float | None
    carrier: str | None
    service_level: str | None
    raw_data: dict[str, Any]


class ValidationReport(BaseModel):
    total_rows: int
    valid_rows: int
    error_rows: int
    warnings: list[str]
    errors: list[str]
    date_range_start: date | None
    date_range_end: date | None


class UploadConfirmResponse(BaseModel):
    batch_id: int
    rows_inserted: int
    status: str
    analysis_triggered: bool
