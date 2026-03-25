"""Image storage service — saves to local media/ folder or Cloudinary."""

import uuid
from pathlib import Path

import cloudinary
import cloudinary.uploader
from app.core.config import get_settings

settings = get_settings()

if settings.CLOUDINARY_CLOUD_NAME:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )

# Local media directory (next to backend/)
MEDIA_DIR = Path(__file__).resolve().parent.parent.parent / "media" / "shelves"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def upload_image(file_bytes: bytes, folder: str = "bigmart-shelves") -> dict:
    """Save image. Returns {url, public_id, local_path}."""
    if settings.CLOUDINARY_CLOUD_NAME:
        result = cloudinary.uploader.upload(
            file_bytes, folder=folder, resource_type="image"
        )
        return {
            "url": result["secure_url"],
            "public_id": result["public_id"],
            "local_path": None,
        }

    # Local storage fallback
    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = MEDIA_DIR / filename
    filepath.write_bytes(file_bytes)
    return {
        "url": f"/media/shelves/{filename}",
        "public_id": f"local-{filename}",
        "local_path": str(filepath),
    }


def save_from_url(url: str) -> dict:
    """Download an image from URL and save locally. Returns same dict as upload_image."""
    import httpx
    resp = httpx.get(url, follow_redirects=True, timeout=20)
    resp.raise_for_status()
    return upload_image(resp.content)


def get_local_path(image_url: str) -> str | None:
    """If the image is stored locally, return the absolute file path."""
    if image_url.startswith("/media/shelves/"):
        filename = image_url.split("/")[-1]
        path = MEDIA_DIR / filename
        if path.exists():
            return str(path)
    return None


def delete_image(public_id: str) -> bool:
    if not settings.CLOUDINARY_CLOUD_NAME or public_id.startswith("local-"):
        return True
    result = cloudinary.uploader.destroy(public_id)
    return result.get("result") == "ok"
