"""Erkennung von Links zu Sprachvarianten in HTML-Dokumenten."""

from collections.abc import Sequence
from dataclasses import dataclass, replace
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from tu_web_linguacheck.urls import is_allowed_url

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


_DETECTION_METHOD_PRIORITIES = {
    "language_switcher": 1,
    "hreflang": 2,
}


def merge_language_links(language_links: list[LanguageLink]) -> list[LanguageLink]:
    """Führt doppelte Sprachlinks zusammen und bevorzugt verlässlichere Quellen."""
    merged_links: dict[tuple[str, str], LanguageLink] = {}

    for language_link in language_links:
        key = (language_link.href, language_link.language)
        existing_link = merged_links.get(key)

        if existing_link is None:
            merged_links[key] = language_link
            continue

        existing_priority = _DETECTION_METHOD_PRIORITIES.get(
            existing_link.detection_method, 0
        )
        new_priority = _DETECTION_METHOD_PRIORITIES.get(
            language_link.detection_method, 0
        )

        if new_priority > existing_priority:
            merged_links[key] = language_link

    return list(merged_links.values())


def resolve_language_link(base_url: str, language_link: LanguageLink) -> LanguageLink:
    """Löst das Ziel eines Sprachlinks gegen eine Basis-URL auf."""
    return replace(language_link, href=urljoin(base_url, language_link.href))


def find_page_language_links(base_url: str, html: str) -> list[LanguageLink]:
    """Findet, löst auf und priorisiert Sprachlinks einer HTML-Seite."""
    detected_links = find_language_switcher_links(html) + find_hreflang_links(html)
    resolved_links = [
        resolve_language_link(base_url, language_link)
        for language_link in detected_links
    ]

    return merge_language_links(resolved_links)


def filter_allowed_language_links(
    language_links: list[LanguageLink],
    allowed_domains: Sequence[str],
) -> list[LanguageLink]:
    """Behält nur Sprachlinks zu erlaubten Domains."""
    return [
        language_link
        for language_link in language_links
        if is_allowed_url(language_link.href, allowed_domains)
    ]


def find_allowed_page_language_links(
    base_url: str,
    html: str,
    allowed_domains: Sequence[str],
) -> list[LanguageLink]:
    """Findet nur aufgelöste Sprachlinks zu erlaubten Domains."""
    language_links = find_page_language_links(base_url, html)

    return filter_allowed_language_links(language_links, allowed_domains)


def find_language_links_for_language(
    language_links: list[LanguageLink],
    language: str,
) -> list[LanguageLink]:
    """Findet Sprachlinks für einen bestimmten Sprachcode."""
    normalized_language = language.casefold()

    return [
        language_link
        for language_link in language_links
        if language_link.language == normalized_language
    ]
