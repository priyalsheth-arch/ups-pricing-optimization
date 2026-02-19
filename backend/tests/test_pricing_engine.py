"""Tests for pricing gap analysis engine."""

from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.pricing_engine import run_gap_analysis
from app.models.pricing import PricingGap
from tests.conftest import make_transaction



async def test_gap_analysis_no_transactions(seeded_db: AsyncSession):
    """No transactions → 0 gaps written."""
    count = await run_gap_analysis(store_id=1, db=seeded_db, period_days=30)
    assert count == 0


async def test_gap_analysis_underpriced(seeded_db: AsyncSession):
    """UPS_GROUND at $12.50 vs FedEx $14.00 → underpriced gap."""
    txn = make_transaction(
        store_id=1,
        connectsuite_txn_id="T-001",
        transaction_date=date.today() - timedelta(days=3),
        service_code="UPS_GROUND",
        service_category="shipping",
        net_revenue=Decimal("12.50"),
        quantity=Decimal("1"),
    )
    seeded_db.add(txn)
    await seeded_db.flush()

    count = await run_gap_analysis(store_id=1, db=seeded_db, period_days=30)
    assert count > 0

    gaps = (await seeded_db.execute(
        select(PricingGap).where(PricingGap.store_id == 1, PricingGap.service_code == "UPS_GROUND")
    )).scalars().all()

    fedex_gap = next((g for g in gaps if g.competitor_name == "FedEx"), None)
    assert fedex_gap is not None
    assert fedex_gap.direction == "underpriced"
    assert fedex_gap.gap_amount > 0


async def test_gap_analysis_overpriced(seeded_db: AsyncSession):
    """UPS_GROUND at $12.50 vs USPS $11.50 → overpriced gap."""
    txn = make_transaction(
        store_id=1,
        connectsuite_txn_id="T-002",
        transaction_date=date.today() - timedelta(days=3),
        service_code="UPS_GROUND",
        service_category="shipping",
        net_revenue=Decimal("12.50"),
    )
    seeded_db.add(txn)
    await seeded_db.flush()

    await run_gap_analysis(store_id=1, db=seeded_db, period_days=30)

    gaps = (await seeded_db.execute(
        select(PricingGap).where(PricingGap.store_id == 1, PricingGap.competitor_name == "USPS")
    )).scalars().all()

    assert len(gaps) > 0
    usps_gap = gaps[0]
    assert usps_gap.direction == "overpriced"
    assert usps_gap.gap_amount < 0


async def test_gap_analysis_revenue_impact(seeded_db: AsyncSession):
    """Revenue impact = gap_amount × txn_count."""
    for i in range(5):
        seeded_db.add(make_transaction(
            store_id=1,
            connectsuite_txn_id=f"T-{i:03d}",
            transaction_date=date.today() - timedelta(days=i + 1),
            service_code="UPS_GROUND",
            service_category="shipping",
            net_revenue=Decimal("12.50"),
        ))
    await seeded_db.flush()

    await run_gap_analysis(store_id=1, db=seeded_db, period_days=30)

    gaps = (await seeded_db.execute(
        select(PricingGap).where(
            PricingGap.store_id == 1,
            PricingGap.service_code == "UPS_GROUND",
            PricingGap.competitor_name == "FedEx",
        )
    )).scalars().all()

    assert len(gaps) == 1
    gap = gaps[0]
    assert gap.transaction_volume == 5
    expected_impact = gap.gap_amount * 5
    assert abs(gap.revenue_impact - expected_impact) < Decimal("0.01")


async def test_gap_analysis_excludes_old_transactions(seeded_db: AsyncSession):
    """Transactions outside the period window are ignored."""
    old_txn = make_transaction(
        store_id=1,
        connectsuite_txn_id="OLD-001",
        transaction_date=date.today() - timedelta(days=45),
        service_code="UPS_GROUND",
        service_category="shipping",
        net_revenue=Decimal("12.50"),
    )
    seeded_db.add(old_txn)
    await seeded_db.flush()

    count = await run_gap_analysis(store_id=1, db=seeded_db, period_days=30)
    assert count == 0


async def test_gap_analysis_skips_service_without_competitor(seeded_db: AsyncSession):
    """Service with no competitor prices is skipped (no gap record created)."""
    txn = make_transaction(
        store_id=1,
        connectsuite_txn_id="PACK-001",
        transaction_date=date.today() - timedelta(days=3),
        service_code="PACK_SVC",
        service_category="packing",
        net_revenue=Decimal("15.00"),
    )
    seeded_db.add(txn)
    await seeded_db.flush()

    await run_gap_analysis(store_id=1, db=seeded_db, period_days=30)

    gaps = (await seeded_db.execute(
        select(PricingGap).where(PricingGap.service_code == "PACK_SVC")
    )).scalars().all()
    assert len(gaps) == 0


async def test_gap_analysis_recomputes_on_rerun(seeded_db: AsyncSession):
    """Running analysis twice should not duplicate gaps (deletes and rewrites)."""
    txn = make_transaction(
        store_id=1,
        connectsuite_txn_id="R-001",
        transaction_date=date.today() - timedelta(days=2),
        service_code="UPS_GROUND",
        service_category="shipping",
        net_revenue=Decimal("12.50"),
    )
    seeded_db.add(txn)
    await seeded_db.flush()

    count1 = await run_gap_analysis(store_id=1, db=seeded_db, period_days=30)
    count2 = await run_gap_analysis(store_id=1, db=seeded_db, period_days=30)
    assert count1 == count2

    gaps = (await seeded_db.execute(select(PricingGap).where(PricingGap.store_id == 1))).scalars().all()
    assert len(gaps) == count1


async def test_gap_analysis_service_name_from_taxonomy(seeded_db: AsyncSession):
    """Gap records should use the human-readable service name from taxonomy."""
    txn = make_transaction(
        store_id=1,
        connectsuite_txn_id="N-001",
        transaction_date=date.today() - timedelta(days=1),
        service_code="UPS_GROUND",
        service_category="shipping",
        net_revenue=Decimal("12.50"),
    )
    seeded_db.add(txn)
    await seeded_db.flush()

    await run_gap_analysis(store_id=1, db=seeded_db, period_days=30)

    gap = (await seeded_db.execute(
        select(PricingGap).where(PricingGap.service_code == "UPS_GROUND").limit(1)
    )).scalar_one()
    assert gap.service_name == "UPS Ground"
