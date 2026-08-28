#!/usr/bin/env bash
set -euo pipefail

LANGUAGETOOL_HOME="${LANGUAGETOOL_HOME:-${XDG_DATA_HOME:-"$HOME/.local/share"}/languagetool/LanguageTool-6.6}"
LANGUAGETOOL_PORT="${LANGUAGETOOL_PORT:-8081}"
SERVER_JAR="$LANGUAGETOOL_HOME/languagetool-server.jar"
LOG_FILE="data/languagetool-server.log"

usage() {
    printf 'Verwendung: %s [--verbose]\n' "$(basename "$0")"
    printf '\n'
    printf 'Startet den lokalen LanguageTool-Server auf Port %s.\n' \
        "$LANGUAGETOOL_PORT"
    printf '\n'
    printf '  --verbose  Server im Vordergrund mit Protokollausgabe starten\n'
}

if [[ "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

if [[ -n "${1:-}" && "${1:-}" != "--verbose" ]]; then
    usage >&2
    exit 2
fi

if [[ ! -f "$SERVER_JAR" ]]; then
    printf 'LanguageTool-Server-JAR nicht gefunden: %s\n' "$SERVER_JAR" >&2
    printf 'Setze bei Bedarf LANGUAGETOOL_HOME auf das LanguageTool-Verzeichnis.\n' >&2
    exit 1
fi

if ss -ltn "sport = :$LANGUAGETOOL_PORT" | grep -q LISTEN; then
    printf 'Port %s wird bereits verwendet.\n' "$LANGUAGETOOL_PORT" >&2
    exit 1
fi

if [[ "${1:-}" == "--verbose" ]]; then
    exec java -cp "$SERVER_JAR" org.languagetool.server.HTTPServer \
        --port "$LANGUAGETOOL_PORT"
fi

mkdir -p "$(dirname "$LOG_FILE")"

nohup java -cp "$SERVER_JAR" org.languagetool.server.HTTPServer \
    --port "$LANGUAGETOOL_PORT" >"$LOG_FILE" 2>&1 &

printf 'LanguageTool-Server im Hintergrund gestartet (PID: %s).\n' "$!"
printf 'Protokoll: %s\n' "$LOG_FILE"
