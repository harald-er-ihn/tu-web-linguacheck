#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_FILE="$PROJECT_ROOT/docs/architecture.dot"
OUTPUT_FILE="$PROJECT_ROOT/docs/images/architecture.svg"

if ! command -v dot >/dev/null 2>&1; then
    printf 'Graphviz-Programm "dot" wurde nicht gefunden.\n' >&2
    exit 1
fi

mkdir -p "$(dirname "$OUTPUT_FILE")"
dot -Tsvg "$SOURCE_FILE" -o "$OUTPUT_FILE"

printf 'Architekturdiagramm erzeugt: %s\n' "$OUTPUT_FILE"
