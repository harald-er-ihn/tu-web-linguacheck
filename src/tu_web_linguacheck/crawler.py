"""BFS-Verwaltung und Orchestrierung kontrollierter HTML-Crawls."""

import time
from collections import deque
from collections.abc import Callable, Sequence
from urllib.error import URLError
from xml.etree import ElementTree

from tu_web_linguacheck.config import CrawlConfig
from tu_web_linguacheck.html_content import TextBlock, extract_page_content
from tu_web_linguacheck.http import fetch_html, fetch_xml
from tu_web_linguacheck.models import CrawlCandidate, CrawledPage
from tu_web_linguacheck.page_links import find_crawlable_page_links
from tu_web_linguacheck.sitemap import parse_sitemap
from tu_web_linguacheck.urls import (
    is_url_under_start_path,
    prepare_crawl_url,
)


class CrawlQueue:
    """Verwaltet eindeutige Crawl-Kandidaten in BFS-Reihenfolge."""

    def __init__(self, *, start_url: str, max_depth: int) -> None:
        self._candidates = deque([CrawlCandidate(url=start_url, depth=0)])
        self._seen_urls = {start_url}
        self._max_depth = max_depth

    def pop(self) -> CrawlCandidate | None:
        """Entnimmt den nächsten Kandidaten in FIFO-Reihenfolge."""
        if not self._candidates:
            return None

        return self._candidates.popleft()

    def add_start_urls(self, urls: Sequence[str]) -> None:
        """Fügt eindeutige zusätzliche Start-URLs mit Tiefe null ein."""
        for url in urls:
            if url in self._seen_urls:
                continue

            self._seen_urls.add(url)
            self._candidates.append(CrawlCandidate(url=url, depth=0))

    def add_children(
        self,
        *,
        parent: CrawlCandidate,
        urls: Sequence[str],
    ) -> None:
        """Fügt neue Kinder eines Kandidaten bis zur maximalen Tiefe ein."""
        if parent.depth >= self._max_depth:
            return

        child_depth = parent.depth + 1

        for url in urls:
            if url in self._seen_urls:
                continue

            self._seen_urls.add(url)
            self._candidates.append(
                CrawlCandidate(
                    url=url,
                    depth=child_depth,
                )
            )


def _find_sitemap_page_urls(config: CrawlConfig) -> list[str]:
    """Liest crawlbare Seiten-URLs aus konfigurierten XML-Sitemaps."""
    pending_sitemaps = deque(config.sitemap_urls)
    seen_sitemaps: set[str] = set()
    page_urls: list[str] = []

    while pending_sitemaps:
        sitemap_url = pending_sitemaps.popleft()

        if sitemap_url in seen_sitemaps:
            continue

        seen_sitemaps.add(sitemap_url)

        try:
            xml = fetch_xml(sitemap_url, config.allowed_domains)
            sitemap_page_urls, child_sitemaps = parse_sitemap(xml)
        except (ElementTree.ParseError, TimeoutError, URLError, ValueError):
            continue

        for url in sitemap_page_urls:
            prepared_url = prepare_crawl_url(url, config)

            if prepared_url is not None:
                page_urls.append(prepared_url)

        pending_sitemaps.extend(child_sitemaps)

    return page_urls


def _filter_urls_by_start_path(
    urls: Sequence[str],
    *,
    start_url: str,
    stay_under_start_path: bool,
) -> list[str]:
    """Filtert URLs optional auf den Startpfad und dessen Unterpfade."""
    if not stay_under_start_path:
        return list(urls)

    return [url for url in urls if is_url_under_start_path(url, start_url)]


# pylint: disable=too-many-arguments
def crawl_html_pages(
    *,
    start_url: str,
    config: CrawlConfig,
    stay_under_start_path: bool = False,
    additional_start_urls: Sequence[str] = (),
    fetch_page: Callable[[str], str],
    sleep: Callable[[float], None],
    on_progress: Callable[[int, CrawlCandidate], None] | None = None,
    on_error: Callable[[CrawlCandidate, Exception], None] | None = None,
) -> list[CrawlCandidate]:
    """Crawlt HTML-Seiten kontrolliert mit injiziertem Abruf und Rate-Limit."""
    prepared_start_url = prepare_crawl_url(start_url, config)

    if prepared_start_url is None:
        return []

    queue = CrawlQueue(
        start_url=prepared_start_url,
        max_depth=config.max_depth,
    )
    queue.add_start_urls(
        _filter_urls_by_start_path(
            additional_start_urls,
            start_url=prepared_start_url,
            stay_under_start_path=stay_under_start_path,
        )
    )
    processed_candidates: list[CrawlCandidate] = []

    while len(processed_candidates) < config.max_pages:
        candidate = queue.pop()

        if candidate is None:
            break

        if processed_candidates:
            sleep(1 / config.requests_per_second)
        if on_progress is not None:
            on_progress(len(processed_candidates) + 1, candidate)
        try:
            html = fetch_page(candidate.url)
        except (TimeoutError, URLError) as error:
            if on_error is not None:
                on_error(candidate, error)
            continue

        processed_candidates.append(candidate)

        queue.add_children(
            parent=candidate,
            urls=_filter_urls_by_start_path(
                find_crawlable_page_links(candidate.url, html, config),
                start_url=prepared_start_url,
                stay_under_start_path=stay_under_start_path,
            ),
        )

    return processed_candidates


def crawl_site(
    *,
    start_url: str,
    config: CrawlConfig,
) -> list[CrawlCandidate]:
    """Crawlt HTML-Seiten mit sicherem lokalem HTTP-Abruf."""
    return crawl_html_pages(
        start_url=start_url,
        config=config,
        additional_start_urls=_find_sitemap_page_urls(config),
        fetch_page=lambda url: fetch_html(url, config.allowed_domains),
        sleep=time.sleep,
    )


def crawl_pages_with_content(
    *,
    start_url: str,
    config: CrawlConfig,
    stay_under_start_path: bool = False,
    on_progress: Callable[[int, CrawlCandidate], None] | None = None,
    on_error: Callable[[CrawlCandidate, Exception], None] | None = None,
) -> list[CrawledPage]:
    """Crawlt Seiten und gibt ihre einmalig extrahierten Inhalte zurück."""
    extracted_content: dict[str, tuple[str, str, tuple[TextBlock, ...], str]] = {}

    def fetch_page(url: str) -> str:
        html = fetch_html(url, config.allowed_domains)
        page_content = extract_page_content(html)
        extracted_content[url] = (
            page_content.title,
            page_content.text,
            page_content.blocks,
            html,
        )
        return html

    candidates = crawl_html_pages(
        start_url=start_url,
        config=config,
        stay_under_start_path=stay_under_start_path,
        additional_start_urls=_find_sitemap_page_urls(config),
        fetch_page=fetch_page,
        sleep=time.sleep,
        on_progress=on_progress,
        on_error=on_error,
    )

    return [
        CrawledPage(
            url=candidate.url,
            depth=candidate.depth,
            title=extracted_content[candidate.url][0],
            text=extracted_content[candidate.url][1],
            blocks=extracted_content[candidate.url][2],
            html=extracted_content[candidate.url][3],
        )
        for candidate in candidates
    ]
