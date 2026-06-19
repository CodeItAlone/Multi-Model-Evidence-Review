"""Pre-flight image validation before sending to Gemini API.

Checks file existence, readability, and format using Pillow.
Saves API tokens by catching bad inputs locally.
"""

from pathlib import Path
from PIL import Image

from config import ALLOWED_IMAGE_EXTENSIONS, DATASET_DIR


def resolve_image_path(relative_path: str) -> Path:
    """Resolve an image path relative to the dataset directory."""
    return DATASET_DIR / relative_path


def validate_single_image(relative_path: str) -> tuple[bool, list[str]]:
    """Validate a single image file.
    
    Returns:
        (is_valid, risk_flags) — is_valid=True if usable for API call.
    """
    flags = []
    abs_path = resolve_image_path(relative_path)
    
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
            img.verify()  # Verify it's a valid image
    except Exception:
        flags.append("damage_not_visible")
        return False, flags
    
    return True, flags


def validate_claim_images(image_paths: list[str]) -> tuple[bool, list[str], list[str]]:
    """Validate all images for a claim.
    
    Returns:
        (all_valid, valid_paths, risk_flags)
        - all_valid: True if at least one image is usable
        - valid_paths: list of paths that passed validation
        - risk_flags: any image-quality flags detected locally
    """
    valid_paths = []
    all_flags = []
    
    for path in image_paths:
        is_valid, flags = validate_single_image(path)
        all_flags.extend(flags)
        if is_valid:
            valid_paths.append(path)
    
    has_valid = len(valid_paths) > 0
    return has_valid, valid_paths, all_flags


def get_image_bytes(relative_path: str) -> bytes:
    """Read image file as bytes for Gemini API upload."""
    abs_path = resolve_image_path(relative_path)
    return abs_path.read_bytes()


def get_image_mime_type(relative_path: str) -> str:
    """Determine MIME type from file extension."""
    ext = Path(relative_path).suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
    }
    return mime_map.get(ext, "image/jpeg")
