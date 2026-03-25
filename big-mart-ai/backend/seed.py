"""CLI script to seed demo data."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal, engine, Base
from app.services.seed_data import seed_all


def main():
    print("Big Mart AI — Seeding demo data...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()
    print("Done!")


if __name__ == "__main__":
    main()
