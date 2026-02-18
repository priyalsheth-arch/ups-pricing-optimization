from sqlalchemy import Integer, String, DateTime, Date, Time, Numeric, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import decimal


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_txn_store_date_service", "store_id", "transaction_date", "service_category"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(Integer, ForeignKey("stores.id"), nullable=False)
    upload_batch_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("upload_batches.id"))
    connectsuite_txn_id: Mapped[str | None] = mapped_column(String)
    transaction_date: Mapped[Date] = mapped_column(Date, nullable=False)
    transaction_time: Mapped[str | None] = mapped_column(String)
    service_category: Mapped[str] = mapped_column(String, nullable=False)  # shipping|printing|mailbox|packing|supplies
    service_code: Mapped[str | None] = mapped_column(String)
    service_description: Mapped[str | None] = mapped_column(String)
    quantity: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 3))
    unit_price: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 4))
    extended_price: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 4))
    discount_amount: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 4), default=0)
    net_revenue: Mapped[decimal.Decimal | None] = mapped_column(Numeric(10, 4))
    carrier: Mapped[str | None] = mapped_column(String)
    service_level: Mapped[str | None] = mapped_column(String)
    weight_lbs: Mapped[decimal.Decimal | None] = mapped_column(Numeric(8, 3))
    zone: Mapped[int | None] = mapped_column(Integer)
    destination_state: Mapped[str | None] = mapped_column(String)
    customer_ref: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    store: Mapped["Store"] = relationship(back_populates="transactions")
    upload_batch: Mapped["UploadBatch | None"] = relationship(back_populates="transactions")
