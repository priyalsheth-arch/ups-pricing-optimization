"""Seed initial data: 4 stores, admin user, service taxonomy, sample prices."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import engine, Base, AsyncSessionLocal
from app.models.store import Store
from app.models.user import User
from app.models.pricing import ServiceTaxonomy, OurPrice, CompetitorPrice
from datetime import date
from decimal import Decimal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

STORES = [
    {"name": "UPS Store #4521", "store_number": "4521", "address": "123 Main St", "city": "Atlanta", "state": "GA"},
    {"name": "UPS Store #4522", "store_number": "4522", "address": "456 Peachtree Rd", "city": "Atlanta", "state": "GA"},
    {"name": "UPS Store #4523", "store_number": "4523", "address": "789 Buckhead Ave", "city": "Atlanta", "state": "GA"},
    {"name": "UPS Store #4524", "store_number": "4524", "address": "321 Midtown Blvd", "city": "Atlanta", "state": "GA"},
]

SERVICE_TAXONOMY = [
    # Shipping
    ("UPS_GROUND", "shipping", "UPS Ground", "per_shipment", ["GROUND", "UPS GROUND"]),
    ("UPS_2DAY", "shipping", "UPS 2-Day Air", "per_shipment", ["2DAY", "2ND DAY AIR"]),
    ("UPS_3DAY", "shipping", "UPS 3 Day Select", "per_shipment", ["3 DAY SELECT", "3DAY"]),
    ("UPS_OVERNIGHT", "shipping", "UPS Next Day Air", "per_shipment", ["NEXT DAY AIR", "NDA"]),
    ("DECLARED_VALUE", "shipping", "Declared Value Coverage", "per_shipment", ["DECL VALUE", "INS"]),
    ("SIG_REQUIRED", "shipping", "Signature Required", "per_shipment", ["SIG REQ", "SIGNATURE"]),
    # Printing
    ("BW_COPY", "printing", "Black & White Copies", "per_page", ["BW COPY", "BWCOPY", "BW_PRINT"]),
    ("COLOR_PRINT", "printing", "Color Copies / Print", "per_page", ["COLOR COPY", "CLR COPY"]),
    ("FULLSERVICE_PRINT", "printing", "Full-Service Printing", "per_job", ["FULL SVC", "FS PRINT"]),
    ("BINDING", "printing", "Document Binding", "per_job", ["BINDING", "BIND"]),
    ("LAMINATE", "printing", "Lamination", "per_item", ["LAMINATE", "LAM"]),
    ("SELF_SERVICE_COPY", "printing", "Self-Service Copies", "per_page", ["SELF COPY", "SELF SVC"]),
    # Mailbox
    ("MAILBOX_S", "mailbox", "Mailbox Rental - Small", "per_month", ["MB SMALL", "MAILBOX S"]),
    ("MAILBOX_M", "mailbox", "Mailbox Rental - Medium", "per_month", ["MB MED", "MAILBOX M"]),
    ("MAILBOX_L", "mailbox", "Mailbox Rental - Large", "per_month", ["MB LARGE", "MAILBOX L"]),
    ("MAILBOX_NOTIF", "mailbox", "Package Notification Add-on", "per_month", ["NOTIF", "PKG NOTIFY"]),
    # Packing
    ("PACKING_SVC", "packing", "Professional Packing Service", "per_item", ["PACK SVC", "PACKING"]),
    # Supplies
    ("SUPPLIES_BUNDLE", "supplies", "Packing Supplies Bundle", "per_bundle", ["SUPPLIES", "SUPPLY BUNDLE"]),
    ("BOX_SMALL", "supplies", "Small Box", "each", ["BOX SM", "SMALL BOX"]),
    ("BOX_MEDIUM", "supplies", "Medium Box", "each", ["BOX MED", "MEDIUM BOX"]),
    ("BOX_LARGE", "supplies", "Large Box", "each", ["BOX LG", "LARGE BOX"]),
]

# Default prices for each store (our_prices)
OUR_PRICES_TEMPLATE = [
    ("UPS_GROUND", "shipping", "UPS Ground", "per_shipment", Decimal("12.50")),
    ("UPS_2DAY", "shipping", "UPS 2-Day Air", "per_shipment", Decimal("28.00")),
    ("UPS_3DAY", "shipping", "UPS 3 Day Select", "per_shipment", Decimal("18.50")),
    ("UPS_OVERNIGHT", "shipping", "UPS Next Day Air", "per_shipment", Decimal("45.00")),
    ("DECLARED_VALUE", "shipping", "Declared Value Coverage", "per_shipment", Decimal("3.50")),
    ("SIG_REQUIRED", "shipping", "Signature Required", "per_shipment", Decimal("2.75")),
    ("BW_COPY", "printing", "Black & White Copies", "per_page", Decimal("0.12")),
    ("COLOR_PRINT", "printing", "Color Copies", "per_page", Decimal("0.49")),
    ("FULLSERVICE_PRINT", "printing", "Full-Service Printing", "per_job", Decimal("8.00")),
    ("BINDING", "printing", "Document Binding", "per_job", Decimal("5.00")),
    ("LAMINATE", "printing", "Lamination", "per_item", Decimal("4.00")),
    ("SELF_SERVICE_COPY", "printing", "Self-Service Copies", "per_page", Decimal("0.09")),
    ("MAILBOX_S", "mailbox", "Mailbox - Small", "per_month", Decimal("18.00")),
    ("MAILBOX_M", "mailbox", "Mailbox - Medium", "per_month", Decimal("24.00")),
    ("MAILBOX_L", "mailbox", "Mailbox - Large", "per_month", Decimal("35.00")),
    ("MAILBOX_NOTIF", "mailbox", "Package Notification", "per_month", Decimal("4.00")),
    ("PACKING_SVC", "packing", "Professional Packing", "per_item", Decimal("18.00")),
    ("SUPPLIES_BUNDLE", "supplies", "Packing Supplies Bundle", "per_bundle", Decimal("9.99")),
    ("BOX_SMALL", "supplies", "Small Box", "each", Decimal("2.99")),
    ("BOX_MEDIUM", "supplies", "Medium Box", "each", Decimal("4.99")),
    ("BOX_LARGE", "supplies", "Large Box", "each", Decimal("6.99")),
]

COMPETITOR_PRICES = [
    # FedEx
    ("FedEx", "UPS_GROUND", "shipping", "FedEx Ground", "per_shipment", Decimal("14.00")),
    ("FedEx", "UPS_2DAY", "shipping", "FedEx 2Day", "per_shipment", Decimal("32.00")),
    ("FedEx", "UPS_3DAY", "shipping", "FedEx Express Saver", "per_shipment", Decimal("22.00")),
    ("FedEx", "UPS_OVERNIGHT", "shipping", "FedEx Standard Overnight", "per_shipment", Decimal("52.00")),
    # USPS
    ("USPS", "UPS_GROUND", "shipping", "Priority Mail", "per_shipment", Decimal("9.65")),
    ("USPS", "UPS_2DAY", "shipping", "Priority Mail Express", "per_shipment", Decimal("27.90")),
    # Staples
    ("Staples", "BW_COPY", "printing", "B&W Copies", "per_page", Decimal("0.14")),
    ("Staples", "COLOR_PRINT", "printing", "Color Copies", "per_page", Decimal("0.69")),
    ("Staples", "BINDING", "printing", "Comb Binding", "per_job", Decimal("4.49")),
    # Office Depot
    ("Office Depot", "BW_COPY", "printing", "B&W Copies", "per_page", Decimal("0.13")),
    ("Office Depot", "COLOR_PRINT", "printing", "Color Copies", "per_page", Decimal("0.59")),
    ("Office Depot", "MAILBOX_S", "mailbox", "Small Mailbox", "per_month", Decimal("15.00")),
]

import json


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Stores
        store_ids = []
        for s in STORES:
            from sqlalchemy import select
            existing = await db.execute(select(Store).where(Store.store_number == s["store_number"]))
            store = existing.scalar_one_or_none()
            if not store:
                store = Store(**s)
                db.add(store)
                await db.flush()
            store_ids.append(store.id)

        # Admin user
        from sqlalchemy import select
        existing_user = await db.execute(select(User).where(User.email == "admin@upsstore.com"))
        if not existing_user.scalar_one_or_none():
            admin = User(
                email="admin@upsstore.com",
                hashed_password=pwd_context.hash("admin123"),
                full_name="Store Admin",
                role="admin",
                store_id=None,
            )
            db.add(admin)

        # Manager user (store 1)
        existing_mgr = await db.execute(select(User).where(User.email == "manager@upsstore.com"))
        if not existing_mgr.scalar_one_or_none():
            mgr = User(
                email="manager@upsstore.com",
                hashed_password=pwd_context.hash("manager123"),
                full_name="Store Manager",
                role="manager",
                store_id=store_ids[0],
            )
            db.add(mgr)

        # Staff user (store 1)
        existing_staff = await db.execute(select(User).where(User.email == "staff@upsstore.com"))
        if not existing_staff.scalar_one_or_none():
            staff = User(
                email="staff@upsstore.com",
                hashed_password=pwd_context.hash("staff123"),
                full_name="Counter Staff",
                role="staff",
                store_id=store_ids[0],
            )
            db.add(staff)

        # Service taxonomy
        for code, cat, name, unit, cs_codes in SERVICE_TAXONOMY:
            existing_tax = await db.execute(
                select(ServiceTaxonomy).where(ServiceTaxonomy.service_code == code)
            )
            if not existing_tax.scalar_one_or_none():
                t = ServiceTaxonomy(
                    service_code=code,
                    service_category=cat,
                    service_name=name,
                    unit=unit,
                    connectsuite_codes=json.dumps(cs_codes),
                )
                db.add(t)

        # Our prices for each store
        today = date.today()
        for store_id in store_ids:
            for code, cat, name, unit, price in OUR_PRICES_TEMPLATE:
                existing_price = await db.execute(
                    select(OurPrice).where(
                        OurPrice.store_id == store_id,
                        OurPrice.service_code == code,
                        OurPrice.effective_date == today,
                    )
                )
                if not existing_price.scalar_one_or_none():
                    op = OurPrice(
                        store_id=store_id,
                        service_code=code,
                        service_category=cat,
                        service_name=name,
                        unit=unit,
                        price=price,
                        effective_date=today,
                    )
                    db.add(op)

        # Competitor prices
        for comp, code, cat, name, unit, price in COMPETITOR_PRICES:
            existing_cp = await db.execute(
                select(CompetitorPrice).where(
                    CompetitorPrice.competitor_name == comp,
                    CompetitorPrice.service_code == code,
                    CompetitorPrice.effective_date == today,
                )
            )
            if not existing_cp.scalar_one_or_none():
                cp = CompetitorPrice(
                    competitor_name=comp,
                    service_code=code,
                    service_category=cat,
                    service_name=name,
                    unit=unit,
                    price=price,
                    effective_date=today,
                    source_notes="Initial seed data",
                )
                db.add(cp)

        await db.commit()
        print("✓ Seed complete:")
        print(f"  {len(STORES)} stores")
        print(f"  3 users (admin / manager / staff)")
        print(f"  {len(SERVICE_TAXONOMY)} service taxonomy entries")
        print(f"  {len(OUR_PRICES_TEMPLATE) * len(store_ids)} our_prices entries")
        print(f"  {len(COMPETITOR_PRICES)} competitor_prices entries")


if __name__ == "__main__":
    asyncio.run(seed())
