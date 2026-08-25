"""Hilfsfunktionen für lokale HTTP-Antworten."""


def is_html_content_type(content_type: str) -> bool:
    """Prüft, ob ein Content-Type eine HTML-Antwort bezeichnet."""
    media_type = content_type.split(";", maxsplit=1)[0].strip().casefold()

    return media_type == "text/html"
