from sqlalchemy import Integer, String, DateTime, Date, Numeric, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import decimal


class UpsellOpportunity(Base):
    __tablename__ = "upsell_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(Integer, ForeignKey("stores.id"), nullable=False)
    rule_id: Mapped[str] = mapped_column(String, nullable=False)
    opportunity_type: Mapped[str] = mapped_column(String, nullable=False)  # service_upgrade|addon|cross_sell
    trigger_service: Mapped[str] = mapped_column(String, nullable=False)
    trigger_category: Mapped[str] = mapped_column(String, nullable=False)
    recommended_service: Mapped[str] = mapped_column(String, nullable=False)
    recommended_service_code: Mapped[str] = mapped_column(String, nullable=False)
    price_delta: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 4))
    conversion_rate_est: Mapped[decimal.Decimal | None] = mapped_column(Numeric(5, 4))
    monthly_volume: Mapped[int | None] = mapped_column(Integer)
    monthly_impact_est: Mapped[decimal.Decimal | None] = mapped_column(Numeric(12, 4))
    priority: Mapped[str | None] = mapped_column(String)  # high|medium|low
    staff_script: Mapped[str | None] = mapped_column(String)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    analysis_date: Mapped[Date] = mapped_column(Date, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    store: Mapped["Store"] = relationship(back_populates="upsell_opportunities")
