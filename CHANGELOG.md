# Changelog

All notable changes to the Multimodal Evidence SDK project will be documented in this file.

## [0.1.0] - 2026-06-23

### Added
- Created the core SDK structure (`multimodal_evidence`).
- Implemented models package (`models/claim.py`) with Pydantic enums and models.
- Implemented pre-flight Pillow image validators (`utils/image.py`) supporting file paths and bytes.
- Implemented custom SDK exceptions (`utils/errors.py`).
- Implemented `GeminiClient` wrapper (`multimodal/client.py`) with concurrency limit, retry limits, and rate limits.
- Implemented `verify_claim`, `retrieve_evidence`, and `rank_evidence` public APIs.
- Implemented CLI entry point `evidence` with support for verify, search, and rank.
- Integrated legacy pipeline code in `code/` to use the SDK features.
- Configured packaging via `pyproject.toml`.
