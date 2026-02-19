"""Tests for the upsell rule engine."""

from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.upsell_engine import run_upsell_analysis, _get_priority, UPSELL_RULES
from app.models.analysis import UpsellOpportunity
from tests.conftest import make_transaction


# ---------------------------------------------------------------------------
# _get_priority helper
# ---------------------------------------------------------------------------

def test_priority_high():
    rule = next(r for r in UPSELL_RULES if r.rule_id == "S1")
    assert _get_priority(rule.priority_threshold_high, rule) == "high"

def test_priority_medium():
    rule = next(r for r in UPSELL_RULES if r.rule_id == "S1")
    assert _get_priority(rule.priority_threshold_medium, rule) == "medium"

def test_priority_low():
    rule = next(r for r in UPSELL_RULES if r.rule_id == "S1")
    assert _get_priority(rule.priority_threshold_medium - 1, rule) == "low"


# ---------------------------------------------------------------------------
# run_upsell_analysis
# ---------------------------------------------------------------------------

async def test_upsell_no_transactions(seeded_db: AsyncSession):
    """No transactions → 0 opportunities."""
    count = await run_upsell_analysis(store_id=1, db=seeded_db, period_days=30)
    assert count == 0


async def test_upsell_S1_ground_shipping_continental(seeded_db: AsyncSession):
    """Rule S1: ground shipment ≤10 lbs to continental US → S1 opportunity fired."""
    seeded_db.add(make_transaction(
        store_id=1,
        connectsuite_txn_id="S1-001",
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

    opps = (await seeded_db.execute(
        select(UpsellOpportunity).where(
            UpsellOpportunity.store_id == 1,
            UpsellOpportunity.rule_id == "S1",
        )
    )).scalars().all()
    assert len(opps) == 1
    assert opps[0].recommended_service_code == "UPS_2DAY"


async def test_upsell_S1_does_not_fire_for_heavy_package(seeded_db: AsyncSession):
    """Rule S1 should not fire for packages > 10 lbs."""
    seeded_db.add(make_transaction(
        store_id=1,
        connectsuite_txn_id="S1-HEAVY",
        transaction_date=date.today() - timedelta(days=5),
        service_category="shipping",
        service_code="UPS_GROUND",
        service_level="ground",
        weight_lbs=Decimal("15.0"),
        destination_state="GA",
        net_revenue=Decimal("18.00"),
    ))
    await seeded_db.flush()

    await run_upsell_analysis(store_id=1, db=seeded_db, period_days=30)

    opps = (await seeded_db.execute(
        select(UpsellOpportunity).where(
            UpsellOpportunity.store_id == 1,
            UpsellOpportunity.rule_id == "S1",
        )
    )).scalars().all()
    assert len(opps) == 0


async def test_upsell_P1_bw_copies_qty_threshold(seeded_db: AsyncSession):
    """Rule P1: B&W copies qty >= 10 → upgrade to color."""
    seeded_db.add(make_transaction(
        store_id=1,
        connectsuite_txn_id="P1-001",
        transaction_date=date.today() - timedelta(days=3),
        service_category="printing",
        service_code="BW_COPY",
        quantity=Decimal("25"),
        net_revenue=Decimal("3.75"),
        service_level=None,
        carrier=None,
        weight_lbs=None,
        destination_state=None,
    ))
    await seeded_db.flush()

    await run_upsell_analysis(store_id=1, db=seeded_db, period_days=30)

    opps = (await seeded_db.execute(
        select(UpsellOpportunity).where(
            UpsellOpportunity.store_id == 1,
            UpsellOpportunity.rule_id == "P1",
        )
    )).scalars().all()
    assert len(opps) == 1


async def test_upsell_P1_does_not_fire_below_threshold(seeded_db: AsyncSession):
    """Rule P1 should not fire when qty < 10."""
    seeded_db.add(make_transaction(
        store_id=1,
        connectsuite_txn_id="P1-SMALL",
        transaction_date=date.today() - timedelta(days=3),
        service_category="printing",
        service_code="BW_COPY",
        quantity=Decimal("5"),
        net_revenue=Decimal("0.75"),
        service_level=None,
        carrier=None,
        weight_lbs=None,
        destination_state=None,
    ))
    await seeded_db.flush()

    await run_upsell_analysis(store_id=1, db=seeded_db, period_days=30)

    opps = (await seeded_db.execute(
        select(UpsellOpportunity).where(
            UpsellOpportunity.store_id == 1,
            UpsellOpportunity.rule_id == "P1",
        )
    )).scalars().all()
    assert len(opps) == 0


async def test_upsell_M1_mailbox_without_notification(seeded_db: AsyncSession):
    """Rule M1: mailbox session without NOTIF code → notification upsell."""
    seeded_db.add(make_transaction(
        store_id=1,
        connectsuite_txn_id="M1-001",
        transaction_date=date.today() - timedelta(days=2),
        service_category="mailbox",
        service_code="MB_BASIC",
        quantity=Decimal("1"),
        net_revenue=Decimal("25.00"),
        service_level=None,
        carrier=None,
        weight_lbs=None,
        destination_state=None,
        customer_ref="CUST-001",
    ))
    await seeded_db.flush()

    await run_upsell_analysis(store_id=1, db=seeded_db, period_days=30)

    opps = (await seeded_db.execute(
        select(UpsellOpportunity).where(
            UpsellOpportunity.store_id == 1,
            UpsellOpportunity.rule_id == "M1",
        )
    )).scalars().all()
    assert len(opps) == 1
    assert opps[0].recommended_service_code == "MAILBOX_NOTIF"


async def test_upsell_results_have_staff_script(seeded_db: AsyncSession):
    """Every opportunity should include a non-empty staff script."""
    seeded_db.add(make_transaction(
        store_id=1,
        connectsuite_txn_id="SS-001",
        transaction_date=date.today() - timedelta(days=3),
        service_category="shipping",
        service_code="UPS_GROUND",
        service_level="ground",
        weight_lbs=Decimal("4.0"),
        destination_state="FL",
        net_revenue=Decimal("12.50"),
    ))
    await seeded_db.flush()

    await run_upsell_analysis(store_id=1, db=seeded_db, period_days=30)

    opps = (await seeded_db.execute(
        select(UpsellOpportunity).where(UpsellOpportunity.store_id == 1)
    )).scalars().all()

    assert len(opps) > 0
    for opp in opps:
        assert opp.staff_script and len(opp.staff_script) > 10


async def test_upsell_does_not_fire_for_null_customer_ref(seeded_db: AsyncSession):
    """Sessions with null customer_ref should not cause errors (C1/C2/M1 rules)."""
    seeded_db.add(make_transaction(
        store_id=1,
        connectsuite_txn_id="NULL-CUST",
        transaction_date=date.today() - timedelta(days=3),
        service_category="packing",
        service_code="PACK_SVC",
        quantity=Decimal("1"),
        net_revenue=Decimal("15.00"),
        service_level=None,
        carrier=None,
        weight_lbs=None,
        destination_state=None,
        customer_ref=None,
    ))
    await seeded_db.flush()

    # Should not raise
    count = await run_upsell_analysis(store_id=1, db=seeded_db, period_days=30)
    assert count >= 0


async def test_upsell_rerun_does_not_duplicate(seeded_db: AsyncSession):
    """Running analysis twice on the same day should not create duplicate records."""
    seeded_db.add(make_transaction(
        store_id=1,
        connectsuite_txn_id="DUP-001",
        transaction_date=date.today() - timedelta(days=3),
        service_category="shipping",
        service_code="UPS_GROUND",
        service_level="ground",
        weight_lbs=Decimal("2.0"),
        destination_state="GA",
        net_revenue=Decimal("12.50"),
    ))
    await seeded_db.flush()

    count1 = await run_upsell_analysis(store_id=1, db=seeded_db, period_days=30)
    count2 = await run_upsell_analysis(store_id=1, db=seeded_db, period_days=30)

    assert count1 == count2
    all_opps = (await seeded_db.execute(
        select(UpsellOpportunity).where(UpsellOpportunity.store_id == 1)
    )).scalars().all()
    assert len(all_opps) == count1
