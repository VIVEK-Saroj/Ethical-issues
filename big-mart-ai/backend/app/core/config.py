from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Big Mart AI"
    DEBUG: bool = False

    # Database — defaults to local SQLite for dev; set to Supabase PostgreSQL URL in production
    DATABASE_URL: str = "sqlite:///./bigmart.db"

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
    RETAIL_SHELF_MODEL_PATH: str = "retail_shelf_detector.pt"
    YOLO_CONFIDENCE_THRESHOLD: float = 0.25
    YOLO_IMG_SIZE: int = 1280
    YOLO_IOU_THRESHOLD: float = 0.45

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
