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
class PageContent:
    """Extrahierter Titel und sichtbarer Text einer HTML-Seite."""

    title: str
    text: str


def _normalize_block_text(block: Tag) -> str:
    """Extrahiert und normalisiert den sichtbaren Text eines HTML-Blocks."""
    text = block.get_text(" ", strip=True)

    return re.sub(r"\s+([,.;:!?])", r"\1", text)


def _extract_visible_text(content_element: Tag | BeautifulSoup) -> str:
    """Extrahiert sichtbaren Text mit Zeilenumbrüchen zwischen Textblöcken."""
    blocks = [
        block
        for block in content_element.find_all(_BLOCK_TAGS)
        if not block.find(_BLOCK_TAGS)
    ]
    block_texts = [
        _normalize_block_text(block) for block in blocks if _normalize_block_text(block)
    ]

    if block_texts:
        return "\n".join(block_texts)

    return content_element.get_text(" ", strip=True)


def extract_page_content(html: str) -> PageContent:
    """Extrahiert Seitentitel und sichtbaren Hauptinhalt aus HTML."""
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.get_text(" ", strip=True) if soup.title is not None else ""
    content_element = soup.find("main") or soup.body or soup

    for element in content_element.find_all(["nav", "footer", "script", "style"]):
        element.decompose()

    text = _extract_visible_text(content_element)

    return PageContent(title=title, text=text)
