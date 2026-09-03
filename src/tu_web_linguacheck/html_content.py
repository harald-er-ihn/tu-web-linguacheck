"""Extraktion sichtbarer Inhalte aus HTML-Dokumenten."""

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag

_BLOCK_TAGS = [
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "p",
    "li",
    "blockquote",
    "pre",
    "td",
    "th",
    "figcaption",
]


@dataclass(frozen=True)
class TextBlock:
    """Ein sichtbarer Textblock mit optionaler HTML-Sprache."""

    text: str
    language: str | None


@dataclass(frozen=True)
class PageContent:
    """Extrahierter Titel und sichtbarer Text einer HTML-Seite."""

    title: str
    text: str
    blocks: tuple[TextBlock, ...] = ()


def _normalize_block_text(block: Tag) -> str:
    """Extrahiert und normalisiert den sichtbaren Text eines HTML-Blocks."""
    text = block.get_text(" ", strip=True)

    return re.sub(r"\s+([,.;:!?])", r"\1", text)


def _get_html_language(block: Tag) -> str | None:
    """Ermittelt die am Block oder einem Vorfahren gesetzte HTML-Sprache."""
    element: Tag | BeautifulSoup | None = block

    while isinstance(element, Tag):
        language = element.get("lang")
        if isinstance(language, str) and language:
            return language
        element = element.parent

    return None


def _extract_visible_blocks(
    content_element: Tag | BeautifulSoup,
) -> tuple[TextBlock, ...]:
    """Extrahiert sichtbare Textblöcke mit ihrer effektiven HTML-Sprache."""
    blocks = [
        block
        for block in content_element.find_all(_BLOCK_TAGS)
        if not block.find(_BLOCK_TAGS)
    ]

    return tuple(
        TextBlock(text=text, language=_get_html_language(block))
        for block in blocks
        if (text := _normalize_block_text(block))
    )


def _extract_visible_text(content_element: Tag | BeautifulSoup) -> str:
    """Extrahiert sichtbaren Text mit Zeilenumbrüchen zwischen Textblöcken."""
    blocks = _extract_visible_blocks(content_element)

    if blocks:
        return "\n".join(block.text for block in blocks)

    return content_element.get_text(" ", strip=True)


def extract_page_content(html: str) -> PageContent:
    """Extrahiert Seitentitel und sichtbaren Hauptinhalt aus HTML."""
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.get_text(" ", strip=True) if soup.title is not None else ""
    content_element = soup.find("main") or soup.body or soup

    for element in content_element.find_all(["nav", "footer", "script", "style"]):
        element.decompose()

    blocks = _extract_visible_blocks(content_element)
    text = "\n".join(block.text for block in blocks)

    if not blocks:
        text = _extract_visible_text(content_element)

    return PageContent(title=title, text=text, blocks=blocks)
