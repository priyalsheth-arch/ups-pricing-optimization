from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal


class UpsellOpportunitySchema(BaseModel):
    id: int
    store_id: int
    rule_id: str
    opportunity_type: str
    trigger_service: str
    trigger_category: str
    recommended_service: str
    recommended_service_code: str
    price_delta: Decimal | None
    conversion_rate_est: Decimal | None
    monthly_volume: int | None
    monthly_impact_est: Decimal | None
    priority: str | None
    staff_script: str | None
    is_dismissed: bool
    analysis_date: date

    model_config = {"from_attributes": True}


class CategoryOpportunity(BaseModel):
    category: str
    pricing_gap_opportunity: Decimal
    upsell_opportunity: Decimal
    addon_opportunity: Decimal
    total: Decimal


class OpportunityAssumptions(BaseModel):
    price_elasticity_factor: float = 0.10
    ground_to_2day_conversion: float = 0.12
    ground_to_3day_conversion: float = 0.18
    insurance_attach_rate: float = 0.25
    packing_supplies_attach: float = 0.35
    printing_finishing_attach: float = 0.22
    max_price_increase_pct: float = 0.15
    analysis_period_months: int = 1


class RevenueOpportunityReport(BaseModel):
    store_id: int
    period_start: date
    period_end: date
    current_period_revenue: Decimal
    prior_period_revenue: Decimal
    pricing_gap_opportunity: Decimal
    upsell_opportunity: Decimal
    addon_opportunity: Decimal
    total_monthly_opportunity: Decimal
    annual_opportunity: Decimal
    by_category: list[CategoryOpportunity]
    assumptions: OpportunityAssumptions


class MultiStoreComparison(BaseModel):
    store_id: int
    store_name: str
    store_number: str
    current_revenue: Decimal
    total_opportunity: Decimal
    top_gap_service: str | None
    top_gap_amount: Decimal | None
    top_upsell_service: str | None
    top_upsell_impact: Decimal | None
    underpriced_service_count: int
