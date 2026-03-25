import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.shelf_image import ShelfImage
from app.models.detection_result import DetectionResult
from app.models.product import Product
from app.schemas.image import ImageUploadOut, ShelfImageOut
from app.schemas.detection import ImageWithDetections, DetectionOut
from app.api.deps import get_current_user
from app.models.user import User
from app.services.image_storage import upload_image, get_local_path
from app.services.shelf_detector import detect_products, COCO_TO_CATEGORY

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/images", tags=["images"])


def _match_product(class_label: str, category: str, db: Session) -> int | None:
    """Find the best matching product in inventory for a COCO detection.

    Strategy: exact category match → name keyword match → None.
    """
    # Try category match first — prefer products whose name hints at the class
    products = (
        db.query(Product)
        .filter(Product.category == category, Product.is_active.is_(True))
        .all()
    )
    if products:
        # Prefer a product whose name contains the COCO class label
        for p in products:
            if class_label.lower() in p.name.lower():
                return p.id
        # Otherwise first match
        return products[0].id
    return None


def _run_analysis(shelf_image: ShelfImage, db: Session) -> dict:
    """Run YOLO on a shelf image, save detections, link to products."""
    shelf_image.processing_status = "processing"
    db.commit()

    try:
        # Determine the image source for YOLO
        local_path = get_local_path(shelf_image.image_url)
        source = local_path or shelf_image.image_url

        result = detect_products(source)

        # Clear old detections
        db.query(DetectionResult).filter(
            DetectionResult.image_id == shelf_image.id
        ).delete()

        for det in result["detections"]:
            product_id = _match_product(
                det["class_label"], det["category"], db
            )
            detection = DetectionResult(
                image_id=shelf_image.id,
                product_id=product_id,
                class_label=det["class_label"],
                bounding_box=det["bounding_box"],
                confidence=det["confidence"],
                shelf_count=1,
                position_on_shelf=det.get("position_on_shelf"),
            )
            db.add(detection)

        shelf_image.processing_status = "done"
        shelf_image.total_detections = result["total_count"]
        shelf_image.shelf_occupancy = result["shelf_occupancy"]
        db.commit()
        db.refresh(shelf_image)
        return result

    except Exception as e:
        logger.error(f"Analysis failed for image {shelf_image.id}: {e}")
        shelf_image.processing_status = "failed"
        db.commit()
        raise


@router.post("/upload", response_model=list[ImageUploadOut], status_code=201)
async def upload_images(
    files: list[UploadFile] = File(...),
    store_id: str = Form("store-1"),
    aisle: str = Form("A1"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    results = []
    for file in files:
        contents = await file.read()
        cloud_result = upload_image(contents)
        shelf_image = ShelfImage(
            store_id=store_id,
            aisle=aisle,
            uploaded_by=user.id,
            image_url=cloud_result["url"],
            cloudinary_public_id=cloud_result["public_id"],
            processing_status="pending",
        )
        db.add(shelf_image)
        db.commit()
        db.refresh(shelf_image)

        # Auto-analyze immediately
        try:
            _run_analysis(shelf_image, db)
        except Exception:
            pass  # status already set to "failed"

        db.refresh(shelf_image)
        results.append(shelf_image)
    return results


@router.post("/{image_id}/analyze", response_model=ImageWithDetections)
def analyze_image(
    image_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    shelf_image = db.query(ShelfImage).filter(ShelfImage.id == image_id).first()
    if not shelf_image:
        raise HTTPException(status_code=404, detail="Image not found")

    try:
        _run_analysis(shelf_image, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    return _build_image_response(shelf_image, db)


@router.get("/", response_model=list[ShelfImageOut])
def list_images(
    store_id: str = Query("", max_length=50),
    status: str = Query("", max_length=20),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    q = db.query(ShelfImage)
    if store_id:
        q = q.filter(ShelfImage.store_id == store_id)
    if status:
        q = q.filter(ShelfImage.processing_status == status)
    return q.order_by(ShelfImage.upload_timestamp.desc()).offset(skip).limit(limit).all()


@router.get("/{image_id}", response_model=ImageWithDetections)
def get_image_detail(
    image_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    shelf_image = db.query(ShelfImage).filter(ShelfImage.id == image_id).first()
    if not shelf_image:
        raise HTTPException(status_code=404, detail="Image not found")
    return _build_image_response(shelf_image, db)


def _build_image_response(shelf_image: ShelfImage, db: Session) -> dict:
    detections = (
        db.query(DetectionResult)
        .filter(DetectionResult.image_id == shelf_image.id)
        .all()
    )

    # Enrich detections with product names
    det_list = []
    for d in detections:
        det_data = DetectionOut.model_validate(d)
        if d.product_id:
            product = db.query(Product).filter(Product.id == d.product_id).first()
            if product:
                det_data.product_name = product.name
        det_list.append(det_data)

    return {
        "id": shelf_image.id,
        "store_id": shelf_image.store_id,
        "aisle": shelf_image.aisle,
        "image_url": shelf_image.image_url,
        "processing_status": shelf_image.processing_status,
        "total_detections": shelf_image.total_detections,
        "shelf_occupancy": shelf_image.shelf_occupancy,
        "detections": det_list,
    }
