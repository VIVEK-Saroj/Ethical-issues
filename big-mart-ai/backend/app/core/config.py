from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Big Mart AI"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/bigmart"

    # JWT
    JWT_SECRET: str = "change-me-in-production-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # YOLO
    YOLO_MODEL_PATH: str = "yolov8m.pt"
    SKU_MODEL_PATH: str = "runs/sku110k/yolov8m_sku110k/weights/best.pt"
    YOLO_CONFIDENCE_THRESHOLD: float = 0.3
    YOLO_IMG_SIZE: int = 1280
    YOLO_IOU_THRESHOLD: float = 0.5

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:5176,http://localhost:3000"

    # Frontend URL (for production CORS)
    FRONTEND_URL: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def cors_origins_list(self) -> list[str]:
        origins = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        if self.FRONTEND_URL:
            origins.append(self.FRONTEND_URL.rstrip("/"))
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
