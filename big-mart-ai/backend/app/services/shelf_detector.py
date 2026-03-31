"""Retail shelf detection service — dual-model architecture.

Two models work together:
 1. **Retail Shelf model** (foduucom/product-detection-in-shelf-yolov8):
    Detects products and empty shelf spaces with high precision (0.91 mAP).
    Classes: 'product', 'empty'.
 2. **COCO model** (pre-trained YOLOv8m): Classifies the content of each
    detected product region into categories (bottle, banana, etc.).

Pipeline:
  Image → preprocess → Retail model detect products/empty →
  for each product crop → COCO classify → merge → post-NMS → output.

Falls back to COCO-only mode when the retail model is unavailable.
"""

import io
import logging
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

logger = logging.getLogger(__name__)

# ── COCO class → retail product category mapping ──────────────────────
COCO_TO_CATEGORY: dict[str, str] = {
    "bottle": "Beverages",
    "wine glass": "Beverages",
    "cup": "Beverages",
    "bowl": "Dairy",
    "banana": "Produce",
    "apple": "Produce",
    "orange": "Produce",
    "sandwich": "Snacks",
    "broccoli": "Produce",
    "carrot": "Produce",
    "cake": "Bakery",
    "donut": "Bakery",
    "pizza": "Frozen",
    "hot dog": "Snacks",
    "vase": "Household",
    "potted plant": "Produce",
    "book": "Household",
    "cell phone": "Personal Care",
    "toothbrush": "Personal Care",
    "scissors": "Household",
    "clock": "Household",
    "remote": "Household",
    "refrigerator": "Household",
    "microwave": "Household",
    "oven": "Household",
    "toaster": "Household",
}

# Per-class minimum confidence
CLASS_CONF_FLOOR: dict[str, float] = {
    "bottle": 0.30,
    "cup": 0.40,
    "wine glass": 0.40,
    "bowl": 0.45,
    "vase": 0.50,
    "potted plant": 0.45,
    "clock": 0.50,
    "remote": 0.50,
    "cell phone": 0.50,
}

# Classes to ignore (not retail products)
IGNORE_CLASSES = {
    "person", "bicycle", "car", "motorcycle", "airplane", "bus",
    "train", "truck", "boat", "traffic light", "fire hydrant",
    "stop sign", "parking meter", "bench", "bird", "cat", "dog",
    "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe",
    "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat",
    "baseball glove", "skateboard", "surfboard", "tennis racket",
    "chair", "couch", "bed", "dining table", "toilet", "tv",
    "laptop", "mouse", "keyboard", "sink", "teddy bear",
    "hair drier", "fork", "knife", "spoon",
}

# ── Model singletons ─────────────────────────────────────────────────
_retail_model = None   # Retail shelf detector (product + empty)
_coco_model = None     # COCO pre-trained (product classifier)


def _get_retail_model():
    """Load the retail shelf detection model."""
    global _retail_model
    if _retail_model is None:
        try:
            from ultralytics import YOLO
            from app.core.config import get_settings
            settings = get_settings()
            model_path = Path(settings.RETAIL_SHELF_MODEL_PATH)
            if model_path.exists():
                _retail_model = YOLO(str(model_path))
                logger.info("Retail shelf model loaded: %s", model_path)
            else:
                logger.info("Retail shelf model not found at %s, using COCO-only mode", model_path)
                _retail_model = "unavailable"
        except Exception as e:
            logger.warning("Could not load retail shelf model: %s", e)
            _retail_model = "unavailable"
    return _retail_model


def _get_coco_model():
    """Load the COCO pre-trained model."""
    global _coco_model
    if _coco_model is None:
        try:
            from ultralytics import YOLO
            from app.core.config import get_settings
            settings = get_settings()
            _coco_model = YOLO(settings.YOLO_MODEL_PATH)
            logger.info("COCO model loaded: %s", settings.YOLO_MODEL_PATH)
        except Exception as e:
            logger.warning("Could not load COCO model: %s", e)
            _coco_model = "unavailable"
    return _coco_model


# ── Image preprocessing ───────────────────────────────────────────────

