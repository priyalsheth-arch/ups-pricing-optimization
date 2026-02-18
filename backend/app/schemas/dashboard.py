from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from app.schemas.pricing import PricingGapSchema
from app.schemas.analysis import UpsellOpportunitySchema


class DashboardSummary(BaseModel):
    store_id: int
    period_days: int
    period_start: date
    period_end: date
    total_revenue: Decimal
    revenue_vs_prior_period: Decimal | None
    transactions_analyzed: int
    top_gaps: list[PricingGapSchema]
    top_upsells: list[UpsellOpportunitySchema]
    total_opportunity_est: Decimal
    last_upload_date: date | None
    underpriced_services: int
    high_priority_upsells: int
