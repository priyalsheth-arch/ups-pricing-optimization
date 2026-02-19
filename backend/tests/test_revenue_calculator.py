"""Tests for the three-bucket revenue opportunity calculator."""

from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.revenue_calculator import compute_revenue_opportunity
from app.services.pricing_engine import run_gap_analysis
from app.services.upsell_engine import run_upsell_analysis
from app.models.pricing import PricingGap
from app.models.analysis import UpsellOpportunity
from app.schemas.analysis import OpportunityAssumptions
from tests.conftest import make_transaction


async def test_revenue_opportunity_empty_db(seeded_db: AsyncSession):
    """No transactions, gaps, or upsells → all buckets are zero."""
    report = await compute_revenue_opportunity(store_id=1, db=seeded_db, period_days=30)
    assert report.total_monthly_opportunity == Decimal("0")
    assert report.annual_opportunity == Decimal("0")
    assert report.pricing_gap_opportunity == Decimal("0")
    assert report.upsell_opportunity == Decimal("0")
    assert report.addon_opportunity == Decimal("0")


async def test_revenue_opportunity_annual_is_monthly_times_12(seeded_db: AsyncSession):
    """Annual opportunity must equal monthly × 12."""
    report = await compute_revenue_opportunity(store_id=1, db=seeded_db, period_days=30)
    assert report.annual_opportunity == report.total_monthly_opportunity * Decimal("12")


async def test_revenue_opportunity_bucket_a_from_gaps(seeded_db: AsyncSession):
    """Bucket A should be non-zero when there are underpriced gaps."""
    # Add transaction so gap analysis has data
    seeded_db.add(make_transaction(
        store_id=1,
        connectsuite_txn_id="RA-001",
        transaction_date=date.today() - timedelta(days=5),
        service_code="UPS_GROUND",
        service_category="shipping",
        net_revenue=Decimal("12.50"),
        quantity=Decimal("1"),
    ))
    await seeded_db.flush()
    await run_gap_analysis(store_id=1, db=seeded_db, period_days=30)

    report = await compute_revenue_opportunity(store_id=1, db=seeded_db, period_days=30)
    assert report.pricing_gap_opportunity > Decimal("0")


async def test_revenue_opportunity_bucket_b_from_upsells(seeded_db: AsyncSession):
    """Bucket B should be non-zero when upsell opportunities exist."""
    seeded_db.add(make_transaction(
        store_id=1,
        connectsuite_txn_id="RB-001",
        transaction_date=date.today() - timedelta(days=5),
        service_category="shipping",
        service_code="UPS_GROUND",
        service_level="ground",
        weight_lbs=Decimal("3.0"),
        destination_state="GA",
        net_revenue=Decimal("12.50"),
    ))
    await seeded_db.flush()
    await run_upsell_analysis(store_id=1, db=seeded_db, period_days=30)

    report = await compute_revenue_opportunity(store_id=1, db=seeded_db, period_days=30)
    assert report.upsell_opportunity > Decimal("0")


async def test_revenue_opportunity_bucket_c_packing(seeded_db: AsyncSession):
    """Bucket C should be non-zero when packing transactions exist in period."""
    seeded_db.add(make_transaction(
        store_id=1,
        connectsuite_txn_id="RC-001",
        transaction_date=date.today() - timedelta(days=3),
        service_category="packing",
        service_code="PACK_SVC",
        quantity=Decimal("1"),
        net_revenue=Decimal("15.00"),
        service_level=None,
        carrier=None,
        weight_lbs=None,
        destination_state=None,
    ))
    await seeded_db.flush()

    report = await compute_revenue_opportunity(store_id=1, db=seeded_db, period_days=30)
    assert report.addon_opportunity > Decimal("0")


async def test_revenue_opportunity_custom_assumptions(seeded_db: AsyncSession):
    """Custom assumptions (zero elasticity) should produce different result than defaults."""
    seeded_db.add(make_transaction(
        store_id=1,
        connectsuite_txn_id="CA-001",
        transaction_date=date.today() - timedelta(days=5),
        service_code="UPS_GROUND",
        service_category="shipping",
        net_revenue=Decimal("12.50"),
        quantity=Decimal("1"),
    ))
    await seeded_db.flush()
    await run_gap_analysis(store_id=1, db=seeded_db, period_days=30)

    zero_elasticity = OpportunityAssumptions(
        price_elasticity_factor=0.0,
        max_price_increase_pct=0.15,
        packing_supplies_attach=0.15,
        printing_finishing_attach=0.10,
    )
    high_elasticity = OpportunityAssumptions(
        price_elasticity_factor=0.5,
        max_price_increase_pct=0.15,
        packing_supplies_attach=0.15,
        printing_finishing_attach=0.10,
    )

    report_zero = await compute_revenue_opportunity(
        store_id=1, db=seeded_db, period_days=30, assumptions=zero_elasticity
    )
    report_high = await compute_revenue_opportunity(
        store_id=1, db=seeded_db, period_days=30, assumptions=high_elasticity
    )
    # Lower elasticity → higher opportunity (less volume loss assumed)
    assert report_zero.pricing_gap_opportunity >= report_high.pricing_gap_opportunity


async def test_revenue_opportunity_by_category_totals(seeded_db: AsyncSession):
    """Sum of by_category totals should equal total_monthly_opportunity."""
    seeded_db.add(make_transaction(
        store_id=1,
        connectsuite_txn_id="CAT-001",
        transaction_date=date.today() - timedelta(days=5),
        service_code="UPS_GROUND",
        service_category="shipping",
        net_revenue=Decimal("12.50"),
        quantity=Decimal("1"),
    ))
    await seeded_db.flush()
    await run_gap_analysis(store_id=1, db=seeded_db, period_days=30)

    report = await compute_revenue_opportunity(store_id=1, db=seeded_db, period_days=30)
    cat_total = sum(c.total for c in report.by_category)
    assert abs(cat_total - report.total_monthly_opportunity) < Decimal("0.01")


async def test_revenue_opportunity_period_revenue_tracking(seeded_db: AsyncSession):
    """Current period revenue should reflect transactions within the window."""
    recent_txn = make_transaction(
        store_id=1,
        connectsuite_txn_id="PR-001",
        transaction_date=date.today() - timedelta(days=5),
        net_revenue=Decimal("50.00"),
    )
    old_txn = make_transaction(
        store_id=1,
        connectsuite_txn_id="PR-OLD",
        transaction_date=date.today() - timedelta(days=90),
        net_revenue=Decimal("200.00"),
    )
    seeded_db.add_all([recent_txn, old_txn])
    await seeded_db.flush()

    report = await compute_revenue_opportunity(store_id=1, db=seeded_db, period_days=30)
    assert report.current_period_revenue == Decimal("50.00")
    # Transaction 90 days ago is outside both current (0-30d) and prior (30-60d) windows
    assert report.prior_period_revenue == Decimal("0")
