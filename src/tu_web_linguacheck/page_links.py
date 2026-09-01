"""Extraktion allgemeiner Seitenlinks aus dem Hauptinhalt."""

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from tu_web_linguacheck.config import CrawlConfig
from tu_web_linguacheck.urls import prepare_crawl_url

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


def find_crawlable_page_links(
    base_url: str,
    html: str,
    config: CrawlConfig,
) -> list[str]:
    """Findet eindeutige, vorbereitete Crawl-Ziele aus dem Hauptinhalt."""
    crawlable_links: list[str] = []
    seen_links: set[str] = set()

    for link in extract_page_links(base_url, html):
        prepared_link = prepare_crawl_url(link, config)

        if prepared_link is None or prepared_link in seen_links:
            continue

        seen_links.add(prepared_link)
        crawlable_links.append(prepared_link)

    return crawlable_links
