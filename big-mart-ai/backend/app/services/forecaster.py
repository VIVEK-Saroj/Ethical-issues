"""Holt-Winters demand forecasting service.

Trains per-SKU exponential smoothing models on historical POS data and
predicts next N days of demand with confidence intervals.
"""

import logging
from datetime import date, timedelta

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from statsmodels.tsa.holtwinters import ExponentialSmoothing

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
    """Train Holt-Winters on a single SKU's history and predict `periods` days ahead."""
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
    df = df.set_index("ds").asfreq("D")
    df["y"] = df["y"].ffill().fillna(0)
    # Holt-Winters needs positive values for multiplicative seasonality
    df["y"] = df["y"].clip(lower=0.1)

    try:
        model = ExponentialSmoothing(
            df["y"],
            trend="add",
            seasonal="add",
            seasonal_periods=7,
        ).fit(optimized=True)

        forecast_values = model.forecast(periods)
        # Approximate confidence interval using residual std
        residuals = model.resid.dropna()
        std = residuals.std() if len(residuals) > 0 else 1.0
    except Exception as e:
        logger.warning(f"Holt-Winters failed for product {product_id}: {e}. Using fallback.")
        return _fallback_forecast(db, product_id, store_id, rows, periods)

    # Delete old forecasts for this product+store
    db.query(Forecast).filter(
        Forecast.product_id == product_id,
        Forecast.store_id == store_id,
    ).delete()

    forecasts = []
    for i, (fc_date, yhat) in enumerate(forecast_values.items()):
        lower = yhat - 1.96 * std
        upper = yhat + 1.96 * std
        fc = Forecast(
            product_id=product_id,
            store_id=store_id,
            forecast_date=fc_date.date(),
            predicted_demand=max(0, round(float(yhat), 1)),
            lower_bound=max(0, round(float(lower), 1)),
            upper_bound=max(0, round(float(upper), 1)),
            model_version="holtwinters-v1",
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
