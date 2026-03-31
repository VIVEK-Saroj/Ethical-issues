"""
Migrate local SQLite demo data → Supabase PostgreSQL.

Usage:
  1. Ensure bigmart.db exists with seeded data (run backend locally first)
  2. Set SUPABASE_DB_URL env var (from Supabase dashboard → Settings → Database → Connection string)
     Example: postgresql://postgres.xxxx:PASSWORD@aws-0-us-east-1.pooler.supabase.com:5432/postgres
  3. Run:
       cd backend
       .venv\\Scripts\\activate
       set SUPABASE_DB_URL=postgresql://postgres.xxxx:PASSWORD@aws-0-...supabase.com:5432/postgres
       python seed_supabase.py
"""

import os
import sys
import json
import sqlite3

# Make app importable
sys.path.insert(0, os.path.dirname(__file__))

PG_URL = os.environ.get("SUPABASE_DB_URL")
if not PG_URL:
    print("ERROR: Set SUPABASE_DB_URL environment variable first.")
    print("  Get it from Supabase dashboard → Settings → Database → Connection string (URI)")
    sys.exit(1)

SQLITE_PATH = os.path.join(os.path.dirname(__file__), "bigmart.db")
if not os.path.exists(SQLITE_PATH):
    print(f"ERROR: {SQLITE_PATH} not found. Run the backend locally first to create seeded data.")
    sys.exit(1)

# Override DATABASE_URL so ORM models use PostgreSQL
os.environ["DATABASE_URL"] = PG_URL

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.database import Base

# Import all models so Base.metadata knows about them
from app.models.user import User
from app.models.product import Product
from app.models.sales_record import SalesRecord
from app.models.shelf_image import ShelfImage
from app.models.detection_result import DetectionResult
from app.models.forecast import Forecast

print(f"Source:  {SQLITE_PATH}")
print(f"Target:  {PG_URL[:60]}...")


def migrate():
    # ── Connect to both databases ──────────────────────────────────
    src = sqlite3.connect(SQLITE_PATH)
    src.row_factory = sqlite3.Row

    pg_engine = create_engine(PG_URL, pool_pre_ping=True)
    PgSession = sessionmaker(bind=pg_engine)
    pg = PgSession()

    # ── Create tables (drop first for clean slate) ─────────────────
    print("\n1. Creating PostgreSQL tables...")
    Base.metadata.drop_all(bind=pg_engine)
    Base.metadata.create_all(bind=pg_engine)
    print("   ✓ Tables created")

    # ── Helper: copy a table ───────────────────────────────────────
    def copy_table(table_name: str, columns: list[str], json_columns: list[str] | None = None):
        rows = src.execute(f"SELECT * FROM {table_name}").fetchall()
        if not rows:
            print(f"   ⚠ {table_name}: empty, skipping")
            return

        json_cols = set(json_columns or [])
        col_list = ", ".join(columns)
        placeholders = ", ".join(f":{c}" for c in columns)
        insert_sql = text(f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})")

        batch = []
        for r in rows:
            params = {}
            for c in columns:
                val = r[c]
                if c in json_cols and isinstance(val, str):
                    val = json.loads(val)
                params[c] = val
            batch.append(params)

        pg.execute(insert_sql, batch)
        pg.commit()

        # Reset auto-increment sequence to max id
        if "id" in columns:
            max_id = max(b["id"] for b in batch)
            seq_name = f"{table_name}_id_seq"
            pg.execute(text(f"SELECT setval('{seq_name}', :val)"), {"val": max_id})
            pg.commit()

        print(f"   ✓ {table_name}: {len(batch)} rows")

    # ── Copy each table ────────────────────────────────────────────
    print("\n2. Copying data...")

    copy_table("users", [
        "id", "username", "email", "hashed_password", "role", "store_id", "created_at",
    ])

    copy_table("products", [
        "id", "sku", "name", "category", "brand", "unit_price",
        "image_url", "is_active", "created_at",
    ])

    copy_table("sales_records", [
        "id", "product_id", "store_id", "date", "quantity_sold", "revenue",
    ])

    copy_table("shelf_images", [
        "id", "store_id", "aisle", "uploaded_by", "image_url",
        "cloudinary_public_id", "processing_status",
        "total_detections", "shelf_occupancy", "upload_timestamp",
    ])

    copy_table("detection_results", [
        "id", "image_id", "product_id", "class_label",
        "bounding_box", "confidence", "shelf_count", "position_on_shelf",
    ], json_columns=["bounding_box"])

    copy_table("forecasts", [
        "id", "product_id", "store_id", "forecast_date",
        "predicted_demand", "lower_bound", "upper_bound",
        "model_version", "created_at",
    ])

    src.close()
    pg.close()
    print("\n✓ Migration complete! All demo data is now in Supabase.")


if __name__ == "__main__":
    migrate()
