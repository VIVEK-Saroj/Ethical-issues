"""Generate realistic demo data for Big Mart AI."""

import random
from datetime import date, timedelta, datetime, timezone
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.product import Product
from app.models.sales_record import SalesRecord
from app.models.shelf_image import ShelfImage
from app.models.detection_result import DetectionResult
from app.models.forecast import Forecast
from app.core.security import hash_password

PRODUCTS = [
    # Beverages
    ("BEV-001", "Coca-Cola 500ml", "Beverages", "Coca-Cola", 1.99),
    ("BEV-002", "Pepsi 500ml", "Beverages", "PepsiCo", 1.89),
    ("BEV-003", "Spring Water 1L", "Beverages", "Aquafina", 0.99),
    ("BEV-004", "Orange Juice 1L", "Beverages", "Tropicana", 3.49),
    ("BEV-005", "Green Tea 250ml", "Beverages", "Lipton", 1.29),
    ("BEV-006", "Energy Drink 250ml", "Beverages", "Red Bull", 2.99),
    ("BEV-007", "Milk 1L Full Fat", "Beverages", "Dairy Fresh", 2.49),
    ("BEV-008", "Coffee Latte 330ml", "Beverages", "Starbucks", 3.99),
    # Snacks
    ("SNK-001", "Potato Chips Classic", "Snacks", "Lay's", 2.49),
    ("SNK-002", "Chocolate Bar", "Snacks", "Cadbury", 1.79),
    ("SNK-003", "Mixed Nuts 200g", "Snacks", "Planters", 4.99),
    ("SNK-004", "Protein Bar", "Snacks", "Kind", 2.99),
    ("SNK-005", "Popcorn Butter", "Snacks", "Orville", 3.29),
    ("SNK-006", "Rice Crackers", "Snacks", "Sakata", 2.19),
    ("SNK-007", "Trail Mix 300g", "Snacks", "Nature Valley", 5.49),
    # Dairy
    ("DRY-001", "Greek Yogurt 500g", "Dairy", "Chobani", 4.49),
    ("DRY-002", "Cheddar Cheese 250g", "Dairy", "Tillamook", 5.99),
    ("DRY-003", "Butter Unsalted 250g", "Dairy", "Kerrygold", 4.99),
    ("DRY-004", "Cream Cheese 200g", "Dairy", "Philadelphia", 3.49),
    ("DRY-005", "Mozzarella 200g", "Dairy", "Galbani", 3.99),
    # Produce
    ("PRD-001", "Bananas 1kg", "Produce", "Dole", 1.49),
    ("PRD-002", "Apples Red 1kg", "Produce", "Local Farm", 2.99),
    ("PRD-003", "Oranges 1kg", "Produce", "Sunkist", 3.49),
    ("PRD-004", "Avocados 3pk", "Produce", "Hass", 4.99),
    ("PRD-005", "Tomatoes 500g", "Produce", "Local Farm", 2.29),
    ("PRD-006", "Spinach 200g", "Produce", "Organic Valley", 2.99),
    ("PRD-007", "Carrots 1kg", "Produce", "Local Farm", 1.99),
    # Bakery
    ("BKY-001", "White Bread Loaf", "Bakery", "Wonder", 2.49),
    ("BKY-002", "Whole Wheat Bread", "Bakery", "Dave's", 4.49),
    ("BKY-003", "Croissants 4pk", "Bakery", "La Boulangerie", 3.99),
    ("BKY-004", "Bagels 6pk", "Bakery", "Thomas", 3.49),
    # Household
    ("HH-001", "Paper Towels 6pk", "Household", "Bounty", 8.99),
    ("HH-002", "Dish Soap 750ml", "Household", "Dawn", 3.49),
    ("HH-003", "Laundry Detergent 2L", "Household", "Tide", 11.99),
    ("HH-004", "Trash Bags 30ct", "Household", "Glad", 6.99),
    ("HH-005", "All-Purpose Cleaner", "Household", "Mr. Clean", 4.49),
    # Personal Care
    ("PC-001", "Shampoo 400ml", "Personal Care", "Pantene", 5.99),
    ("PC-002", "Toothpaste 150g", "Personal Care", "Colgate", 3.49),
    ("PC-003", "Hand Soap 250ml", "Personal Care", "Dove", 2.99),
    ("PC-004", "Deodorant", "Personal Care", "Old Spice", 4.99),
    # Frozen
    ("FRZ-001", "Frozen Pizza", "Frozen", "DiGiorno", 6.99),
    ("FRZ-002", "Ice Cream 1L", "Frozen", "Ben & Jerry's", 5.99),
    ("FRZ-003", "Frozen Vegetables 500g", "Frozen", "Bird's Eye", 2.99),
    ("FRZ-004", "Frozen Chicken Nuggets", "Frozen", "Tyson", 7.49),
    # Canned
    ("CAN-001", "Canned Tuna", "Canned Goods", "StarKist", 1.99),
    ("CAN-002", "Canned Tomatoes 400g", "Canned Goods", "Hunt's", 1.49),
    ("CAN-003", "Canned Beans 400g", "Canned Goods", "Bush's", 1.29),
    ("CAN-004", "Chicken Soup", "Canned Goods", "Campbell's", 2.49),
    # Condiments
    ("CND-001", "Ketchup 500ml", "Condiments", "Heinz", 3.49),
    ("CND-002", "Mayonnaise 400g", "Condiments", "Hellmann's", 4.49),
]

