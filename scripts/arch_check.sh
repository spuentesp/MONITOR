#!/usr/bin/env bash
set -euo pipefail

echo "Running Ruff..."
ruff check .

echo "Running tests..."
pytest -q

if ! command -v lint-imports >/dev/null 2>&1; then
  echo "import-linter (lint-imports) not found. Install with: pip install import-linter"
  exit 1
fi

echo "Running Import Linter..."
lint-imports --config importlinter.ini

echo "All checks passed."
