"""Three-bucket revenue opportunity calculator."""

from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.transaction import Transaction
from app.models.pricing import PricingGap
from app.models.analysis import UpsellOpportunity
from app.schemas.analysis import RevenueOpportunityReport, CategoryOpportunity, OpportunityAssumptions

SERVICE_CATEGORIES = ["shipping", "printing", "mailbox", "packing", "supplies"]


async def compute_revenue_opportunity(
    store_id: int,
    db: AsyncSession,
    period_days: int = 30,
    assumptions: OpportunityAssumptions | None = None,
) -> RevenueOpportunityReport:
    if assumptions is None:
        assumptions = OpportunityAssumptions()

    period_end = date.today()
    period_start = period_end - timedelta(days=period_days)
    prior_start = period_start - timedelta(days=period_days)

    # Current period revenue
    cur_result = await db.execute(
        select(func.sum(Transaction.net_revenue))
        .where(
            and_(
                Transaction.store_id == store_id,
                Transaction.transaction_date >= period_start,
                Transaction.transaction_date <= period_end,
                Transaction.net_revenue > 0,
            )
        )
    )
    current_revenue = Decimal(str(cur_result.scalar() or 0))

    # Prior period revenue
    prior_result = await db.execute(
        select(func.sum(Transaction.net_revenue))
        .where(
            and_(
                Transaction.store_id == store_id,
                Transaction.transaction_date >= prior_start,
                Transaction.transaction_date < period_start,
                Transaction.net_revenue > 0,
            )
        )
    )
    prior_revenue = Decimal(str(prior_result.scalar() or 0))

    # --- Bucket A: Pricing Gap Capture ---
    gap_result = await db.execute(
        select(
            PricingGap.service_category,
            func.sum(PricingGap.gap_amount * PricingGap.transaction_volume).label("raw_impact"),
            func.sum(PricingGap.transaction_volume).label("total_vol"),
            func.avg(PricingGap.our_price).label("avg_our_price"),
        )
        .where(
            and_(
                PricingGap.store_id == store_id,
                PricingGap.direction == "underpriced",
            )
        )
        .group_by(PricingGap.service_category)
    )
    gap_rows = gap_result.fetchall()

    bucket_a_by_category: dict[str, Decimal] = {}
    for r in gap_rows:
        # Cap raise at max_price_increase_pct above current
        raw = Decimal(str(r.raw_impact or 0))
        avg_our = Decimal(str(r.avg_our_price or 1))
        max_increase = avg_our * Decimal(str(assumptions.max_price_increase_pct))
        vol = Decimal(str(r.total_vol or 0))
        capped_impact = min(raw, max_increase * vol)
        # Apply elasticity (volume loss)
        conservative = capped_impact * (Decimal("1") - Decimal(str(assumptions.price_elasticity_factor)))
        bucket_a_by_category[r.service_category] = conservative

    total_bucket_a = sum(bucket_a_by_category.values(), Decimal("0"))

    # --- Bucket B: Upsell Conversions ---
    upsell_result = await db.execute(
        select(
            UpsellOpportunity.trigger_category,
            func.sum(UpsellOpportunity.monthly_impact_est).label("upsell_total"),
        )
        .where(
            and_(
                UpsellOpportunity.store_id == store_id,
                UpsellOpportunity.is_dismissed == False,
            )
        )
        .group_by(UpsellOpportunity.trigger_category)
    )
    upsell_rows = upsell_result.fetchall()
    bucket_b_by_category: dict[str, Decimal] = {r.trigger_category: Decimal(str(r.upsell_total or 0)) for r in upsell_rows}
    total_bucket_b = sum(bucket_b_by_category.values(), Decimal("0"))

    # --- Bucket C: Add-on Attach Rate Improvement ---
    # Count sessions missing add-ons per category
    bucket_c_by_category: dict[str, Decimal] = {}

    # Packing without supplies
    packing_result = await db.execute(
        select(func.count(Transaction.id))
        .where(
            and_(
                Transaction.store_id == store_id,
                Transaction.transaction_date >= period_start,
                Transaction.service_category == "packing",
            )
        )
    )
    packing_sessions = packing_result.scalar() or 0
    packing_addon_opportunity = (
        Decimal(str(packing_sessions)) * Decimal("8.50") * Decimal(str(assumptions.packing_supplies_attach))
    )
    bucket_c_by_category["packing"] = packing_addon_opportunity

    # Printing without finishing
    printing_result = await db.execute(
        select(func.count(Transaction.id))
        .where(
            and_(
                Transaction.store_id == store_id,
                Transaction.transaction_date >= period_start,
                Transaction.service_category == "printing",
            )
        )
    )
    printing_sessions = printing_result.scalar() or 0
    printing_addon_opportunity = (
        Decimal(str(printing_sessions)) * Decimal("6.00") * Decimal(str(assumptions.printing_finishing_attach))
    )
    bucket_c_by_category["printing"] = printing_addon_opportunity

    total_bucket_c = sum(bucket_c_by_category.values(), Decimal("0"))

    total_monthly = total_bucket_a + total_bucket_b + total_bucket_c
    annual = total_monthly * Decimal("12")

    # Combine by category
    by_category = []
    all_cats = set(list(bucket_a_by_category.keys()) + list(bucket_b_by_category.keys()) + list(bucket_c_by_category.keys()))
    for cat in sorted(all_cats):
        a = bucket_a_by_category.get(cat, Decimal("0"))
        b = bucket_b_by_category.get(cat, Decimal("0"))
        c = bucket_c_by_category.get(cat, Decimal("0"))
        by_category.append(CategoryOpportunity(
            category=cat,
            pricing_gap_opportunity=a,
            upsell_opportunity=b,
            addon_opportunity=c,
            total=a + b + c,
        ))

    return RevenueOpportunityReport(
        store_id=store_id,
        period_start=period_start,
        period_end=period_end,
        current_period_revenue=current_revenue,
        prior_period_revenue=prior_revenue,
        pricing_gap_opportunity=total_bucket_a,
        upsell_opportunity=total_bucket_b,
        addon_opportunity=total_bucket_c,
        total_monthly_opportunity=total_monthly,
        annual_opportunity=annual,
        by_category=by_category,
        assumptions=assumptions,
    )