AISLES = ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2"]

# Images curated for real YOLO detections (bottles, fruit, produce, baked goods)
SHELF_IMAGES = [
    ("A1", "https://images.unsplash.com/photo-1506617420156-8e4536971650?w=800&h=600&fit=crop"),   # produce market – bottles/produce
    ("A2", "https://images.unsplash.com/photo-1488459716781-31db52582fe9?w=800&h=600&fit=crop"),    # fruit display – apples
    ("A3", "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=800&h=600&fit=crop"),    # bakery – cakes/donuts
    ("B1", "https://images.unsplash.com/photo-1542838132-92c53300491e?w=800&h=600&fit=crop"),       # produce bins – oranges/broccoli
    ("B2", "https://images.unsplash.com/photo-1567306226416-28f0efdc88ce?w=800&h=600&fit=crop"),    # market stall – apples
    ("B3", "https://images.unsplash.com/photo-1527960471264-932f39eb5846?w=800&h=600&fit=crop"),    # soda aisle – bottles
    ("C1", "https://images.unsplash.com/photo-1595981267035-7b04ca84a82d?w=800&h=600&fit=crop"),    # juice shelf – cups/bottles
    ("C2", "https://images.unsplash.com/photo-1606168094336-48f205276929?w=800&h=600&fit=crop"),    # fridge display – oranges/bottles
    ("A1", "https://images.unsplash.com/photo-1550989460-0adf9ea622e2?w=800&h=600&fit=crop"),       # market – carrots/broccoli/apples
    ("A3", "https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=800&h=600&fit=crop"),    # fruit – oranges/bananas
    ("B1", "https://images.unsplash.com/photo-1573246123716-6b1782bfc499?w=800&h=600&fit=crop"),    # veggies – carrots/broccoli/oranges
    ("B2", "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&h=600&fit=crop"),    # pizza – frozen
    ("C1", "https://images.unsplash.com/photo-1611080626919-7cf5a9dbab5b?w=800&h=600&fit=crop"),    # oranges display
    ("C2", "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=800&h=600&fit=crop"),      # apples display
    ("A2", "https://images.unsplash.com/photo-1583258292688-d0213dc5a3a8?w=800&h=600&fit=crop"),    # dairy section – oranges/apples
]


def seed_all(db: Session):
    """Generate all demo data."""
    _seed_users(db)
    products = _seed_products(db)
    _seed_sales(db, products)
    _seed_images_and_detections(db, products)
    _seed_forecasts(db, products)
    print("✓ Demo data seeded successfully!")


def _seed_users(db: Session):
    if db.query(User).first():
        print("  Users already exist, skipping...")
        return
    users = [
        User(
            username="admin",
            email="admin@bigmart.com",
            hashed_password=hash_password("admin123"),
            role="admin",
            store_id="store-1",
        ),
        User(
            username="manager",
            email="manager@bigmart.com",
            hashed_password=hash_password("manager123"),
            role="manager",
            store_id="store-1",
        ),
    ]
    db.add_all(users)
    db.commit()
    print(f"  ✓ Created {len(users)} demo users")


def _seed_products(db: Session) -> list[Product]:
    if db.query(Product).first():
        print("  Products already exist, skipping...")
        return db.query(Product).all()
    products = []
    for sku, name, category, brand, price in PRODUCTS:
        p = Product(sku=sku, name=name, category=category, brand=brand, unit_price=price)
        products.append(p)
    db.add_all(products)
    db.commit()
    for p in products:
        db.refresh(p)
    print(f"  ✓ Created {len(products)} products")
    return products


