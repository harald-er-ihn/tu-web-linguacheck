"""BFS-Verwaltung für kontrollierte Crawl-Kandidaten."""

from collections import deque
from collections.abc import Sequence

from tu_web_linguacheck.models import CrawlCandidate


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
