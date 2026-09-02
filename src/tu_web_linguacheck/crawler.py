"""BFS-Verwaltung und Orchestrierung kontrollierter HTML-Crawls."""

import time
from collections import deque
from collections.abc import Callable, Sequence

from tu_web_linguacheck.config import CrawlConfig
from tu_web_linguacheck.http import fetch_html
from tu_web_linguacheck.models import CrawlCandidate
from tu_web_linguacheck.page_links import find_crawlable_page_links
from tu_web_linguacheck.urls import prepare_crawl_url


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


def crawl_html_pages(
    *,
    start_url: str,
    config: CrawlConfig,
    fetch_page: Callable[[str], str],
    sleep: Callable[[float], None],
) -> list[CrawlCandidate]:
    """Crawlt HTML-Seiten kontrolliert mit injiziertem Abruf und Rate-Limit."""
    prepared_start_url = prepare_crawl_url(start_url, config)

    if prepared_start_url is None:
        return []

    queue = CrawlQueue(
        start_url=prepared_start_url,
        max_depth=config.max_depth,
    )
    processed_candidates: list[CrawlCandidate] = []

    while len(processed_candidates) < config.max_pages:
        candidate = queue.pop()

        if candidate is None:
            break

        if processed_candidates:
            sleep(1 / config.requests_per_second)
        html = fetch_page(candidate.url)
        processed_candidates.append(candidate)

        queue.add_children(
            parent=candidate,
            urls=find_crawlable_page_links(
                candidate.url,
                html,
                config,
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
        fetch_page=lambda url: fetch_html(url, config.allowed_domains),
        sleep=time.sleep,
    )
