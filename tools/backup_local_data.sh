#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
BACKUP_ROOT="${BACKUP_ROOT:-/media/harald/CloudSpace/Sciebo/tu-web-linguacheck-backup}"
BACKUP_TIMESTAMP="${BACKUP_TIMESTAMP:-$(date +%Y-%m-%d_%H%M%S)}"
BACKUP_NAME="tu-web-linguacheck-$BACKUP_TIMESTAMP"
BACKUP_DIRECTORY="$BACKUP_ROOT/$BACKUP_NAME"

mkdir -p "$BACKUP_DIRECTORY/config" "$BACKUP_DIRECTORY/data" "$BACKUP_DIRECTORY/reports"

shopt -s nullglob
for config_file in "$PROJECT_ROOT"/config/*.local.yaml; do
    cp -a "$config_file" "$BACKUP_DIRECTORY/config/"
done

if [ -d "$PROJECT_ROOT/data" ]; then
    cp -a "$PROJECT_ROOT/data/." "$BACKUP_DIRECTORY/data/"
fi

if [ -d "$PROJECT_ROOT/reports" ]; then
    cp -a "$PROJECT_ROOT/reports/." "$BACKUP_DIRECTORY/reports/"
fi

mapfile -t backup_directories < <(
    find "$BACKUP_ROOT" -maxdepth 1 -mindepth 1 -type d \
        -name 'tu-web-linguacheck-*' -printf '%f\n' | sort -r
)

for backup_name in "${backup_directories[@]:2}"; do
    rm -rf "$BACKUP_ROOT/$backup_name"
done

printf 'Backup erstellt: %s\n' "$BACKUP_DIRECTORY"
