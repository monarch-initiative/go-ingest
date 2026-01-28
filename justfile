# go-ingest justfile

# Package directory
PKG := "src"

# Explicitly enumerate transforms
TRANSFORMS := "go_annotation"

# List all commands
_default:
    @just --list

# ============== Project Management ==============

# Install dependencies
[group('project management')]
install:
    uv sync --group dev

# ============== Ingest Pipeline ==============

# Full pipeline: download -> transform
[group('ingest')]
run: download transform-all
    @echo "Done!"

# Download source data
[group('ingest')]
download:
    uv run koza download download.yaml

# Run all transforms
[group('ingest')]
transform-all:
    #!/usr/bin/env bash
    set -euo pipefail
    for t in {{TRANSFORMS}}; do
        if [ -n "$t" ]; then
            echo "Transforming $t..."
            uv run koza transform {{PKG}}/$t.yaml
        fi
    done

# Run specific transform
[group('ingest')]
transform NAME:
    uv run koza transform {{PKG}}/{{NAME}}.yaml

# ============== Development ==============

# Run tests
[group('development')]
test:
    uv run pytest

# Run tests with coverage
[group('development')]
test-cov:
    uv run pytest --cov=. --cov-report=term-missing

# Lint code
[group('development')]
lint:
    uv run ruff check .

# Format code
[group('development')]
format:
    uv run ruff format .

# Clean output directory
[group('development')]
clean:
    rm -rf output/
