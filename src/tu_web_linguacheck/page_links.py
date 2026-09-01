"""Extraktion allgemeiner Seitenlinks aus dem Hauptinhalt."""

from urllib.parse import urljoin

from bs4 import BeautifulSoup

_IGNORED_LINK_PREFIXES = ("#", "javascript:", "mailto:", "tel:")


def extract_page_links(base_url: str, html: str) -> list[str]:
    """Extrahiert aufgelöste reguläre Links aus einem HTML-Hauptinhalt."""
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main")

    if main is None:
        return []

    return [
        urljoin(base_url, link["href"])
        for link in main.find_all("a", href=True)
        if not link["href"].strip().casefold().startswith(_IGNORED_LINK_PREFIXES)
    ]
