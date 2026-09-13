"""Extraktion sichtbarer Inhalte aus HTML-Dokumenten."""

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup, NavigableString, Tag

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


def _normalize_text(text: str) -> str:
    """Normalisiert Leerraum und Leerzeichen vor Satzzeichen."""
    text = " ".join(text.split())

    return re.sub(r"\s+([,.;:!?])", r"\1", text)


def _normalize_block_text(block: Tag) -> str:
    """Extrahiert und normalisiert den sichtbaren Text eines HTML-Blocks."""
    return _normalize_text(block.get_text(" ", strip=True))


def _get_html_language(block: Tag) -> str | None:
    """Ermittelt die am Block oder einem Vorfahren gesetzte HTML-Sprache."""
    element: Tag | BeautifulSoup | None = block

    while isinstance(element, Tag):
        language = element.get("lang")
        if isinstance(language, str) and language:
            return language
        element = element.parent

    return None


def _extract_block_segments(block: Tag) -> tuple[TextBlock, ...]:
    """Teilt einen Block an seinen effektiven HTML-Sprachwechseln auf."""
    segments: list[TextBlock] = []

    def append_text(text: str, language: str | None) -> None:
        normalized_text = _normalize_text(text)

        if not normalized_text:
            return

        if segments and segments[-1].language == language:
            previous = segments[-1]
            segments[-1] = TextBlock(
                text=_normalize_text(f"{previous.text} {normalized_text}"),
                language=language,
            )
            return

        segments.append(TextBlock(text=normalized_text, language=language))

    def visit(element: Tag, language: str | None) -> None:
        for child in element.children:
            if isinstance(child, NavigableString):
                append_text(str(child), language)
            elif isinstance(child, Tag):
                child_language = child.get("lang")
                effective_language = (
                    child_language
                    if isinstance(child_language, str) and child_language
                    else language
                )
                visit(child, effective_language)

    visit(block, _get_html_language(block))

    return tuple(segments)


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
        segment for block in blocks for segment in _extract_block_segments(block)
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
