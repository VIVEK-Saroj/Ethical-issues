FROM python:3.12-slim

WORKDIR /app

# System deps for OpenCV (ultralytics) and psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Download YOLOv8m if not bundled (runs once at build time)
RUN python -c "from ultralytics import YOLO; YOLO('yolov8m.pt')" 2>/dev/null || true

# Create media directory for uploaded images
RUN mkdir -p /app/media/shelves

ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--timeout-keep-alive", "120"]
