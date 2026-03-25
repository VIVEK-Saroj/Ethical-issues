"""YOLOv8 shelf detection service — dual-model architecture.

Two models work together for maximum accuracy:
 1. **SKU-110K model** (fine-tuned): Detects *every* retail item on a shelf
    with high precision, even tightly packed products.  Single class "object".
 2. **COCO model** (pre-trained YOLOv8m): Classifies the content of each
    detected region into product categories (bottle, banana, etc.).

Pipeline:
  Image → preprocess → SKU-110K detect items → for each item crop →
  COCO classify → merge results → post-NMS dedup → output.

Falls back to COCO-only mode when the SKU-110K model is not yet available.
- Test-time augmentation (TTA) for robust multi-scale detection
- Post-processing NMS to remove duplicate / overlapping boxes
- Per-class confidence floors for high-precision retail mapping
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

# Per-class minimum confidence — classes that are easy to confuse get a
# higher floor so only strong detections survive.
CLASS_CONF_FLOOR: dict[str, float] = {
    "bottle": 0.30,
    "cup": 0.40,
    "wine glass": 0.40,
    "bowl": 0.45,
    "vase": 0.50,       # often confused with bottle
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
_sku_model = None   # SKU-110K fine-tuned (retail item detector)
_coco_model = None  # COCO pre-trained (product classifier)


def _get_sku_model():
    """Load the SKU-110K fine-tuned model (if available)."""
    global _sku_model
    if _sku_model is None:
        try:
            from ultralytics import YOLO
            from app.core.config import get_settings
            settings = get_settings()
            sku_path = Path(settings.SKU_MODEL_PATH)
            if sku_path.exists():
                _sku_model = YOLO(str(sku_path))
                logger.info("SKU-110K model loaded: %s", sku_path)
            else:
                logger.info("SKU-110K model not found at %s, using COCO-only mode", sku_path)
                _sku_model = "unavailable"
        except Exception as e:
            logger.warning("Could not load SKU-110K model: %s", e)
            _sku_model = "unavailable"
    return _sku_model


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
    """Enhance shelf images before inference for better accuracy.

    1. Auto-contrast — normalize uneven store lighting.
    2. Mild sharpening — bring out product edges on shelves.
    3. Convert to RGB if needed (YOLO requires 3 channels).
    """
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
    """Compute IoU between two bounding-box dicts with x1/y1/x2/y2 keys."""
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
    """Remove near-duplicate overlapping boxes (class-agnostic NMS).

    Keeps the higher-confidence detection when two boxes overlap heavily.
    This catches duplicates the model's built-in NMS may miss — especially
    when TTA produces slightly shifted boxes at different scales.
    """
    if len(detections) <= 1:
        return detections

    # Sort by confidence descending
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
    """Run COCO model on a crop to get class_label + category.

    Returns (class_label, category, confidence).
    Falls back to ("object", "Other", 0) when COCO finds nothing.
    """
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
        return "object", "Other", 0.0

    results = coco_model(crop, conf=conf_threshold, imgsz=320, verbose=False)

    best_label, best_cat, best_conf = "object", "Other", 0.0
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
) -> list[dict]:
    """Run COCO model on full image (fallback when SKU model unavailable)."""
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
    return raw


# ── Dual-model detection ─────────────────────────────────────────────

def _detect_dual(
    img: Image.Image,
    confidence_threshold: float,
) -> list[dict]:
    """SKU-110K detects items → COCO classifies each crop."""
    from app.core.config import get_settings
    settings = get_settings()

    sku_model = _get_sku_model()
    coco_model = _get_coco_model()

    img_w, img_h = img.size

    # Step 1: SKU-110K — find every retail item on the shelf
    sku_results = sku_model(
        img,
        conf=confidence_threshold,
        iou=0.4,
        imgsz=settings.YOLO_IMG_SIZE,
        augment=True,
        verbose=False,
    )

    detections: list[dict] = []
    for result in sku_results:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            sku_conf = float(box.conf[0])

            bb = {
                "x1": round(x1, 1), "y1": round(y1, 1),
                "x2": round(x2, 1), "y2": round(y2, 1),
            }

            # Step 2: COCO classify the crop
            if coco_model != "unavailable":
                cls_label, category, cls_conf = _classify_crop(
                    img, bb, coco_model, conf_threshold=0.20
                )
                combined_conf = max(sku_conf, cls_conf) if cls_conf > 0 else sku_conf
            else:
                cls_label, category, combined_conf = "object", "Other", sku_conf

            detections.append({
                "class_label": cls_label,
                "category": category,
                "bounding_box": bb,
                "confidence": round(combined_conf, 3),
                "position_on_shelf": _shelf_position(y1, y2, img_h),
            })

    return detections


# ── Public API ────────────────────────────────────────────────────────

def detect_products(
    image_source: str | bytes | Path,
    confidence_threshold: float = 0.20,
) -> dict:
    """Run detection on a shelf image.

    Automatically uses dual-model (SKU-110K + COCO) when the SKU model
    is available, otherwise falls back to COCO-only mode.

    Returns dict with detections, occupancy, counts, dimensions.
    """
    img = _load_image(image_source)
    img = _preprocess(img)
    img_w, img_h = img.size
    image_area = img_w * img_h

    sku_model = _get_sku_model()
    if sku_model != "unavailable":
        raw_detections = _detect_dual(img, confidence_threshold)
        logger.info("Dual-model detection: %d items found", len(raw_detections))
    else:
        raw_detections = _detect_coco_only(img, confidence_threshold)
        logger.info("COCO-only detection: %d items found", len(raw_detections))

    # Post-process: deduplicate + remove noise
    detections = _nms_dedup(raw_detections, iou_thresh=0.45)
    detections = _filter_tiny_boxes(detections, img_w, img_h)

    total_area = sum(
        (d["bounding_box"]["x2"] - d["bounding_box"]["x1"])
        * (d["bounding_box"]["y2"] - d["bounding_box"]["y1"])
        for d in detections
    )
    occupancy = min((total_area / image_area * 100) if image_area else 0, 100)
    empty_spots = max(0, int((100 - occupancy) / 15))

    return {
        "detections": detections,
        "total_count": len(detections),
        "shelf_occupancy": round(occupancy, 1),
        "empty_spots": empty_spots,
        "image_width": img_w,
        "image_height": img_h,
    }
