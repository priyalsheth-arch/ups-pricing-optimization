"""Pricing gap analysis engine."""

from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete
from app.models.transaction import Transaction
from app.models.pricing import OurPrice, CompetitorPrice, PricingGap, ServiceTaxonomy


async def run_gap_analysis(store_id: int, db: AsyncSession, period_days: int = 30) -> int:
    """
    Compute pricing gaps for a store over the given period.
    Materializes results into pricing_gaps table.
    Returns count of gaps written.
    """
    period_end = date.today()
    period_start = period_end - timedelta(days=period_days)
    analysis_date = date.today()

    # Step 1: Realized prices from transactions
    txn_result = await db.execute(
        select(
            Transaction.service_code,
            Transaction.service_category,
            func.sum(Transaction.net_revenue).label("total_revenue"),
            func.sum(Transaction.quantity).label("total_qty"),
            func.count(Transaction.id).label("txn_count"),
        )
        .where(
            and_(
                Transaction.store_id == store_id,
                Transaction.transaction_date >= period_start,
                Transaction.transaction_date <= period_end,
                Transaction.service_code.isnot(None),
                Transaction.net_revenue > 0,
            )
        )
        .group_by(Transaction.service_code, Transaction.service_category)
    )
    txn_rows = txn_result.fetchall()

    if not txn_rows:
        return 0

    # Step 2: Our latest listed prices
    our_prices_result = await db.execute(
        select(OurPrice)
        .where(OurPrice.store_id == store_id)
        .order_by(OurPrice.effective_date.desc())
    )
    our_prices_list = our_prices_result.scalars().all()
    our_prices_map: dict[str, OurPrice] = {}
    for op in our_prices_list:
        if op.service_code not in our_prices_map:
            our_prices_map[op.service_code] = op

    # Step 3: Competitor prices
    comp_result = await db.execute(
        select(CompetitorPrice).order_by(CompetitorPrice.effective_date.desc())
    )
    comp_prices = comp_result.scalars().all()
    # Map: service_code → {competitor_name: CompetitorPrice}
    comp_map: dict[str, dict[str, CompetitorPrice]] = {}
    for cp in comp_prices:
        if cp.service_code not in comp_map:
            comp_map[cp.service_code] = {}
        if cp.competitor_name not in comp_map[cp.service_code]:
            comp_map[cp.service_code][cp.competitor_name] = cp

    # Step 4: Service taxonomy names
    taxonomy_result = await db.execute(select(ServiceTaxonomy))
    taxonomy = {t.service_code: t for t in taxonomy_result.scalars().all()}

    # Step 5: Delete old gaps for this store+period, recompute
    await db.execute(
        delete(PricingGap).where(
            and_(PricingGap.store_id == store_id, PricingGap.analysis_date == analysis_date)
        )
    )

    gaps_written = 0
    for row in txn_rows:
        service_code = row.service_code
        service_category = row.service_category
        txn_count = row.txn_count
        total_revenue = Decimal(str(row.total_revenue or 0))
        total_qty = Decimal(str(row.total_qty or 1))
        avg_realized = total_revenue / total_qty if total_qty > 0 else Decimal("0")

        our_price_obj = our_prices_map.get(service_code)
        our_price_val = our_price_obj.price if our_price_obj else avg_realized

        service_name = taxonomy.get(service_code, None)
        service_name_str = service_name.service_name if service_name else service_code

        competitors = comp_map.get(service_code, {})
        if not competitors:
            continue

        for comp_name, comp_price_obj in competitors.items():
            comp_price_val = comp_price_obj.price
            gap_amount = comp_price_val - avg_realized
            gap_pct = (gap_amount / avg_realized) if avg_realized > 0 else None

            if gap_pct is not None:
                if gap_pct > Decimal("0.05"):
                    direction = "underpriced"
                elif gap_pct < Decimal("-0.05"):
                    direction = "overpriced"
                else:
                    direction = "competitive"
            else:
                direction = None

            revenue_impact = gap_amount * txn_count

            gap = PricingGap(
                store_id=store_id,
                service_code=service_code,
                service_category=service_category,
                service_name=service_name_str,
                our_price=avg_realized,
                competitor_name=comp_name,
                competitor_price=comp_price_val,
                gap_amount=gap_amount,
                gap_pct=gap_pct,
                direction=direction,
                transaction_volume=txn_count,
                revenue_impact=revenue_impact,
                analysis_date=analysis_date,
                period_start=period_start,
                period_end=period_end,
            )
            db.add(gap)
            gaps_written += 1

    await db.flush()
    return gaps_written
