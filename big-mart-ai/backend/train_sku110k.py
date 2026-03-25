"""Train YOLOv8m on SKU-110K retail dataset."""
import sys
print(f"Python: {sys.executable}")

import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

from ultralytics import YOLO

model = YOLO("yolov8m.pt")

results = model.train(
    data="SKU-110K.yaml",
    epochs=50,
    imgsz=640,
    batch=8,
    device=0 if torch.cuda.is_available() else "cpu",
    patience=10,
    save=True,
    project="runs/sku110k",
    name="yolov8m_sku110k",
    pretrained=True,
    optimizer="AdamW",
    lr0=0.001,
    lrf=0.01,
    warmup_epochs=3,
    cos_lr=True,
    workers=4,
    cache=False,
    verbose=True,
)

print("Training complete!")
print(f"Best model: {results.save_dir / 'weights' / 'best.pt'}")
