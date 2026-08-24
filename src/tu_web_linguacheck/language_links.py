"""Erkennung von Links zu Sprachvarianten in HTML-Dokumenten."""

from bs4 import BeautifulSoup

_LANGUAGE_BY_LINK_TEXT = {
    "de": "de",
    "deutsch": "de",
    "en": "en",
    "english": "en",
}


def find_language_switcher_links(html: str) -> list[tuple[str, str]]:
    """Findet Links, deren sichtbarer Text einen Sprachumschalter bezeichnet."""
    soup = BeautifulSoup(html, "html.parser")
    language_links: list[tuple[str, str]] = []

    for link in soup.find_all("a", href=True):
        link_text = link.get_text(" ", strip=True).casefold()
        language = _LANGUAGE_BY_LINK_TEXT.get(link_text)

        if language is not None:
            language_links.append((link["href"], language))

    return language_links
