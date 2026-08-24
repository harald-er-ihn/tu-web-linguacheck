"""Erkennung von Links zu Sprachvarianten in HTML-Dokumenten."""

from bs4 import BeautifulSoup

_LANGUAGE_BY_LINK_TEXT = {
    "de": "de",
    "deutsch": "de",
    "en": "en",
    "english": "en",
}
_SUPPORTED_HREFLANG_CODES = {"de", "en"}


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


def find_hreflang_links(html: str) -> list[tuple[str, str]]:
    """Findet deutsche und englische Alternativlinks mit hreflang."""
    soup = BeautifulSoup(html, "html.parser")
    language_links: list[tuple[str, str]] = []

    for link in soup.find_all("link", href=True):
        relations = {relation.casefold() for relation in link.get("rel", [])}

        if "alternate" not in relations:
            continue

        language = link.get("hreflang", "").casefold()

        if language in _SUPPORTED_HREFLANG_CODES:
            language_links.append((link["href"], language))

    return language_links
