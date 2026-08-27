"""Client für einen ausschließlich lokal erreichbaren LanguageTool-Server."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

LANGUAGETOOL_CHECK_URL = "http://127.0.0.1:8081/v2/check"
DEFAULT_TIMEOUT_SECONDS = 10.0


class LanguageToolUnavailableError(RuntimeError):
    """Der ausschließlich lokale LanguageTool-Dienst ist nicht erreichbar."""


@dataclass(frozen=True)
class LanguageToolMatch:
    """Ein von LanguageTool gemeldeter Textfund."""

    message: str
    offset: int
    length: int
    rule_id: str
    replacements: tuple[str, ...]


# pylint: disable=too-few-public-methods
class LanguageToolClient:
    """Prüft Texte mit einem lokalen LanguageTool-Server."""

    def check(self, *, text: str, language: str) -> list[LanguageToolMatch]:
        """Sendet Text und Sprachcode an den lokalen Prüfendpunkt."""
        request_data = urlencode(
            {
                "text": text,
                "language": language,
            }
        ).encode("utf-8")

        request = Request(
            LANGUAGETOOL_CHECK_URL,
            data=request_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
                payload: dict[str, Any] = json.loads(response.read().decode("utf-8"))
        except URLError as error:
            raise LanguageToolUnavailableError(
                "Der lokale LanguageTool-Server unter 127.0.0.1:8081 ist "
                "nicht erreichbar."
            ) from error

        return [
            LanguageToolMatch(
                message=match["message"],
                offset=match["offset"],
                length=match["length"],
                rule_id=match["rule"]["id"],
                replacements=tuple(
                    replacement["value"] for replacement in match["replacements"]
                ),
            )
            for match in payload["matches"]
        ]
