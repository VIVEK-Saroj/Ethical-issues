from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_products: int
    scans_today: int
    stockout_risks: int
    forecast_accuracy: float


class TrendPoint(BaseModel):
    date: str
    value: float


class RiskDistribution(BaseModel):
    critical: int
    warning: int
    ok: int


class TopRiskProduct(BaseModel):
    product_id: int
    sku: str
    name: str
    category: str
    shelf_stock: int
    predicted_demand: float
    risk_level: str
    restock_qty: int


class RecentScan(BaseModel):
    id: int
    image_url: str
    aisle: str
    total_detections: int
    shelf_occupancy: float
    upload_timestamp: str


class AlertOut(BaseModel):
    product_id: int
    sku: str
    product_name: str
    category: str
    shelf_stock: int
    predicted_demand_7d: float
    risk_level: str  # critical | warning | ok
    restock_qty: int


class AlertSummary(BaseModel):
    critical: int
    warning: int
    ok: int
    total: int
