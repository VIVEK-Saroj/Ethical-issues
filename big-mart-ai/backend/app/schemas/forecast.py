from pydantic import BaseModel
from datetime import date, datetime


class ForecastOut(BaseModel):
    id: int
    product_id: int
    store_id: str
    forecast_date: date
    predicted_demand: float
    lower_bound: float
    upper_bound: float
    model_version: str
    created_at: datetime

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class ForecastSummary(BaseModel):
    product_id: int
    sku: str
    product_name: str
    category: str
    avg_daily_sales: float
    predicted_tomorrow: float
    predicted_next_week: float
    trend: str  # up | down | stable


class ForecastRunResult(BaseModel):
    products_forecasted: int
    forecasts_created: int
    message: str
