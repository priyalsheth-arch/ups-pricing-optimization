from sqlalchemy import Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    store_number: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    address: Mapped[str | None] = mapped_column(String)
    city: Mapped[str | None] = mapped_column(String)
    state: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="store")
    upload_batches: Mapped[list["UploadBatch"]] = relationship(back_populates="store")
    our_prices: Mapped[list["OurPrice"]] = relationship(back_populates="store")
    pricing_gaps: Mapped[list["PricingGap"]] = relationship(back_populates="store")
    upsell_opportunities: Mapped[list["UpsellOpportunity"]] = relationship(back_populates="store")
