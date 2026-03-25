from sqlalchemy import Integer, Float, String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class DetectionResult(Base):
    __tablename__ = "detection_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("shelf_images.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=True)
    class_label: Mapped[str] = mapped_column(String(100), nullable=False)
    bounding_box: Mapped[dict] = mapped_column(JSON, nullable=False)  # {x1, y1, x2, y2}
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    shelf_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    position_on_shelf: Mapped[str] = mapped_column(String(50), nullable=True)  # top/middle/bottom

    image = relationship("ShelfImage", back_populates="detections")
