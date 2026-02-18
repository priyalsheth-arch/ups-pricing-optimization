import json
from sqlalchemy import Integer, String, DateTime, Date, Numeric, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import decimal


class ServiceTaxonomy(Base):
    __tablename__ = "service_taxonomy"

    service_code: Mapped[str] = mapped_column(String, primary_key=True)
    service_category: Mapped[str] = mapped_column(String, nullable=False)
    service_name: Mapped[str] = mapped_column(String, nullable=False)
    unit: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String)
    connectsuite_codes: Mapped[str | None] = mapped_column(String)  # JSON array


class OurPrice(Base):
    __tablename__ = "our_prices"
    __table_args__ = (
        UniqueConstraint("store_id", "service_code", "effective_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(Integer, ForeignKey("stores.id"), nullable=False)
    service_code: Mapped[str] = mapped_column(String, nullable=False)
    service_category: Mapped[str] = mapped_column(String, nullable=False)
    service_name: Mapped[str] = mapped_column(String, nullable=False)
    unit: Mapped[str | None] = mapped_column(String)
    price: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    effective_date: Mapped[Date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(String)
    updated_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    store: Mapped["Store"] = relationship(back_populates="our_prices")


class CompetitorPrice(Base):
    __tablename__ = "competitor_prices"
    __table_args__ = (
        UniqueConstraint("competitor_name", "service_code", "effective_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    competitor_name: Mapped[str] = mapped_column(String, nullable=False)
    service_code: Mapped[str] = mapped_column(String, nullable=False)
    service_category: Mapped[str] = mapped_column(String, nullable=False)
    service_name: Mapped[str] = mapped_column(String, nullable=False)
    unit: Mapped[str | None] = mapped_column(String)
    price: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    effective_date: Mapped[Date] = mapped_column(Date, nullable=False)
    source_notes: Mapped[str | None] = mapped_column(String)
    entered_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class PricingGap(Base):
    __tablename__ = "pricing_gaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(Integer, ForeignKey("stores.id"), nullable=False)
    service_code: Mapped[str] = mapped_column(String, nullable=False)
    service_category: Mapped[str] = mapped_column(String, nullable=False)
    service_name: Mapped[str | None] = mapped_column(String)
    our_price: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 4))
    competitor_name: Mapped[str] = mapped_column(String, nullable=False)
    competitor_price: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 4))
    gap_amount: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 4))
    gap_pct: Mapped[decimal.Decimal | None] = mapped_column(Numeric(6, 4))
    direction: Mapped[str | None] = mapped_column(String)  # underpriced|overpriced|competitive
    transaction_volume: Mapped[int | None] = mapped_column(Integer)
    revenue_impact: Mapped[decimal.Decimal | None] = mapped_column(Numeric(12, 4))
    analysis_date: Mapped[Date] = mapped_column(Date, nullable=False)
    period_start: Mapped[Date | None] = mapped_column(Date)
    period_end: Mapped[Date | None] = mapped_column(Date)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    store: Mapped["Store"] = relationship(back_populates="pricing_gaps")
