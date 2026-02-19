"""Upsell opportunity engine — applies rule-based analysis to transaction history."""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete
from app.models.transaction import Transaction
from app.models.pricing import OurPrice
from app.models.analysis import UpsellOpportunity
from app.utils.csv_mappings import CONTINENTAL_US_STATES, BASIC_MAILBOX_CODES


@dataclass
class UpsellRule:
    rule_id: str
    opportunity_type: str  # service_upgrade | addon | cross_sell
    trigger_category: str
    recommended_service: str
    recommended_service_code: str
    conversion_rate_default: float
    priority_threshold_high: float  # monthly_impact above this → HIGH
    priority_threshold_medium: float
    staff_script: str


UPSELL_RULES: list[UpsellRule] = [
    UpsellRule(
        rule_id="S1",
        opportunity_type="service_upgrade",
        trigger_category="shipping",
        recommended_service="UPS 2-Day Air",
        recommended_service_code="UPS_2DAY",
        conversion_rate_default=0.12,
        priority_threshold_high=500.0,
        priority_threshold_medium=100.0,
        staff_script=(
            "For time-sensitive packages, UPS 2-Day Air guarantees delivery by end of day "
            "the second business day. Would you like to upgrade for just a few dollars more?"
        ),
    ),
    UpsellRule(
        rule_id="S2",
        opportunity_type="service_upgrade",
        trigger_category="shipping",
        recommended_service="UPS 3 Day Select",
        recommended_service_code="UPS_3DAY",
        conversion_rate_default=0.18,
        priority_threshold_high=400.0,
        priority_threshold_medium=80.0,
        staff_script=(
            "UPS 3 Day Select gives your customer a guaranteed delivery window at a great value. "
            "It's only a small upgrade from ground — would that work?"
        ),
    ),
    UpsellRule(
        rule_id="S3",
        opportunity_type="addon",
        trigger_category="shipping",
        recommended_service="Declared Value Coverage",
        recommended_service_code="DECLARED_VALUE",
        conversion_rate_default=0.25,
        priority_threshold_high=300.0,
        priority_threshold_medium=60.0,
        staff_script=(
            "This package looks valuable. UPS only covers up to $100 by default — "
            "would you like to add declared value coverage to protect the full value?"
        ),
    ),
    UpsellRule(
        rule_id="S4",
        opportunity_type="addon",
        trigger_category="shipping",
        recommended_service="Signature Required",
        recommended_service_code="SIG_REQUIRED",
        conversion_rate_default=0.20,
        priority_threshold_high=200.0,
        priority_threshold_medium=50.0,
        staff_script=(
            "Would you like to add signature confirmation? It ensures the package is "
            "only delivered to the recipient — great for important documents or valuables."
        ),
    ),
    UpsellRule(
        rule_id="P1",
        opportunity_type="service_upgrade",
        trigger_category="printing",
        recommended_service="Color Print / Color Copies",
        recommended_service_code="COLOR_PRINT",
        conversion_rate_default=0.15,
        priority_threshold_high=300.0,
        priority_threshold_medium=60.0,
        staff_script=(
            "Color copies make a much stronger impression for presentations and marketing materials. "
            "Would you like to upgrade to color for this print job?"
        ),
    ),
    UpsellRule(
        rule_id="P2",
        opportunity_type="service_upgrade",
        trigger_category="printing",
        recommended_service="Full-Service Printing (staff-assisted)",
        recommended_service_code="FULLSERVICE_PRINT",
        conversion_rate_default=0.10,
        priority_threshold_high=200.0,
        priority_threshold_medium=40.0,
        staff_script=(
            "For large jobs like this, our staff can handle everything — file prep, quality check, "
            "and finishing. Would you like us to manage it from start to finish?"
        ),
    ),
    UpsellRule(
        rule_id="P3",
        opportunity_type="addon",
        trigger_category="printing",
        recommended_service="Document Binding / Lamination",
        recommended_service_code="BINDING",
        conversion_rate_default=0.22,
        priority_threshold_high=250.0,
        priority_threshold_medium=50.0,
        staff_script=(
            "We can bind or laminate this for a professional finish. "
            "It's a great way to protect and present your documents — interested?"
        ),
    ),
    UpsellRule(
        rule_id="C1",
        opportunity_type="cross_sell",
        trigger_category="packing",
        recommended_service="Packing Supplies Bundle",
        recommended_service_code="SUPPLIES_BUNDLE",
        conversion_rate_default=0.35,
        priority_threshold_high=300.0,
        priority_threshold_medium=60.0,
        staff_script=(
            "We also carry bubble wrap, packing peanuts, and tape — "
            "would you like a supplies bundle to protect your items even better?"
        ),
    ),
    UpsellRule(
        rule_id="C2",
        opportunity_type="cross_sell",
        trigger_category="shipping",
        recommended_service="Professional Packing Service",
        recommended_service_code="PACKING_SVC",
        conversion_rate_default=0.08,
        priority_threshold_high=200.0,
        priority_threshold_medium=40.0,
        staff_script=(
            "We offer professional packing to make sure your item is protected for shipping. "
            "Would you like us to take care of that for you?"
        ),
    ),
    UpsellRule(
        rule_id="M1",
        opportunity_type="addon",
        trigger_category="mailbox",
        recommended_service="Package Notification Add-on",
        recommended_service_code="MAILBOX_NOTIF",
        conversion_rate_default=0.30,
        priority_threshold_high=150.0,
        priority_threshold_medium=30.0,
        staff_script=(
            "Would you like to add package notifications to your mailbox? "
            "We'll text or email you the moment a package arrives for you."
        ),
    ),
]


