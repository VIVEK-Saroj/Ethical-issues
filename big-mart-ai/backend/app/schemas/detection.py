from pydantic import BaseModel


class DetectionOut(BaseModel):
    id: int
    image_id: int
    product_id: int | None
    product_name: str | None = None
    class_label: str
    bounding_box: dict
    confidence: float
    shelf_count: int
    position_on_shelf: str | None

    model_config = {"from_attributes": True}


class ImageWithDetections(BaseModel):
    id: int
    store_id: str
    aisle: str
    image_url: str
    processing_status: str
    total_detections: int
    shelf_occupancy: float
    detections: list[DetectionOut]

    model_config = {"from_attributes": True}
