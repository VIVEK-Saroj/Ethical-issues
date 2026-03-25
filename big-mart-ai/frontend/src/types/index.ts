export interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'manager';
  store_id: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Product {
  id: number;
  sku: string;
  name: string;
  category: string;
  brand: string;
  unit_price: number;
  image_url: string | null;
  is_active: boolean;
  created_at: string;
}

export interface ShelfImage {
  id: number;
  store_id: string;
  aisle: string;
  uploaded_by: number;
  image_url: string;
  processing_status: 'pending' | 'processing' | 'done' | 'failed';
  total_detections: number;
  shelf_occupancy: number;
  upload_timestamp: string;
}

export interface Detection {
  id: number;
  image_id: number;
  product_id: number | null;
  product_name: string | null;
  class_label: string;
  bounding_box: { x1: number; y1: number; x2: number; y2: number };
  confidence: number;
  shelf_count: number;
  position_on_shelf: string | null;
}

export interface ImageWithDetections extends ShelfImage {
  detections: Detection[];
}

export interface Forecast {
  id: number;
  product_id: number;
  store_id: string;
  forecast_date: string;
  predicted_demand: number;
  lower_bound: number;
  upper_bound: number;
  model_version: string;
  created_at: string;
}

export interface ForecastSummary {
  product_id: number;
  sku: string;
  product_name: string;
  category: string;
  avg_daily_sales: number;
  predicted_tomorrow: number;
  predicted_next_week: number;
  trend: 'up' | 'down' | 'stable';
}

export interface DashboardStats {
  total_products: number;
  scans_today: number;
  stockout_risks: number;
  forecast_accuracy: number;
}

export interface TrendPoint {
  date: string;
  value: number;
}

export interface RiskDistribution {
  critical: number;
  warning: number;
  ok: number;
}

export interface TopRiskProduct {
  product_id: number;
  sku: string;
  name: string;
  category: string;
  shelf_stock: number;
  predicted_demand: number;
  risk_level: 'critical' | 'warning' | 'ok';
  restock_qty: number;
}

export interface RecentScan {
  id: number;
  image_url: string;
  aisle: string;
  total_detections: number;
  shelf_occupancy: number;
  upload_timestamp: string;
}

export interface Alert {
  product_id: number;
  sku: string;
  product_name: string;
  category: string;
  shelf_stock: number;
  predicted_demand_7d: number;
  risk_level: 'critical' | 'warning' | 'ok';
  restock_qty: number;
}

export interface AlertSummary {
  critical: number;
  warning: number;
  ok: number;
  total: number;
}