def _preprocess(img: Image.Image) -> Image.Image:
    """Enhance shelf images before inference."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    img = ImageOps.autocontrast(img, cutoff=1)
    img = ImageEnhance.Sharpness(img).enhance(1.4)
    return img


def _load_image(source: str | bytes | Path) -> Image.Image:
    """Load an image from bytes, local path, or URL."""
    if isinstance(source, bytes):
        return Image.open(io.BytesIO(source))

    source_str = str(source)

    if Path(source_str).exists():
        return Image.open(source_str)

    if source_str.startswith(("http://", "https://")):
        import httpx
        resp = httpx.get(source_str, follow_redirects=True, timeout=20)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content))

    raise FileNotFoundError(f"Cannot load image from: {source_str}")


# ── Post-processing ──────────────────────────────────────────────────

def _iou(a: dict, b: dict) -> float:
    """Compute IoU between two bounding-box dicts."""
    xa = max(a["x1"], b["x1"])
    ya = max(a["y1"], b["y1"])
    xb = min(a["x2"], b["x2"])
    yb = min(a["y2"], b["y2"])
    inter = max(0, xb - xa) * max(0, yb - ya)
    if inter == 0:
        return 0.0
    area_a = (a["x2"] - a["x1"]) * (a["y2"] - a["y1"])
    area_b = (b["x2"] - b["x1"]) * (b["y2"] - b["y1"])
    return inter / (area_a + area_b - inter)


def _nms_dedup(detections: list[dict], iou_thresh: float = 0.45) -> list[dict]:
    """Remove near-duplicate overlapping boxes."""
    if len(detections) <= 1:
        return detections
    dets = sorted(detections, key=lambda d: d["confidence"], reverse=True)
    keep: list[dict] = []
    for det in dets:
        box = det["bounding_box"]
        if all(_iou(box, k["bounding_box"]) < iou_thresh for k in keep):
            keep.append(det)
    return keep


def _filter_tiny_boxes(
    detections: list[dict], img_w: int, img_h: int, min_frac: float = 0.0005
) -> list[dict]:
    """Drop detections whose area is negligible."""
    image_area = img_w * img_h
    min_area = image_area * min_frac
    return [
        d for d in detections
        if (d["bounding_box"]["x2"] - d["bounding_box"]["x1"])
         * (d["bounding_box"]["y2"] - d["bounding_box"]["y1"]) >= min_area
    ]


def _shelf_position(y1: float, y2: float, img_h: int) -> str:
    center_y = (y1 + y2) / 2
    if center_y < img_h * 0.33:
        return "top"
    if center_y < img_h * 0.66:
        return "middle"
    return "bottom"


# ── Classify a crop using COCO model ─────────────────────────────────

def _classify_crop(
    img: Image.Image,
    box: dict,
    coco_model,
    conf_threshold: float = 0.25,
) -> tuple[str, str, float]:
    """Run COCO model on a crop to get class_label + category."""
    img_w, img_h = img.size
    pad_x = (box["x2"] - box["x1"]) * 0.10
    pad_y = (box["y2"] - box["y1"]) * 0.10
    cx1 = max(0, int(box["x1"] - pad_x))
    cy1 = max(0, int(box["y1"] - pad_y))
    cx2 = min(img_w, int(box["x2"] + pad_x))
    cy2 = min(img_h, int(box["y2"] + pad_y))

    crop = img.crop((cx1, cy1, cx2, cy2))
    cw, ch = crop.size
    if cw < 32 or ch < 32:
        return "product", "Other", 0.0

    results = coco_model(crop, conf=conf_threshold, imgsz=320, verbose=False)

    best_label, best_cat, best_conf = "product", "Other", 0.0
    for result in results:
        for rbox in result.boxes:
            cls_name = coco_model.names[int(rbox.cls[0])]
            conf = float(rbox.conf[0])
            if cls_name in IGNORE_CLASSES:
                continue
            floor = CLASS_CONF_FLOOR.get(cls_name, conf_threshold)
            if conf < floor:
                continue
            if conf > best_conf:
                best_label = cls_name
                best_cat = COCO_TO_CATEGORY.get(cls_name, "Other")
                best_conf = conf

    return best_label, best_cat, best_conf


# ── COCO-only fallback ───────────────────────────────────────────────

def _detect_coco_only(
    img: Image.Image,
    confidence_threshold: float,
) -> tuple[list[dict], int]:
    """Run COCO model on full image (fallback). Returns (detections, empty_count)."""
    from app.core.config import get_settings
    settings = get_settings()

    coco_model = _get_coco_model()
    if coco_model == "unavailable":
        raise RuntimeError("No YOLO model could be loaded")

    img_w, img_h = img.size

    results = coco_model(
        img,
        conf=confidence_threshold,
        iou=settings.YOLO_IOU_THRESHOLD,
        imgsz=settings.YOLO_IMG_SIZE,
        augment=True,
        verbose=False,
    )

    raw: list[dict] = []
    for result in results:
        for box in result.boxes:
            cls_name = coco_model.names[int(box.cls[0])]
            if cls_name in IGNORE_CLASSES:
                continue
            conf = float(box.conf[0])
            floor = CLASS_CONF_FLOOR.get(cls_name, confidence_threshold)
            if conf < floor:
                continue
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            raw.append({
                "class_label": cls_name,
                "category": COCO_TO_CATEGORY.get(cls_name, "Other"),
                "bounding_box": {
                    "x1": round(x1, 1), "y1": round(y1, 1),
                    "x2": round(x2, 1), "y2": round(y2, 1),
                },
                "confidence": round(conf, 3),
                "position_on_shelf": _shelf_position(y1, y2, img_h),
            })
    return raw, 0  # no empty shelf detection in COCO-only mode


# ── Dual-model detection ─────────────────────────────────────────────

def _detect_dual(
    img: Image.Image,
    confidence_threshold: float,
) -> tuple[list[dict], int]:
    """Retail model detects products/empty → COCO classifies each product crop.
    Returns (product_detections, empty_shelf_count).
    """
    from app.core.config import get_settings
    settings = get_settings()

    retail_model = _get_retail_model()
    coco_model = _get_coco_model()

    img_w, img_h = img.size

    # Step 1: Retail shelf model — find products and empty spaces
    results = retail_model(
        img,
        conf=confidence_threshold,
        iou=0.45,
        imgsz=settings.YOLO_IMG_SIZE,
        augment=True,
        verbose=False,
        max_det=1000,
    )

    detections: list[dict] = []
    empty_count = 0

    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            cls_name = retail_model.names[cls_id]
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            det_conf = float(box.conf[0])

            if cls_name == "empty":
                empty_count += 1
                continue

            # It's a product — classify with COCO
            bb = {
                "x1": round(x1, 1), "y1": round(y1, 1),
                "x2": round(x2, 1), "y2": round(y2, 1),
            }

            if coco_model != "unavailable":
                cls_label, category, cls_conf = _classify_crop(
                    img, bb, coco_model, conf_threshold=0.20
                )
                combined_conf = max(det_conf, cls_conf) if cls_conf > 0 else det_conf
            else:
                cls_label, category, combined_conf = "product", "Other", det_conf

            detections.append({
                "class_label": cls_label,
                "category": category,
                "bounding_box": bb,
                "confidence": round(combined_conf, 3),
                "position_on_shelf": _shelf_position(y1, y2, img_h),
            })

    return detections, empty_count


# ── Public API ────────────────────────────────────────────────────────

def detect_products(
    image_source: str | bytes | Path,
    confidence_threshold: float = 0.20,
) -> dict:
    """Run detection on a shelf image.

    Uses retail shelf model + COCO classifier when available,
    otherwise COCO-only fallback.

    Returns dict with detections, occupancy, counts, dimensions.
    """
    img = _load_image(image_source)
    img = _preprocess(img)
    img_w, img_h = img.size
    image_area = img_w * img_h

    retail_model = _get_retail_model()
    if retail_model != "unavailable":
        raw_detections, empty_count = _detect_dual(img, confidence_threshold)
        logger.info("Dual-model detection: %d products, %d empty spaces", len(raw_detections), empty_count)
    else:
        raw_detections, empty_count = _detect_coco_only(img, confidence_threshold)
        logger.info("COCO-only detection: %d items found", len(raw_detections))

    # Post-process
    detections = _nms_dedup(raw_detections, iou_thresh=0.45)
    detections = _filter_tiny_boxes(detections, img_w, img_h)

    total_area = sum(
        (d["bounding_box"]["x2"] - d["bounding_box"]["x1"])
        * (d["bounding_box"]["y2"] - d["bounding_box"]["y1"])
        for d in detections
    )
    occupancy = min((total_area / image_area * 100) if image_area else 0, 100)

    return {
        "detections": detections,
        "total_count": len(detections),
        "empty_spots": empty_count,
        "shelf_occupancy": round(occupancy, 1),
        "image_width": img_w,
        "image_height": img_h,
    }
