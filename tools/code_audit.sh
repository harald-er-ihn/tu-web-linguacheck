#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pylint src tests

while IFS= read -r -d '' file; do
    echo "Checking: $file"
    mdl "$file"
done < <(
    find . \
        -path "./.git" -prune -o \
        -path "./.venv" -prune -o \
        -path "./.pytest_cache" -prune -o \
        -type f -name "*.md" -print0
)

git diff --check
git diff
git status --short