def _get_priority(monthly_impact: float, rule: UpsellRule) -> str:
    if monthly_impact >= rule.priority_threshold_high:
        return "high"
    elif monthly_impact >= rule.priority_threshold_medium:
        return "medium"
    return "low"


async def _get_price_delta(
    rule: UpsellRule,
    db: AsyncSession,
    store_id: int,
    avg_realized_price: Decimal,
) -> Decimal:
    """Look up recommended service price and compute delta vs trigger."""
    result = await db.execute(
        select(OurPrice)
        .where(
            and_(
                OurPrice.store_id == store_id,
                OurPrice.service_code == rule.recommended_service_code,
            )
        )
        .order_by(OurPrice.effective_date.desc())
        .limit(1)
    )
    our_price = result.scalar_one_or_none()
    if our_price:
        return our_price.price - avg_realized_price
    # Fallback: use a reasonable default delta per rule type
    defaults = {
        "S1": Decimal("4.50"), "S2": Decimal("2.50"), "S3": Decimal("3.00"),
        "S4": Decimal("2.00"), "P1": Decimal("0.15"), "P2": Decimal("0.10"),
        "P3": Decimal("5.00"), "C1": Decimal("8.50"), "C2": Decimal("18.00"),
        "M1": Decimal("4.00"),
    }
    return defaults.get(rule.rule_id, Decimal("3.00"))


