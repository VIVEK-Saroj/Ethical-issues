"""Alerting engine: computes stock-out risk by comparing shelf counts vs predicted demand."""

from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.product import Product
from app.models.detection_result import DetectionResult
from app.models.shelf_image import ShelfImage
from app.models.forecast import Forecast
from app.schemas.dashboard import AlertOut, AlertSummary

SAFETY_BUFFER = 0.2  # 20% extra for safety stock


def compute_stock_risk(
    db: Session, product_id: int, store_id: str
) -> dict:
    """
    Compute stock risk for a single product.
    Compares latest shelf count against 7-day predicted demand.
    """
    # Get latest shelf count from most recent detection
    latest_detection = (
        db.query(func.sum(DetectionResult.shelf_count))
        .join(ShelfImage, DetectionResult.image_id == ShelfImage.id)
        .filter(
            DetectionResult.product_id == product_id,
            ShelfImage.store_id == store_id,
        )
        .scalar()
    ) or 0

    # Get 7-day predicted demand
    today = date.today()
    week_ahead = today + timedelta(days=7)
    predicted_7d = (
        db.query(func.sum(Forecast.predicted_demand))
        .filter(
            Forecast.product_id == product_id,
            Forecast.store_id == store_id,
            Forecast.forecast_date >= today,
            Forecast.forecast_date <= week_ahead,
        )
        .scalar()
    ) or 0

    daily_demand = predicted_7d / 7 if predicted_7d > 0 else 1

    # Risk levels
    if latest_detection < daily_demand:
        risk_level = "critical"
    elif latest_detection < daily_demand * 3:
        risk_level = "warning"
    else:
        risk_level = "ok"

    # Suggested restock quantity
    restock_qty = max(0, int(predicted_7d * (1 + SAFETY_BUFFER) - latest_detection))

    return {
        "shelf_stock": latest_detection,
        "predicted_demand_7d": round(predicted_7d, 1),
        "risk_level": risk_level,
        "restock_qty": restock_qty,
    }


def get_all_alerts(db: Session, store_id: str = "store-1") -> list[AlertOut]:
    """Compute alerts for all active products."""
    products = db.query(Product).filter(Product.is_active.is_(True)).all()
    alerts = []

    for product in products:
        risk = compute_stock_risk(db, product.id, store_id)
        alerts.append(
            AlertOut(
                product_id=product.id,
                sku=product.sku,
                product_name=product.name,
                category=product.category,
                shelf_stock=risk["shelf_stock"],
                predicted_demand_7d=risk["predicted_demand_7d"],
                risk_level=risk["risk_level"],
                restock_qty=risk["restock_qty"],
            )
        )

    # Sort by severity: critical first, then warning, then ok
    severity_order = {"critical": 0, "warning": 1, "ok": 2}
    alerts.sort(key=lambda a: (severity_order.get(a.risk_level, 3), -a.predicted_demand_7d))
    return alerts


def get_alert_summary(db: Session, store_id: str = "store-1") -> AlertSummary:
    """Get counts by risk level."""
    alerts = get_all_alerts(db, store_id)
    critical = sum(1 for a in alerts if a.risk_level == "critical")
    warning = sum(1 for a in alerts if a.risk_level == "warning")
    ok = sum(1 for a in alerts if a.risk_level == "ok")
    return AlertSummary(critical=critical, warning=warning, ok=ok, total=len(alerts))
