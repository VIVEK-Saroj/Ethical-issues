"""Prophet-based demand forecasting service.

Trains per-SKU Prophet models on historical POS data and
predicts next 7 days of demand with confidence intervals.
"""

import logging
from datetime import date, timedelta
import pandas as pd
from sqlalchemy.orm import Session
from app.models.sales_record import SalesRecord
from app.models.forecast import Forecast
from app.models.product import Product

logger = logging.getLogger(__name__)


def train_and_forecast(
    db: Session,
    product_id: int,
    store_id: str,
    periods: int = 7,
) -> list[Forecast]:
    """Train Prophet on a single SKU's history and predict `periods` days ahead."""
    rows = (
        db.query(SalesRecord.date, SalesRecord.quantity_sold)
        .filter(SalesRecord.product_id == product_id, SalesRecord.store_id == store_id)
        .order_by(SalesRecord.date)
        .all()
    )

    if len(rows) < 14:
        logger.warning(f"Not enough data for product {product_id} (only {len(rows)} days). Using simple average.")
        return _fallback_forecast(db, product_id, store_id, rows, periods)

    df = pd.DataFrame(rows, columns=["ds", "y"])
    df["ds"] = pd.to_datetime(df["ds"])

    try:
        from prophet import Prophet

        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,
            changepoint_prior_scale=0.05,
        )
        model.fit(df)
        future = model.make_future_dataframe(periods=periods)
        forecast_df = model.predict(future)

        # Take only the future dates
        forecast_df = forecast_df.tail(periods)
    except Exception as e:
        logger.warning(f"Prophet failed for product {product_id}: {e}. Using fallback.")
        return _fallback_forecast(db, product_id, store_id, rows, periods)

    # Delete old forecasts for this product+store
    db.query(Forecast).filter(
        Forecast.product_id == product_id,
        Forecast.store_id == store_id,
    ).delete()

    forecasts = []
    for _, row in forecast_df.iterrows():
        fc = Forecast(
            product_id=product_id,
            store_id=store_id,
            forecast_date=row["ds"].date(),
            predicted_demand=max(0, round(row["yhat"], 1)),
            lower_bound=max(0, round(row["yhat_lower"], 1)),
            upper_bound=max(0, round(row["yhat_upper"], 1)),
            model_version="prophet-v1",
        )
        db.add(fc)
        forecasts.append(fc)

    db.commit()
    for fc in forecasts:
        db.refresh(fc)
    return forecasts


def _fallback_forecast(
    db: Session, product_id: int, store_id: str, rows: list, periods: int
) -> list[Forecast]:
    """Simple moving average fallback when Prophet can't run."""
    if rows:
        avg = sum(r[1] for r in rows) / len(rows)
    else:
        avg = 5.0  # default

    db.query(Forecast).filter(
        Forecast.product_id == product_id,
        Forecast.store_id == store_id,
    ).delete()

    today = date.today()
    forecasts = []
    for i in range(1, periods + 1):
        fc = Forecast(
            product_id=product_id,
            store_id=store_id,
            forecast_date=today + timedelta(days=i),
            predicted_demand=round(avg, 1),
            lower_bound=round(avg * 0.7, 1),
            upper_bound=round(avg * 1.3, 1),
            model_version="fallback-avg",
        )
        db.add(fc)
        forecasts.append(fc)

    db.commit()
    for fc in forecasts:
        db.refresh(fc)
    return forecasts


def run_batch_forecasts(db: Session, store_id: str = "store-1", periods: int = 7) -> dict:
    """Run forecasts for all active products in a store."""
    products = db.query(Product).filter(Product.is_active.is_(True)).all()
    total_forecasts = 0
    for product in products:
        fcs = train_and_forecast(db, product.id, store_id, periods)
        total_forecasts += len(fcs)

    return {
        "products_forecasted": len(products),
        "forecasts_created": total_forecasts,
        "message": f"Forecasted {len(products)} products, created {total_forecasts} forecast records.",
    }
