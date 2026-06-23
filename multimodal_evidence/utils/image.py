"""Pre-flight image validation and utility functions before sending to Gemini API.

Checks file existence, readability, and format using Pillow.
Saves API tokens by catching bad inputs locally.
Supports both file paths and in-memory bytes.
"""

import io
from pathlib import Path
from PIL import Image

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


def resolve_image_path(image_path: str | Path, base_dir: Path | None = None) -> Path:
    """Resolve an image path relative to a base directory if provided and not absolute."""
    path = Path(image_path)
    if base_dir and not path.is_absolute():
        return base_dir / path
    return path


def validate_single_image(
    image_source: str | Path | bytes,
    base_dir: Path | None = None
) -> tuple[bool, list[str]]:
    """Validate a single image (from path or bytes).
    
    Returns:
        (is_valid, risk_flags) — is_valid=True if usable for API call.
    """
    flags = []
    
    if isinstance(image_source, (str, Path)):
        abs_path = resolve_image_path(image_source, base_dir)
        
        # Check existence
        if not abs_path.exists():
            flags.append("damage_not_visible")
            return False, flags
        
        # Check file size > 0
        if abs_path.stat().st_size == 0:
            flags.append("damage_not_visible")
            return False, flags
        
        # Check extension
        if abs_path.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
            flags.append("damage_not_visible")
            return False, flags
        
        # Check readability with Pillow
        try:
            with Image.open(abs_path) as img:
                img.verify()
        except Exception:
            flags.append("damage_not_visible")
            return False, flags
            
    elif isinstance(image_source, bytes):
        if len(image_source) == 0:
            flags.append("damage_not_visible")
            return False, flags
            
        try:
            with Image.open(io.BytesIO(image_source)) as img:
                img.verify()
                # Check format extension
                ext = f".{img.format.lower()}" if img.format else ""
                if ext == ".jpeg":
                    ext = ".jpg"
                if ext not in ALLOWED_IMAGE_EXTENSIONS and img.format not in ("JPEG", "PNG", "WEBP", "GIF", "BMP"):
                    flags.append("damage_not_visible")
                    return False, flags
        except Exception:
            flags.append("damage_not_visible")
            return False, flags
    else:
        flags.append("damage_not_visible")
        return False, flags
        
    return True, flags


def validate_claim_images(
    images: list[str | Path | bytes],
    base_dir: Path | None = None
) -> tuple[bool, list[str | Path | bytes], list[str]]:
    """Validate all images for a claim.
    
    Returns:
        (all_valid, valid_images, risk_flags)
        - all_valid: True if at least one image is usable
        - valid_images: list of sources that passed validation
        - risk_flags: any image-quality flags detected locally
    """
    valid_images = []
    all_flags = []
    
    for img in images:
        is_valid, flags = validate_single_image(img, base_dir)
        all_flags.extend(flags)
        if is_valid:
            valid_images.append(img)
            
    has_valid = len(valid_images) > 0
    return has_valid, valid_images, all_flags


def get_image_bytes(image_source: str | Path | bytes, base_dir: Path | None = None) -> bytes:
    """Get the raw bytes of an image (reads file if path, returns directly if bytes)."""
    if isinstance(image_source, bytes):
        return image_source
    abs_path = resolve_image_path(image_source, base_dir)
    return abs_path.read_bytes()


def get_image_mime_type(image_source: str | Path | bytes, base_dir: Path | None = None) -> str:
    """Determine MIME type from filename extension or bytes analysis."""
    if isinstance(image_source, bytes):
        try:
            with Image.open(io.BytesIO(image_source)) as img:
                fmt = img.format.lower() if img.format else "jpeg"
                return f"image/{fmt}"
        except Exception:
            return "image/jpeg"
            
    ext = Path(image_source).suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
    }
    return mime_map.get(ext, "image/jpeg")
