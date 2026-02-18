from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal


class OurPriceCreate(BaseModel):
    store_id: int
    service_code: str
    service_category: str
    service_name: str
    unit: str | None = None
    price: Decimal
    effective_date: date
    notes: str | None = None


class OurPriceSchema(BaseModel):
    id: int
    store_id: int
    service_code: str
    service_category: str
    service_name: str
    unit: str | None
    price: Decimal
    effective_date: date
    notes: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompetitorPriceCreate(BaseModel):
    competitor_name: str
    service_code: str
    service_category: str
    service_name: str
    unit: str | None = None
    price: Decimal
    effective_date: date
    source_notes: str | None = None


class CompetitorPriceSchema(BaseModel):
    id: int
    competitor_name: str
    service_code: str
    service_category: str
    service_name: str
    unit: str | None
    price: Decimal
    effective_date: date
    source_notes: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class PricingGapSchema(BaseModel):
    id: int
    store_id: int
    service_code: str
    service_category: str
    service_name: str | None
    our_price: Decimal | None
    competitor_name: str
    competitor_price: Decimal | None
    gap_amount: Decimal | None
    gap_pct: Decimal | None
    direction: str | None
    transaction_volume: int | None
    revenue_impact: Decimal | None
    analysis_date: date
    period_start: date | None
    period_end: date | None

    model_config = {"from_attributes": True}
