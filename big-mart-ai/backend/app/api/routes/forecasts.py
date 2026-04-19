from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
import csv
import io

from app.core.database import get_db
from app.models.sales_record import SalesRecord
from app.models.product import Product
from app.models.forecast import Forecast
from app.schemas.forecast import ForecastOut, ForecastSummary, ForecastRunResult
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.services.forecaster import run_batch_forecasts

router = APIRouter(prefix="/forecasts", tags=["forecasts"])


@router.post("/run", response_model=ForecastRunResult)
def trigger_forecasts(
    store_id: str = Query("store-1"),
    periods: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    _user: User = Depends(require_admin),
):
    result = run_batch_forecasts(db, store_id, periods)
    return ForecastRunResult(**result)


@router.get("/{sku}", response_model=list[ForecastOut])
def get_forecasts(
    sku: str,
    store_id: str = Query("store-1"),
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.sku == sku).first()
    if not product:
        return []

    today = date.today()
    return (
        db.query(Forecast)
        .filter(
            Forecast.product_id == product.id,
            Forecast.store_id == store_id,
            Forecast.forecast_date >= today,
            Forecast.forecast_date <= today + timedelta(days=days),
        )
        .order_by(Forecast.forecast_date)
        .all()
    )


@router.get("/summary/all", response_model=list[ForecastSummary])
def forecast_summaries(
    store_id: str = Query("store-1"),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    products = db.query(Product).filter(Product.is_active.is_(True)).all()
    today = date.today()
    summaries = []

    for product in products:
        # Average daily sales (last 30 days)
        avg_sales = (
            db.query(func.avg(SalesRecord.quantity_sold))
            .filter(
                SalesRecord.product_id == product.id,
                SalesRecord.store_id == store_id,
                SalesRecord.date >= today - timedelta(days=30),
            )
            .scalar()
        )
        avg_sales = float(avg_sales) if avg_sales is not None else 0.0

        # Tomorrow's prediction
        tomorrow_fc = (
            db.query(Forecast)
            .filter(
                Forecast.product_id == product.id,
                Forecast.store_id == store_id,
                Forecast.forecast_date == today + timedelta(days=1),
            )
            .first()
        )

        # Next 7 days total
        week_total = (
            db.query(func.sum(Forecast.predicted_demand))
            .filter(
                Forecast.product_id == product.id,
                Forecast.store_id == store_id,
                Forecast.forecast_date >= today,
                Forecast.forecast_date <= today + timedelta(days=7),
            )
            .scalar()
        )
        week_total = float(week_total) if week_total is not None else 0.0

        predicted_tomorrow = (
            float(tomorrow_fc.predicted_demand)
            if tomorrow_fc and tomorrow_fc.predicted_demand is not None
            else 0.0
        )

        # Trend: compare predicted tomorrow vs average
        if avg_sales > 0:
            ratio = predicted_tomorrow / avg_sales
            trend = "up" if ratio > 1.1 else "down" if ratio < 0.9 else "stable"
        else:
            trend = "stable"

        summaries.append(
            ForecastSummary(
                product_id=product.id,
                sku=product.sku,
                product_name=product.name,
                category=product.category,
                avg_daily_sales=round(avg_sales, 1),
                predicted_tomorrow=round(predicted_tomorrow, 1),
                predicted_next_week=round(week_total, 1),
                trend=trend,
            )
        )

    return summaries


@router.post("/sales/upload")
async def upload_sales_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _user: User = Depends(require_admin),
):
    """Upload CSV with columns: date, sku, store_id, quantity_sold, revenue"""
    contents = await file.read()
    decoded = contents.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))

    inserted = 0
    skipped = 0
    for row in reader:
        sku = row.get("sku", "").strip()
        product = db.query(Product).filter(Product.sku == sku).first()
        if not product:
            skipped += 1
            continue

        record = SalesRecord(
            product_id=product.id,
            store_id=row.get("store_id", "store-1").strip(),
            date=date.fromisoformat(row["date"].strip()),
            quantity_sold=int(row.get("quantity_sold", 0)),
            revenue=float(row.get("revenue", 0)),
        )
        db.add(record)
        inserted += 1

    db.commit()
    return {"inserted": inserted, "skipped": skipped}
