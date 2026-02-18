from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import date, timedelta
from decimal import Decimal
from app.database import get_db
from app.models.transaction import Transaction
from app.models.pricing import PricingGap
from app.models.analysis import UpsellOpportunity
from app.models.upload import UploadBatch
from app.schemas.dashboard import DashboardSummary
from app.schemas.pricing import PricingGapSchema
from app.schemas.analysis import UpsellOpportunitySchema
from app.dependencies import get_current_user
from app.services.revenue_calculator import compute_revenue_opportunity

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardSummary)
async def get_dashboard(
    store_id: int,
    period_days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    period_end = date.today()
    period_start = period_end - timedelta(days=period_days)
    prior_start = period_start - timedelta(days=period_days)

    # Total revenue current period
    cur_rev_result = await db.execute(
        select(func.sum(Transaction.net_revenue))
        .where(
            and_(
                Transaction.store_id == store_id,
                Transaction.transaction_date >= period_start,
                Transaction.net_revenue > 0,
            )
        )
    )
    current_revenue = Decimal(str(cur_rev_result.scalar() or 0))

    # Prior period revenue for comparison
    prior_rev_result = await db.execute(
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
    prior_revenue = Decimal(str(prior_rev_result.scalar() or 0))
    revenue_vs_prior = current_revenue - prior_revenue if prior_revenue > 0 else None

    # Transaction count
    txn_count_result = await db.execute(
        select(func.count(Transaction.id))
        .where(
            and_(
                Transaction.store_id == store_id,
                Transaction.transaction_date >= period_start,
            )
        )
    )
    txn_count = txn_count_result.scalar() or 0

    # Top 5 gaps
    gap_result = await db.execute(
        select(PricingGap)
        .where(and_(PricingGap.store_id == store_id, PricingGap.direction == "underpriced"))
        .order_by(PricingGap.revenue_impact.desc())
        .limit(5)
    )
    top_gaps = [PricingGapSchema.model_validate(g) for g in gap_result.scalars().all()]

    # Top 5 upsells
    upsell_result = await db.execute(
        select(UpsellOpportunity)
        .where(and_(UpsellOpportunity.store_id == store_id, UpsellOpportunity.is_dismissed == False))
        .order_by(UpsellOpportunity.monthly_impact_est.desc())
        .limit(5)
    )
    top_upsells = [UpsellOpportunitySchema.model_validate(u) for u in upsell_result.scalars().all()]

    # Revenue opportunity
    opp = await compute_revenue_opportunity(store_id, db, period_days)

    # Last upload date
    upload_result = await db.execute(
        select(UploadBatch.date_range_end)
        .where(and_(UploadBatch.store_id == store_id, UploadBatch.status == "complete"))
        .order_by(UploadBatch.uploaded_at.desc())
        .limit(1)
    )
    last_upload_date = upload_result.scalar_one_or_none()

    # Underpriced service count
    underpriced_result = await db.execute(
        select(func.count(PricingGap.id))
        .where(and_(PricingGap.store_id == store_id, PricingGap.direction == "underpriced"))
    )
    underpriced_count = underpriced_result.scalar() or 0

    # High priority upsells count
    high_priority_result = await db.execute(
        select(func.count(UpsellOpportunity.id))
        .where(
            and_(
                UpsellOpportunity.store_id == store_id,
                UpsellOpportunity.priority == "high",
                UpsellOpportunity.is_dismissed == False,
            )
        )
    )
    high_priority_count = high_priority_result.scalar() or 0

    return DashboardSummary(
        store_id=store_id,
        period_days=period_days,
        period_start=period_start,
        period_end=period_end,
        total_revenue=current_revenue,
        revenue_vs_prior_period=revenue_vs_prior,
        transactions_analyzed=txn_count,
        top_gaps=top_gaps,
        top_upsells=top_upsells,
        total_opportunity_est=opp.total_monthly_opportunity,
        last_upload_date=last_upload_date,
        underpriced_services=underpriced_count,
        high_priority_upsells=high_priority_count,
    )
