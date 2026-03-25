from pydantic import BaseModel
from datetime import datetime


class ImageUploadOut(BaseModel):
    id: int
    store_id: str
    aisle: str
    image_url: str
    processing_status: str
    upload_timestamp: datetime

    model_config = {"from_attributes": True}


class ShelfImageOut(BaseModel):
    id: int
    store_id: str
    aisle: str
    uploaded_by: int
    image_url: str
    processing_status: str
    total_detections: int
    shelf_occupancy: float
    upload_timestamp: datetime

    model_config = {"from_attributes": True}
