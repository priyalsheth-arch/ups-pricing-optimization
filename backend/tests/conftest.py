"""Shared fixtures for all backend tests."""

import pytest_asyncio
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base

# Import all models so Base.metadata has all tables
import app.models.store       # noqa: F401
import app.models.user        # noqa: F401
import app.models.upload      # noqa: F401
import app.models.transaction # noqa: F401
import app.models.pricing     # noqa: F401
import app.models.analysis    # noqa: F401

from app.models.store import Store
from app.models.pricing import OurPrice, CompetitorPrice, ServiceTaxonomy
from app.models.transaction import Transaction


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    """In-memory SQLite session with all tables created."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def seeded_db(db_session: AsyncSession):
    """Session pre-seeded with store, taxonomy, our prices, and competitor prices."""
    store = Store(
        id=1,
        store_number="4521",
        name="UPS Store #4521",
        address="123 Main St",
        city="Atlanta",
        state="GA",
    )
    db_session.add(store)

    taxonomy_entries = [
        ServiceTaxonomy(service_code="UPS_GROUND", service_name="UPS Ground", service_category="shipping"),
        ServiceTaxonomy(service_code="UPS_2DAY", service_name="UPS 2-Day Air", service_category="shipping"),
        ServiceTaxonomy(service_code="UPS_3DAY", service_name="UPS 3 Day Select", service_category="shipping"),
        ServiceTaxonomy(service_code="UPS_OVERNIGHT", service_name="UPS Next Day Air", service_category="shipping"),
        ServiceTaxonomy(service_code="BW_COPY", service_name="B&W Copies", service_category="printing"),
        ServiceTaxonomy(service_code="COLOR_COPY", service_name="Color Copies", service_category="printing"),
        ServiceTaxonomy(service_code="PACK_SVC", service_name="Professional Packing", service_category="packing"),
        ServiceTaxonomy(service_code="MB_BASIC", service_name="Mailbox Rental Basic", service_category="mailbox"),
    ]
    db_session.add_all(taxonomy_entries)

    today = date.today()
    our_prices = [
        OurPrice(store_id=1, service_code="UPS_GROUND", service_category="shipping",
                 service_name="UPS Ground", price=Decimal("12.50"), effective_date=today),
        OurPrice(store_id=1, service_code="UPS_2DAY", service_category="shipping",
                 service_name="UPS 2-Day Air", price=Decimal("22.50"), effective_date=today),
        OurPrice(store_id=1, service_code="UPS_3DAY", service_category="shipping",
                 service_name="UPS 3 Day Select", price=Decimal("16.00"), effective_date=today),
        OurPrice(store_id=1, service_code="UPS_OVERNIGHT", service_category="shipping",
                 service_name="UPS Next Day Air", price=Decimal("45.00"), effective_date=today),
        OurPrice(store_id=1, service_code="BW_COPY", service_category="printing",
                 service_name="B&W Copies", price=Decimal("0.15"), effective_date=today),
        OurPrice(store_id=1, service_code="COLOR_COPY", service_category="printing",
                 service_name="Color Copies", price=Decimal("0.49"), effective_date=today),
        OurPrice(store_id=1, service_code="PACK_SVC", service_category="packing",
                 service_name="Professional Packing", price=Decimal("15.00"), effective_date=today),
        OurPrice(store_id=1, service_code="MB_BASIC", service_category="mailbox",
                 service_name="Mailbox Rental Basic", price=Decimal("25.00"), effective_date=today),
    ]
    db_session.add_all(our_prices)

    competitor_prices = [
        CompetitorPrice(service_code="UPS_GROUND", service_category="shipping", service_name="UPS Ground",
                        competitor_name="FedEx", price=Decimal("14.00"), effective_date=today),
        CompetitorPrice(service_code="UPS_GROUND", service_category="shipping", service_name="UPS Ground",
                        competitor_name="USPS", price=Decimal("11.50"), effective_date=today),
        CompetitorPrice(service_code="UPS_2DAY", service_category="shipping", service_name="UPS 2-Day Air",
                        competitor_name="FedEx", price=Decimal("25.00"), effective_date=today),
        CompetitorPrice(service_code="BW_COPY", service_category="printing", service_name="B&W Copies",
                        competitor_name="Staples", price=Decimal("0.18"), effective_date=today),
        CompetitorPrice(service_code="COLOR_COPY", service_category="printing", service_name="Color Copies",
                        competitor_name="Staples", price=Decimal("0.55"), effective_date=today),
    ]
    db_session.add_all(competitor_prices)

    await db_session.flush()
    return db_session


def make_transaction(store_id=1, batch_id=None, **kwargs) -> Transaction:
    """Helper to create a Transaction with sensible defaults."""
    defaults = dict(
        store_id=store_id,
        upload_batch_id=batch_id,
        connectsuite_txn_id=None,
        transaction_date=date.today() - timedelta(days=5),
        service_category="shipping",
        service_code="UPS_GROUND",
        service_description="UPS Ground Shipping",
        quantity=Decimal("1"),
        unit_price=Decimal("12.50"),
        net_revenue=Decimal("12.50"),
        discount_amount=Decimal("0"),
        service_level="ground",
        weight_lbs=Decimal("3.0"),
        destination_state="GA",
        carrier="UPS",
        customer_ref=None,
    )
    defaults.update(kwargs)
    return Transaction(**defaults)
