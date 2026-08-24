"""Erkennung von Links zu Sprachvarianten in HTML-Dokumenten."""

from dataclasses import dataclass

from bs4 import BeautifulSoup

_LANGUAGE_BY_LINK_TEXT = {
    "de": "de",
    "deutsch": "de",
    "en": "en",
    "english": "en",
}
_SUPPORTED_LANGUAGE_CODES = {"de", "en"}


@dataclass(frozen=True)
class LanguageLink:
    """Ein erkannter Link zu einer Sprachvariante."""

    href: str
    language: str
    detection_method: str


def find_language_switcher_links(html: str) -> list[LanguageLink]:
    """Findet Links, deren sichtbarer Text einen Sprachumschalter bezeichnet."""
    soup = BeautifulSoup(html, "html.parser")
    language_links: list[LanguageLink] = []

    for link in soup.find_all("a", href=True):
        link_text = link.get_text(" ", strip=True).casefold()
        language = _LANGUAGE_BY_LINK_TEXT.get(link_text)

        if language is not None:
            language_links.append(
                LanguageLink(
                    href=link["href"],
                    language=language,
                    detection_method="language_switcher",
                )
            )

    return language_links


def find_hreflang_links(html: str) -> list[LanguageLink]:
    """Findet deutsche und englische Alternativlinks mit hreflang."""
    soup = BeautifulSoup(html, "html.parser")
    language_links: list[LanguageLink] = []

    for link in soup.find_all("link", href=True):
        relations = {relation.casefold() for relation in link.get("rel", [])}

        if "alternate" not in relations:
            continue

        hreflang = link.get("hreflang", "").casefold()
        language = hreflang.split("-", maxsplit=1)[0]

        if language in _SUPPORTED_LANGUAGE_CODES:
            language_links.append(
                LanguageLink(
                    href=link["href"],
                    language=language,
                    detection_method="hreflang",
                )
            )

    return language_links
