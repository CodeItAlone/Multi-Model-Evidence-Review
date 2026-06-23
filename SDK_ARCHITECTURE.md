# SDK Architecture: Multimodal Evidence SDK

This document defines the Python SDK design for `multimodal-evidence-sdk`.

---

## 1. Package Structure

The SDK will reside in the `multimodal_evidence` package directory with the following structure:

```
multimodal_evidence/
├── __init__.py          # Exposed public APIs (verify_claim, retrieve_evidence, rank_evidence)
├── models/              # Pydantic data models & schema definitions
│   ├── __init__.py
│   └── claim.py         # ClaimInput, ClaimOutput, GeminiAnalysisResult, and Enums
├── retrieval/           # Evidence retrieval logic and CSV parsers
│   ├── __init__.py
│   └── search.py        # Loading and indexing requirements/history
├── ranking/             # Evidence sorting, filtering, and decision overrides
│   ├── __init__.py
│   └── ranker.py        # supporting_image_ids identification, severity levels
├── verification/        # High-level claim verification orchestration
│   ├── __init__.py
│   └── verifier.py      # verify_claim function & core LLM-guided verification
├── multimodal/          # Image pre-flight checks and API wrappers
│   ├── __init__.py
│   ├── client.py        # Gemini client wrapper, rate limiter, and backoff
│   └── pipeline.py      # Async batch claims runner
├── embeddings/          # Extensible placeholder for future embedding search
│   └── __init__.py
└── utils/               # Common helper utilities
    ├── __init__.py
    ├── image.py         # Pillow image validation and bytes converters
    └── errors.py        # Custom SDK exceptions
```

---

## 2. Public APIs

The top-level `__init__.py` will export:

```python
from multimodal_evidence.verification.verifier import verify_claim
from multimodal_evidence.retrieval.search import retrieve_evidence
from multimodal_evidence.ranking.ranker import rank_evidence

__all__ = [
    "verify_claim",
    "retrieve_evidence",
    "rank_evidence",
]
```

### API Details

#### 1. `verify_claim`
Verifies a single claim using text and image evidence.

```python
def verify_claim(
    claim_text: str,
    images: list[str | bytes] | None = None,
    claim_object: str = "car",
    history: dict | None = None,
    requirements: list | None = None,
    api_key: str = "",
    model: str = "gemini-flash-lite-latest",
    strategy: str = "few_shot"
) -> dict:
    """Verifies a single claim using multimodal inputs.
    
    Args:
        claim_text: Chat transcript/description of the claim.
        images: List of local paths OR raw bytes of images.
        claim_object: Type of object (car, laptop, package).
        history: Dictionary representing user history record.
        requirements: List of dictionaries of evidence requirements.
        api_key: Optional Gemini API key override.
        model: Model name override.
        strategy: 'direct' or 'few_shot'.
        
    Returns:
        dict: Validated claim verification output matching the output schema.
    """
```

#### 2. `retrieve_evidence`
Retrieves applicable evidence requirements for a given claim object type.

```python
def retrieve_evidence(
    claim_object: str,
    requirements_path_or_list: str | list[dict]
) -> list[dict]:
    """Retrieves and filters requirements applicable to a specific claim object.
    
    Returns requirements where claim_object matches or is "all".
    """
```

#### 3. `rank_evidence`
Applies sorting, filtering, and decision guardrails over raw Gemini outputs.

```python
def rank_evidence(
    claim_input: dict,
    gemini_result: dict,
    history: dict | None = None
) -> dict:
    """Combines user history and validation results to override raw outcomes."""
```

---

## 3. Dependency Strategy

To remain lightweight and embeddable, dependencies are kept to a minimum:

*   **`google-genai>=0.1.1`** (Core Gemini client communication)
*   **`pydantic>=2.0.0`** (Data schema enforcement and serialization)
*   **`Pillow>=9.0.0`** (Pre-flight image format and resolution verification)
*   **`python-dotenv>=1.0.0`** (Optional helper for development setup)
*   **`tqdm`** (Progress bar for batch execution, optional depend)

---

## 4. Configuration Strategy

Config settings will be managed dynamically via a `Settings` class instead of global constants:

```python
from pydantic import BaseModel, Field

class SDKSettings(BaseModel):
    google_api_key: str = Field(default="", env="GOOGLE_API_KEY")
    gemini_model: str = "gemini-flash-lite-latest"
    concurrency_limit: int = 5
    max_retries: int = 5
    initial_backoff: float = 15.0
```

This can be initialized from standard environment variables automatically, or programmatically passed to client instances, keeping the SDK isolated from global side effects.

---

## 5. Error Handling Strategy

All SDK actions will raise standard custom exceptions derived from a base exception:

```python
class MultimodalSDKError(Exception):
    """Base exception for all SDK errors."""

class ConfigurationError(MultimodalSDKError):
    """Raised when configuration, paths, or keys are missing or invalid."""

class ImageValidationError(MultimodalSDKError):
    """Raised when input images are corrupt, unreadable, or missing."""

class APIError(MultimodalSDKError):
    """Raised when the Gemini API returns errors or fails all retries."""

class ValidationError(MultimodalSDKError):
    """Raised when Gemini responses fail model validation."""
```

---

## 6. Logging Strategy

*   The SDK will use Python's built-in `logging` module.
*   The parent logger will be named `"multimodal_evidence"`.
*   All CLI print statements will be replaced by log entries (`logger.info`, `logger.warning`, `logger.error`).
*   SDK users can customize logs by attaching standard handlers to `"multimodal_evidence"`.
