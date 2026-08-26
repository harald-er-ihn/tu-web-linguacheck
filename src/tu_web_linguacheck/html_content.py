"""Extraktion sichtbarer Inhalte aus HTML-Dokumenten."""

from dataclasses import dataclass

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class PageContent:
    """Extrahierter Titel und sichtbarer Text einer HTML-Seite."""

    title: str
    text: str


def extract_page_content(html: str) -> PageContent:
    """Extrahiert Seitentitel und sichtbaren Hauptinhalt aus HTML."""
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.get_text(" ", strip=True) if soup.title is not None else ""
    content_element = soup.find("main") or soup.body or soup

    for element in content_element.find_all(["nav", "footer", "script", "style"]):
        element.decompose()

    text = content_element.get_text(" ", strip=True)

    return PageContent(title=title, text=text)
