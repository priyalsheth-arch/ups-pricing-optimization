from sqlalchemy import Integer, String, DateTime, Date, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UploadBatch(Base):
    __tablename__ = "upload_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(Integer, ForeignKey("stores.id"), nullable=False)
    uploaded_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column(String, nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending|processing|complete|error
    error_message: Mapped[str | None] = mapped_column(String)
    date_range_start: Mapped[Date | None] = mapped_column(Date)
    date_range_end: Mapped[Date | None] = mapped_column(Date)
    uploaded_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    store: Mapped["Store"] = relationship(back_populates="upload_batches")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="upload_batch")
