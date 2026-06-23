# PyPI Publishing Guide: `multimodal-evidence-sdk`

This guide explains how to package and release the `multimodal-evidence-sdk` to PyPI.

---

## 1. Prerequisites

Ensure you have the latest versions of `pip`, `build`, and `twine` installed:

```bash
python -m pip install --upgrade pip
pip install build twine
```

---

## 2. Build the Distribution Packages

From the repository root (containing `pyproject.toml`), run the build tool:

```bash
python -m build
```

This compiles your package into source and wheel distribution formats inside the `dist/` directory:
*   `dist/multimodal_evidence_sdk-0.1.0.tar.gz` (Source Archive)
*   `dist/multimodal_evidence_sdk-0.1.0-py3-none-any.whl` (Built Wheel)

---

## 3. Test and Verify the Package

Before uploading to PyPI, you should run a pre-upload validation using `twine check`:

```bash
twine check dist/*
```

To test the installation locally, you can install the wheel file directly:

```bash
pip install dist/multimodal_evidence_sdk-0.1.0-py3-none-any.whl
```

Test running the CLI tool:

```bash
evidence --help
```

---

## 4. Publish to TestPyPI

To make sure everything is configured properly, upload the package to TestPyPI first:

```bash
twine upload --repository testpypi dist/*
```

*   **Username:** `__token__`
*   **Password:** Your TestPyPI API token (begins with `pypi-`)

---

## 5. Publish to PyPI (Production)

Once TestPyPI upload succeeds and the package installs correctly, publish to the main PyPI registry:

```bash
twine upload dist/*
```

*   **Username:** `__token__`
*   **Password:** Your production PyPI API token (begins with `pypi-`)

---

## 6. Automated Publishing via GitHub Actions

The repository includes a GitHub Action workflow under `.github/workflows/publish.yml`.
To trigger it:
1.  Add your PyPI API token to your GitHub repository secrets as `PYPI_API_TOKEN`.
2.  Create and publish a new GitHub Release with a tag matching your version (e.g. `v0.1.0`).
3.  The workflow will automatically run, build, and publish the packages to PyPI.