def _seed_sales(db: Session, products: list[Product]):
    if db.query(SalesRecord).first():
        print("  Sales records already exist, skipping...")
        return
    today = date.today()
    start = today - timedelta(days=180)  # 6 months
    records = []

    for product in products:
        # Base daily sales varies by product
        base = random.uniform(5, 40)
        # Some products have an upward trend, some downward
        trend = random.uniform(-0.02, 0.03)

        current = start
        while current <= today:
            day_of_week = current.weekday()
            # Weekend boost
            weekend_factor = 1.3 if day_of_week >= 5 else 1.0
            # Slight monthly seasonality
            month_factor = 1.0 + 0.1 * ((current.month % 3) - 1)
            # Random noise
            noise = random.gauss(1.0, 0.15)
            # Trend drift
            days_from_start = (current - start).days
            trend_factor = 1.0 + trend * (days_from_start / 30)

            quantity = max(0, int(base * weekend_factor * month_factor * noise * trend_factor))
            revenue = round(quantity * product.unit_price, 2)

            records.append(
                SalesRecord(
                    product_id=product.id,
                    store_id="store-1",
                    date=current,
                    quantity_sold=quantity,
                    revenue=revenue,
                )
            )
            current += timedelta(days=1)

    db.bulk_save_objects(records)
    db.commit()
    print(f"  ✓ Created {len(records)} sales records ({len(products)} products × 180 days)")


def _seed_images_and_detections(db: Session, products: list[Product]):
    if db.query(ShelfImage).first():
        print("  Shelf images already exist, skipping...")
        return

    from app.services.image_storage import save_from_url
    from app.services.shelf_detector import detect_products, COCO_TO_CATEGORY

    admin = db.query(User).filter(User.username == "admin").first()
    user_id = admin.id if admin else 1

    # Build category → product lookup for linking detections to inventory
    cat_to_products: dict[str, list[Product]] = {}
    for p in products:
        cat_to_products.setdefault(p.category, []).append(p)

    today = date.today()
    total_images = 0
    total_detections = 0

    for i, (aisle, url) in enumerate(SHELF_IMAGES):
        scan_date = today - timedelta(days=random.randint(0, 6))
        print(f"  Downloading & analyzing image {i+1}/{len(SHELF_IMAGES)}...")

        try:
            # Download image and save locally
            saved = save_from_url(url)
            local_path = saved.get("local_path")

            # Run real YOLO detection
            source = local_path or url
            result = detect_products(source, confidence_threshold=0.20)

            img = ShelfImage(
                store_id="store-1",
                aisle=aisle,
                uploaded_by=user_id,
                image_url=saved["url"],
                cloudinary_public_id=saved["public_id"],
                processing_status="done",
                total_detections=result["total_count"],
                shelf_occupancy=result["shelf_occupancy"],
                upload_timestamp=datetime(
                    scan_date.year, scan_date.month, scan_date.day,
                    random.randint(8, 18), random.randint(0, 59),
                    tzinfo=timezone.utc,
                ),
            )
            db.add(img)
            db.commit()
            db.refresh(img)
            total_images += 1

            # Store real detections linked to inventory products
            for det in result["detections"]:
                category = det["category"]
                product_id = None
                if category in cat_to_products and cat_to_products[category]:
                    matched = random.choice(cat_to_products[category])
                    product_id = matched.id

                db.add(DetectionResult(
                    image_id=img.id,
                    product_id=product_id,
                    class_label=det["class_label"],
                    bounding_box=det["bounding_box"],
                    confidence=det["confidence"],
                    shelf_count=1,
                    position_on_shelf=det.get("position_on_shelf"),
                ))
                total_detections += 1

            db.commit()

        except Exception as e:
            print(f"    ⚠ Failed image {i+1}: {e}")
            continue

    print(f"  ✓ Created {total_images} shelf images with {total_detections} REAL detections")


def _seed_forecasts(db: Session, products: list[Product]):
    if db.query(Forecast).first():
        print("  Forecasts already exist, skipping...")
        return

    today = date.today()
    forecasts = []
    for product in products:
        base = random.uniform(8, 35)
        for day_offset in range(1, 8):
            fc_date = today + timedelta(days=day_offset)
            noise = random.gauss(1.0, 0.1)
            demand = max(1, round(base * noise, 1))
            forecasts.append(
                Forecast(
                    product_id=product.id,
                    store_id="store-1",
                    forecast_date=fc_date,
                    predicted_demand=demand,
                    lower_bound=round(demand * 0.75, 1),
                    upper_bound=round(demand * 1.25, 1),
                    model_version="seed-v1",
                )
            )

    db.bulk_save_objects(forecasts)
    db.commit()
    print(f"  ✓ Created {len(forecasts)} forecast records")
