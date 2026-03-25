from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ShelfImage(Base):
    __tablename__ = "shelf_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    aisle: Mapped[str] = mapped_column(String(50), nullable=False)
    uploaded_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    cloudinary_public_id: Mapped[str] = mapped_column(String(200), nullable=True)
    processing_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending | processing | done | failed
    total_detections: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shelf_occupancy: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    upload_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    detections = relationship("DetectionResult", back_populates="image", cascade="all, delete-orphan")
