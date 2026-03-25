"""Quick test of real detection pipeline."""
import httpx

# Login
r = httpx.post('http://localhost:8001/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
token = r.json()['access_token']
h = {'Authorization': f'Bearer {token}'}

# Test images list
r2 = httpx.get('http://localhost:8001/api/images/', headers=h)
imgs = r2.json()
print(f"Images: {len(imgs)}")
for img in imgs[:3]:
    print(f"  Aisle {img['aisle']}: {img['total_detections']} detections, "
          f"{img['shelf_occupancy']}% occupancy, url={img['image_url'][:50]}")

# Test image detail with detections + product names
r3 = httpx.get(f"http://localhost:8001/api/images/{imgs[0]['id']}", headers=h)
detail = r3.json()
print(f"\nImage {detail['id']} detail: {len(detail['detections'])} detections")
for d in detail['detections'][:5]:
    pname = d.get('product_name') or 'unmatched'
    print(f"  {d['class_label']} -> {pname} ({d['confidence']:.0%}) at {d['position_on_shelf']}")

# Test local image file serving
img_url = imgs[0]['image_url']
if img_url.startswith('/media/'):
    r4 = httpx.get(f"http://localhost:8001{img_url}")
    print(f"\nLocal image serving: {r4.status_code} ({len(r4.content)} bytes)")

print("\n--- All product links ---")
linked = sum(1 for d in detail['detections'] if d.get('product_name'))
total = len(detail['detections'])
print(f"Linked to inventory: {linked}/{total}")
