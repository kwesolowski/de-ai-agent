default:
    @just --list

# Install dependencies and pre-commit hooks
setup:
    uv sync
    pre-commit install --hook-type commit-msg

# Run all tests with coverage
test:
    uv run pytest

# Run only fast tests (skip E2E)
test-fast:
    uv run pytest -m "not slow"

# Run pre-commit on all files
lint:
    pre-commit run --all-files

# Run pre-commit verbose (for QA)
pcrafv:
    pre-commit run --all-files --verbose

# Sync dependencies
sync:
    uv sync
