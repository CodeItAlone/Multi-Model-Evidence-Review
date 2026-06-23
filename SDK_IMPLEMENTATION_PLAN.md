# SDK Implementation Plan: Step-by-Step Migration

This document outlines the step-by-step plan for refactoring the Multi-Modal Evidence Review codebase into a reusable developer SDK (`multimodal-evidence-sdk`).

---

## Migration Steps

### Step 1: Initialize Package Directories
Create the target package directories and boilerplate empty `__init__.py` files to establish the library structure.

*   **Files Affected:**
    *   `[NEW]` `multimodal_evidence/__init__.py`
    *   `[NEW]` `multimodal_evidence/models/__init__.py`
    *   `[NEW]` `multimodal_evidence/retrieval/__init__.py`
    *   `[NEW]` `multimodal_evidence/ranking/__init__.py`
    *   `[NEW]` `multimodal_evidence/verification/__init__.py`
    *   `[NEW]` `multimodal_evidence/multimodal/__init__.py`
    *   `[NEW]` `multimodal_evidence/embeddings/__init__.py`
    *   `[NEW]` `multimodal_evidence/utils/__init__.py`
*   **Risk Level:** Very Low
*   **Breaking Changes:** None.
*   **Rollback Strategy:** Delete the `multimodal_evidence/` folder.

---

### Step 2: Migrate Core Models and Custom Errors
Migrate Pydantic models, schemas, and enums from `code/models.py` into the SDK models directory. Add custom error classes.

*   **Files Affected:**
    *   `[NEW]` `multimodal_evidence/models/claim.py` (Copied from `code/models.py` with modifications)
    *   `[NEW]` `multimodal_evidence/utils/errors.py` (Defines `SDKException` and specialized errors)
*   **Risk Level:** Low
*   **Breaking Changes:** None.
*   **Rollback Strategy:** Delete the created modules.

---

### Step 3: Implement Image Utility & Gemini Client
Migrate local pre-flight checks and Pillow image utilities into `utils/image.py`. Port the async rate-limited `GeminiClient` into the `multimodal` module, upgrading it to accept bytes directly rather than requiring file path resolutions.

*   **Files Affected:**
    *   `[NEW]` `multimodal_evidence/utils/image.py` (Decoupled image verification and loader)
    *   `[NEW]` `multimodal_evidence/multimodal/client.py` (Gemini API wrapper)
*   **Risk Level:** Medium
*   **Breaking Changes:** None.
*   **Rollback Strategy:** Delete files.

---

### Step 4: Port Search, Retrieval, and Ranking Engines
Extract CSV parse logic, requirements indexing, and risk flag ranking/guardrail rules. Allow requirements and history to be passed dynamically as in-memory data structures.

*   **Files Affected:**
    *   `[NEW]` `multimodal_evidence/retrieval/search.py`
    *   `[NEW]` `multimodal_evidence/ranking/ranker.py`
*   **Risk Level:** Medium
*   **Breaking Changes:** None.
*   **Rollback Strategy:** Revert file additions.

---

### Step 5: Implement High-Level Verification APIs
Build the `verify_claim` orchestrator in `verification/verifier.py` and register all public methods in the root `__init__.py`.

*   **Files Affected:**
    *   `[NEW]` `multimodal_evidence/verification/verifier.py`
    *   `[NEW]` `multimodal_evidence/multimodal/pipeline.py` (Batch processing pipeline class)
    *   `[MODIFY]` `multimodal_evidence/__init__.py` (Expose public functions)
*   **Risk Level:** Medium
*   **Breaking Changes:** None.
*   **Rollback Strategy:** Revert file additions.

---

### Step 6: Refactor original code to consume the SDK
Refactor imports inside the original `code/` folder so that it imports and uses the new `multimodal_evidence` package. This acts as a backward compatibility gate. We will run the evaluation runner to prove accuracy remains identical.

*   **Files Affected:**
    *   `[MODIFY]` `code/models.py` (Point imports to SDK models)
    *   `[MODIFY]` `code/gemini_client.py` (Reference SDK Client)
    *   `[MODIFY]` `code/image_validator.py` (Reference SDK Image Utils)
    *   `[MODIFY]` `code/post_processor.py` (Reference SDK Ranker)
    *   `[MODIFY]` `code/vision_analyzer.py` (Reference SDK Verifier)
    *   `[MODIFY]` `code/pipeline.py` (Reference SDK pipeline orchestration)
*   **Risk Level:** High
*   **Breaking Changes:** Modifies active legacy code; potential run time failures if types differ.
*   **Rollback Strategy:** Restore `code/` files from Git repository checkout.

---

### Step 7: CLI, Packaging, and Publishing Setup
Create the CLI entry point, pyproject.toml packaging configurations, readme documentation, and GHA publish scripts.

*   **Files Affected:**
    *   `[NEW]` `multimodal_evidence/cli.py` (CLI entry point implementation)
    *   `[NEW]` `pyproject.toml` (Setuptools / build metadata)
    *   `[NEW]` `README.md` (Developer instructions)
    *   `[NEW]` `LICENSE` (MIT License)
    *   `[NEW]` `CHANGELOG.md`
    *   `[NEW]` `.github/workflows/publish.yml`
*   **Risk Level:** Low
*   **Breaking Changes:** None.
*   **Rollback Strategy:** Delete new config files.
