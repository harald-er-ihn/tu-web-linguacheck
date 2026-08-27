#!/usr/bin/env bash
set -euo pipefail

LANGUAGETOOL_HOME="${LANGUAGETOOL_HOME:-${XDG_DATA_HOME:-"$HOME/.local/share"}/languagetool/LanguageTool-6.6}"
LANGUAGETOOL_PORT="${LANGUAGETOOL_PORT:-8081}"
SERVER_JAR="$LANGUAGETOOL_HOME/languagetool-server.jar"

if [[ ! -f "$SERVER_JAR" ]]; then
    printf 'LanguageTool-Server-JAR nicht gefunden: %s\n' "$SERVER_JAR" >&2
    printf 'Setze bei Bedarf LANGUAGETOOL_HOME auf das LanguageTool-Verzeichnis.\n' >&2
    exit 1
fi

exec java -cp "$SERVER_JAR" org.languagetool.server.HTTPServer \
    --port "$LANGUAGETOOL_PORT"
