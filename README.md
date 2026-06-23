# Multimodal Evidence SDK

`multimodal-evidence-sdk` is a Python SDK for verifying, ranking, and reviewing multi-modal damage claims using Gemini vision models. It provides structural validation and decision-making logic originally developed for the HackerRank Orchestrate Evidence Review platform.

---

## Installation

Install the package locally in editable mode:

```bash
pip install -e .
```

---

## SDK Usage

```python
from multimodal_evidence import (
    retrieve_evidence,
    rank_evidence,
    verify_claim
)

# 1. Verify a claim statement factually (Text-only)
result = verify_claim(
    claim_text="India launched Chandrayaan-3 in 2023"
)
print(result["claim_status"])  # -> "supported"

# 2. Verify a damage claim with image evidence (Multimodal)
claim_result = verify_claim(
    claim_text="The car rear bumper has a major dent",
    images=["path/to/img_1.jpg"],
    claim_object="car",
    history={
        "user_id": "usr_123",
        "past_claim_count": 0,
        "accept_claim": 0,
        "manual_review_claim": 0,
        "rejected_claim": 0,
        "last_90_days_claim_count": 0,
        "history_flags": "none",
        "history_summary": ""
    }
)
print(claim_result["claim_status"])
```

---

## Command Line Interface (CLI)

The SDK registers the `evidence` executable.

### 1. Verify a Statement

```bash
evidence verify "The Earth has two moons"
```

For damage claims with images:
```bash
evidence verify "Rear bumper dent" --images "dataset/images/sample/case_001/img_1.jpg" --object car
```

### 2. Search Factual Details or Requirements

```bash
evidence search "Chandrayaan-3 launch"
```

```bash
evidence search car
```

### 3. Rank Evidence from JSON Payload

```bash
evidence rank evidence.json
```

---

## Development & Evaluation

If you are participating in the **HackerRank Orchestrate** hackathon, you can run the evaluation metrics and pipeline using the scripts in `code/`:

### 1. Install Dependencies
```bash
cd code/
pip install -r requirements.txt
```

### 2. Set API Key
Copy the template `.env.example` to `.env` and insert your API key:
```bash
# code/.env
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 3. Run Pipeline on Test Data
```bash
cd code/
python main.py
```

### 4. Run Strategy Evaluation
```bash
cd code/
python evaluation/main.py --compare
```

---

## Project Structure

*   `multimodal_evidence/`: The SDK package directory.
    *   `models/`: Pydantic schemas and enums.
    *   `retrieval/`: Search and requirements indexing.
    *   `ranking/`: Guardrails and risk flag merging.
    *   `verification/`: Claims and factual verifications.
    *   `multimodal/`: Gemini client wrapper and batch pipeline runner.
*   `code/`: The hackathon pipeline interface (fully refactored to consume the SDK).
*   `dataset/`: Claims databases and visual evidence.
