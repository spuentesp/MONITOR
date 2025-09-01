#!/usr/bin/env bash
set -euo pipefail

# Auto-fix linting issues using Ruff (format + check --fix).
# Usage: bash scripts/lint_fix.sh [path...]
# If no paths are provided, defaults to repository root.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
TARGETS=("$@")
if [ ${#TARGETS[@]} -eq 0 ]; then
  TARGETS=("$ROOT_DIR")
fi

echo "[lint] Formatting with ruff format …"
ruff format "${TARGETS[@]}"

echo "[lint] Linting with ruff check --fix …"
ruff check --fix "${TARGETS[@]}"

echo "[lint] Done. To verify without changing files:"
echo "  ruff format --check ${TARGETS[*]}"
echo "  ruff check ${TARGETS[*]}"
