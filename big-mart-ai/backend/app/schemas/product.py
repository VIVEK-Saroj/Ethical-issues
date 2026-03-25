from pydantic import BaseModel
from datetime import datetime


class ProductCreate(BaseModel):
    sku: str
    name: str
    category: str
    brand: str = ""
    unit_price: float = 0.0
    image_url: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    brand: str | None = None
    unit_price: float | None = None
    image_url: str | None = None
    is_active: bool | None = None


class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    category: str
    brand: str
    unit_price: float
    image_url: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