async def run_upsell_analysis(store_id: int, db: AsyncSession, period_days: int = 30) -> int:
    """
    Analyze transactions and fire upsell rules.
    Materializes results into upsell_opportunities table.
    Returns count of opportunities written.
    """
    period_end = date.today()
    period_start = period_end - timedelta(days=period_days)
    analysis_date = date.today()

    # Clear previous analysis for this store
    await db.execute(
        delete(UpsellOpportunity).where(
            and_(UpsellOpportunity.store_id == store_id, UpsellOpportunity.analysis_date == analysis_date)
        )
    )

    # Build session-level groupings: sessions where certain services co-occur
    # A "session" here = same connectsuite_txn_id prefix or same date + customer_ref
    # For simplicity, group by transaction_date + customer_ref as a proxy session
    session_result = await db.execute(
        select(
            Transaction.transaction_date,
            Transaction.customer_ref,
            func.group_concat(Transaction.service_category).label("categories"),
            func.group_concat(Transaction.service_code).label("service_codes"),
        )
        .where(
            and_(
                Transaction.store_id == store_id,
                Transaction.transaction_date >= period_start,
                Transaction.transaction_date <= period_end,
            )
        )
        .group_by(Transaction.transaction_date, Transaction.customer_ref)
    )
    sessions = session_result.fetchall()

    # Build sets of service codes per session for cross-sell detection
    session_categories: dict[tuple, set[str]] = {}
    session_service_codes: dict[tuple, set[str]] = {}
    for s in sessions:
        key = (str(s.transaction_date), str(s.customer_ref))
        cats = set((s.categories or "").upper().split(","))
        codes = set((s.service_codes or "").upper().split(","))
        session_categories[key] = cats
        session_service_codes[key] = codes

    opportunities_written = 0
    for rule in UPSELL_RULES:
        # Query aggregate stats for this rule's trigger category
        agg_result = await db.execute(
            select(
                func.count(Transaction.id).label("txn_count"),
                func.avg(Transaction.net_revenue).label("avg_revenue"),
                func.avg(Transaction.weight_lbs).label("avg_weight"),
            )
            .where(
                and_(
                    Transaction.store_id == store_id,
                    Transaction.transaction_date >= period_start,
                    Transaction.transaction_date <= period_end,
                    Transaction.service_category == rule.trigger_category,
                )
            )
        )
        agg = agg_result.one()
        txn_count = agg.txn_count or 0
        avg_revenue = Decimal(str(agg.avg_revenue or 0))

        if txn_count == 0:
            continue

        # Rule-specific filtering
        qualifying_count = txn_count  # start with all, narrow down per rule

        if rule.rule_id == "S1":
            # Ground shipping, ≤10 lbs, continental US
            q = await db.execute(
                select(func.count(Transaction.id))
                .where(
                    and_(
                        Transaction.store_id == store_id,
                        Transaction.transaction_date >= period_start,
                        Transaction.service_category == "shipping",
                        Transaction.service_level == "ground",
                        Transaction.weight_lbs <= 10,
                        Transaction.destination_state.in_(list(CONTINENTAL_US_STATES)),
                    )
                )
            )
            qualifying_count = q.scalar() or 0

        elif rule.rule_id == "S2":
            q = await db.execute(
                select(func.count(Transaction.id))
                .where(
                    and_(
                        Transaction.store_id == store_id,
                        Transaction.transaction_date >= period_start,
                        Transaction.service_category == "shipping",
                        Transaction.service_level == "ground",
                        Transaction.destination_state.notin_(["AK", "HI", "PR"]),
                    )
                )
            )
            qualifying_count = q.scalar() or 0

        elif rule.rule_id == "S3":
            # High-value shipments without insurance in session
            q = await db.execute(
                select(func.count(Transaction.id))
                .where(
                    and_(
                        Transaction.store_id == store_id,
                        Transaction.transaction_date >= period_start,
                        Transaction.service_category == "shipping",
                        Transaction.net_revenue > 100,
                    )
                )
            )
            qualifying_count = q.scalar() or 0

        elif rule.rule_id == "S4":
            q = await db.execute(
                select(func.count(Transaction.id))
                .where(
                    and_(
                        Transaction.store_id == store_id,
                        Transaction.transaction_date >= period_start,
                        Transaction.service_category == "shipping",
                        Transaction.net_revenue > 75,
                    )
                )
            )
            qualifying_count = q.scalar() or 0

        elif rule.rule_id == "P1":
            # BW copies, qty >= 10
            q = await db.execute(
                select(func.count(Transaction.id))
                .where(
                    and_(
                        Transaction.store_id == store_id,
                        Transaction.transaction_date >= period_start,
                        Transaction.service_category == "printing",
                        Transaction.service_code.in_(["BW_COPY", "BW_PRINT", "BWCOPY", "BWPRINT"]),
                        Transaction.quantity >= 10,
                    )
                )
            )
            qualifying_count = q.scalar() or 0

        elif rule.rule_id == "P2":
            q = await db.execute(
                select(func.count(Transaction.id))
                .where(
                    and_(
                        Transaction.store_id == store_id,
                        Transaction.transaction_date >= period_start,
                        Transaction.service_code.in_(["SELF_SERVICE_COPY", "SELFCOPY", "SELF_COPY"]),
                        Transaction.quantity >= 25,
                    )
                )
            )
            qualifying_count = q.scalar() or 0

        elif rule.rule_id == "P3":
            q = await db.execute(
                select(func.count(Transaction.id))
                .where(
                    and_(
                        Transaction.store_id == store_id,
                        Transaction.transaction_date >= period_start,
                        Transaction.service_category == "printing",
                        Transaction.quantity >= 10,
                    )
                )
            )
            qualifying_count = q.scalar() or 0

        elif rule.rule_id in ("C1", "C2", "M1"):
            # Cross-sell: count sessions missing the add-on
            missing_count = 0
            for key, cats in session_categories.items():
                if rule.rule_id == "C1" and "PACKING" in cats and "SUPPLIES" not in cats:
                    missing_count += 1
                elif rule.rule_id == "C2" and "SHIPPING" in cats and "PACKING" not in cats:
                    missing_count += 1
                elif rule.rule_id == "M1" and "MAILBOX" in cats:
                    codes = session_service_codes.get(key, set())
                    if not any("NOTIF" in c for c in codes):
                        missing_count += 1
            qualifying_count = missing_count

        if qualifying_count == 0:
            continue

        # Estimate monthly volume (scale to 30 days)
        actual_days = period_days or 30
        monthly_volume = int(qualifying_count * 30 / actual_days)

        price_delta = await _get_price_delta(rule, db, store_id, avg_revenue)
        if price_delta <= 0:
            continue

        monthly_impact = float(price_delta) * monthly_volume * rule.conversion_rate_default
        priority = _get_priority(monthly_impact, rule)

        opportunity = UpsellOpportunity(
            store_id=store_id,
            rule_id=rule.rule_id,
            opportunity_type=rule.opportunity_type,
            trigger_service=rule.trigger_category,
            trigger_category=rule.trigger_category,
            recommended_service=rule.recommended_service,
            recommended_service_code=rule.recommended_service_code,
            price_delta=price_delta,
            conversion_rate_est=Decimal(str(rule.conversion_rate_default)),
            monthly_volume=monthly_volume,
            monthly_impact_est=Decimal(str(round(monthly_impact, 2))),
            priority=priority,
            staff_script=rule.staff_script,
            analysis_date=analysis_date,
        )
        db.add(opportunity)
        opportunities_written += 1

    await db.flush()
    return opportunities_written
