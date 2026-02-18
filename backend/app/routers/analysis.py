from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.database import get_db
from app.models.pricing import PricingGap
from app.models.analysis import UpsellOpportunity
from app.models.store import Store
from app.models.transaction import Transaction
from app.schemas.pricing import PricingGapSchema
from app.schemas.analysis import UpsellOpportunitySchema, RevenueOpportunityReport, MultiStoreComparison, OpportunityAssumptions
from app.dependencies import get_current_user, require_manager
from app.services.pricing_engine import run_gap_analysis
from app.services.upsell_engine import run_upsell_analysis
from app.services.revenue_calculator import compute_revenue_opportunity
from decimal import Decimal

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/gaps", response_model=list[PricingGapSchema])
async def get_pricing_gaps(
    store_id: int | None = None,
    category: str | None = None,
    direction: str | None = None,
    period_days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = (
        select(PricingGap)
        .order_by(PricingGap.revenue_impact.desc())
    )
    if store_id:
        q = q.where(PricingGap.store_id == store_id)
    elif current_user.role == "staff" and current_user.store_id:
        q = q.where(PricingGap.store_id == current_user.store_id)
    if category:
        q = q.where(PricingGap.service_category == category)
    if direction:
        q = q.where(PricingGap.direction == direction)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/upsells", response_model=list[UpsellOpportunitySchema])
async def get_upsells(
    store_id: int | None = None,
    category: str | None = None,
    priority: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = (
        select(UpsellOpportunity)
        .where(UpsellOpportunity.is_dismissed == False)
        .order_by(UpsellOpportunity.monthly_impact_est.desc())
    )
    if store_id:
        q = q.where(UpsellOpportunity.store_id == store_id)
    elif current_user.role == "staff" and current_user.store_id:
        q = q.where(UpsellOpportunity.store_id == current_user.store_id)
    if category:
        q = q.where(UpsellOpportunity.trigger_category == category)
    if priority:
        q = q.where(UpsellOpportunity.priority == priority)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/upsells/{opportunity_id}/dismiss")
async def dismiss_upsell(
    opportunity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager),
):
    result = await db.execute(select(UpsellOpportunity).where(UpsellOpportunity.id == opportunity_id))
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    opp.is_dismissed = True
    await db.flush()
    return {"dismissed": True}


@router.get("/revenue-opportunity", response_model=RevenueOpportunityReport)
async def get_revenue_opportunity(
    store_id: int,
    period_days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await compute_revenue_opportunity(store_id, db, period_days)


@router.post("/run")
async def run_analysis(
    store_id: int,
    period_days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager),
):
    """Manually trigger full analysis re-run for a store."""
    gaps = await run_gap_analysis(store_id, db, period_days)
    upsells = await run_upsell_analysis(store_id, db, period_days)
    return {"gaps_computed": gaps, "upsells_computed": upsells, "status": "complete"}


@router.get("/multistore", response_model=list[MultiStoreComparison])
async def get_multistore_comparison(
    period_days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager),
):
    stores_result = await db.execute(select(Store))
    stores = stores_result.scalars().all()

    comparisons = []
    for store in stores:
        # Revenue
        from datetime import date, timedelta
        period_end = date.today()
        period_start = period_end - timedelta(days=period_days)
        rev_result = await db.execute(
            select(func.sum(Transaction.net_revenue))
            .where(
                and_(
                    Transaction.store_id == store.id,
                    Transaction.transaction_date >= period_start,
                    Transaction.net_revenue > 0,
                )
            )
        )
        revenue = Decimal(str(rev_result.scalar() or 0))

        # Top gap
        gap_result = await db.execute(
            select(PricingGap)
            .where(and_(PricingGap.store_id == store.id, PricingGap.direction == "underpriced"))
            .order_by(PricingGap.revenue_impact.desc())
            .limit(1)
        )
        top_gap = gap_result.scalar_one_or_none()

        # Top upsell
        upsell_result = await db.execute(
            select(UpsellOpportunity)
            .where(and_(UpsellOpportunity.store_id == store.id, UpsellOpportunity.is_dismissed == False))
            .order_by(UpsellOpportunity.monthly_impact_est.desc())
            .limit(1)
        )
        top_upsell = upsell_result.scalar_one_or_none()

        # Underpriced count
        underpriced_result = await db.execute(
            select(func.count(PricingGap.id))
            .where(and_(PricingGap.store_id == store.id, PricingGap.direction == "underpriced"))
        )
        underpriced_count = underpriced_result.scalar() or 0

        # Total opportunity
        opp = await compute_revenue_opportunity(store.id, db, period_days)

        comparisons.append(MultiStoreComparison(
            store_id=store.id,
            store_name=store.name,
            store_number=store.store_number,
            current_revenue=revenue,
            total_opportunity=opp.total_monthly_opportunity,
            top_gap_service=top_gap.service_name if top_gap else None,
            top_gap_amount=top_gap.revenue_impact if top_gap else None,
            top_upsell_service=top_upsell.recommended_service if top_upsell else None,
            top_upsell_impact=top_upsell.monthly_impact_est if top_upsell else None,
            underpriced_service_count=underpriced_count,
        ))

    return comparisons
