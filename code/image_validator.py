from pathlib import Path
from config import DATASET_DIR
import multimodal_evidence.utils.image as sdk_image

def resolve_image_path(relative_path: str) -> Path:
    return sdk_image.resolve_image_path(relative_path, DATASET_DIR)

def validate_single_image(relative_path: str):
    return sdk_image.validate_single_image(relative_path, DATASET_DIR)

def validate_claim_images(image_paths: list[str]):
    return sdk_image.validate_claim_images(image_paths, DATASET_DIR)

def get_image_bytes(relative_path: str) -> bytes:
    return sdk_image.get_image_bytes(relative_path, DATASET_DIR)

def get_image_mime_type(relative_path: str) -> str:
    return sdk_image.get_image_mime_type(relative_path, DATASET_DIR)
