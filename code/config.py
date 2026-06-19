"""Configuration settings for the Multi-Modal Evidence Review pipeline."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from code/ directory
load_dotenv(Path(__file__).parent / ".env")

# --- Paths ---
PROJECT_ROOT = Path(__file__).parent.parent  # hackerrank-orchestrate-june26-1/
CODE_DIR = Path(__file__).parent             # code/
DATASET_DIR = PROJECT_ROOT / "dataset"
IMAGES_DIR = DATASET_DIR / "images"
SAMPLE_CLAIMS_PATH = DATASET_DIR / "sample_claims.csv"
TEST_CLAIMS_PATH = DATASET_DIR / "claims.csv"
USER_HISTORY_PATH = DATASET_DIR / "user_history.csv"
EVIDENCE_REQUIREMENTS_PATH = DATASET_DIR / "evidence_requirements.csv"
OUTPUT_PATH = PROJECT_ROOT / "output.csv"

# --- Gemini API ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
CONCURRENCY = int(os.getenv("CONCURRENCY", "1"))

# --- Retry Settings ---
MAX_RETRIES = 5
INITIAL_BACKOFF_SECONDS = 15.0
BACKOFF_MULTIPLIER = 1.5

# --- Image Validation ---
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
