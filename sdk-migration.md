# SDK Migration Plan

## Overview
Migrate the existing Multi-Modal Evidence Review hackathon system into a structured, installable, and reusable Python SDK (`multimodal-evidence-sdk`) with clean public API entry points and a CLI utility.

## Project Type
BACKEND / SDK

## Success Criteria
1. The new package `multimodal_evidence` exposes `verify_claim`, `retrieve_evidence`, and `rank_evidence`.
2. Existing codebase in `code/` imports from the SDK and executes without errors.
3. The evaluation metrics computed via `code/evaluation/main.py` match pre-migration metrics exactly.
4. CLI command `evidence` is functional and correct.

## Tech Stack
*   **Language:** Python (3.10+)
*   **Libraries:** `google-genai`, `pydantic`, `Pillow`, `tqdm`
*   **Build System:** `hatchling` (modern standard for pyproject.toml)

## File Structure
```
multimodal_evidence/
├── __init__.py
├── models/
│   ├── __init__.py
│   └── claim.py
├── retrieval/
│   ├── __init__.py
│   └── search.py
├── ranking/
│   ├── __init__.py
│   └── ranker.py
├── verification/
│   ├── __init__.py
│   └── verifier.py
├── multimodal/
│   ├── __init__.py
│   ├── client.py
│   └── pipeline.py
├── embeddings/
│   └── __init__.py
└── utils/
    ├── __init__.py
    ├── image.py
    └── errors.py
```

## Task Breakdown

### Task 1: Package Directory and Init setup
- **Agent:** project-planner
- **Priority:** P0
- **Dependencies:** None
- **INPUT:** None
- **OUTPUT:** Directory tree with empty `__init__.py` files.
- **VERIFY:** Check directories exist.

### Task 2: Models and Errors
- **Agent:** backend-specialist
- **Priority:** P1
- **Dependencies:** Task 1
- **INPUT:** `code/models.py`
- **OUTPUT:** `multimodal_evidence/models/claim.py` and `multimodal_evidence/utils/errors.py`.
- **VERIFY:** Python compile check on new files.

### Task 3: Image Utility & Client
- **Agent:** backend-specialist
- **Priority:** P1
- **Dependencies:** Task 2
- **INPUT:** `code/image_validator.py`, `code/gemini_client.py`
- **OUTPUT:** `multimodal_evidence/utils/image.py` and `multimodal_evidence/multimodal/client.py`.
- **VERIFY:** Ensure images can be validated via Pillow in the new module.

### Task 4: Retrieval and Ranking
- **Agent:** backend-specialist
- **Priority:** P1
- **Dependencies:** Task 3
- **INPUT:** `code/parsers.py`, `code/post_processor.py`, `code/prompts.py`
- **OUTPUT:** `multimodal_evidence/retrieval/search.py` and `multimodal_evidence/ranking/ranker.py`.
- **VERIFY:** Test loading sample database in isolation.

### Task 5: High-level APIs and Orchestration
- **Agent:** backend-specialist
- **Priority:** P1
- **Dependencies:** Task 4
- **INPUT:** `code/vision_analyzer.py`, `code/pipeline.py`
- **OUTPUT:** `multimodal_evidence/verification/verifier.py`, `multimodal_evidence/multimodal/pipeline.py`.
- **VERIFY:** Import test of public functions in `__init__.py`.

### Task 6: CLI Implementation
- **Agent:** backend-specialist
- **Priority:** P2
- **Dependencies:** Task 5
- **INPUT:** CLI design requirements
- **OUTPUT:** `multimodal_evidence/cli.py`
- **VERIFY:** Run `python -m multimodal_evidence.cli --help`

### Task 7: Backward Compatibility
- **Agent:** backend-specialist
- **Priority:** P2
- **Dependencies:** Task 6
- **INPUT:** Existing `code/` pipeline files
- **OUTPUT:** Refactored `code/` imports pointing to the SDK package
- **VERIFY:** Run `python code/evaluation/main.py --compare` and confirm it succeeds.

### Task 8: Publishing Configuration
- **Agent:** devops-engineer
- **Priority:** P3
- **Dependencies:** Task 7
- **INPUT:** Packaging templates
- **OUTPUT:** `pyproject.toml`, `README.md`, `LICENSE`, `CHANGELOG.md`, `.github/workflows/publish.yml`
- **VERIFY:** Run `pip install -e .` and verify the package installs correctly.

## Phase X: Verification
- [ ] Run `python code/evaluation/main.py --compare` to verify accuracy.
- [ ] Test the `evidence` CLI tool.
- [ ] Ensure local package install works via `pip install -e .`.
