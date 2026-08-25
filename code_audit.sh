#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pylint src tests
git diff --check
git diff
git status --short
