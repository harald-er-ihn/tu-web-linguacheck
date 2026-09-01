"""Tests für die BFS-Verwaltung kontrollierter Crawl-Kandidaten."""

from tu_web_linguacheck.crawler import CrawlQueue
from tu_web_linguacheck.models import CrawlCandidate


def test_crawl_queue_uses_fifo_order_and_respects_maximum_depth() -> None:
    """Die Queue verarbeitet eindeutige Kandidaten breitensuchend."""
    queue = CrawlQueue(
        start_url="https://example.org/",
        max_depth=1,
    )

    assert queue.pop() == CrawlCandidate(
        url="https://example.org/",
        depth=0,
    )

    queue.add_children(
        parent=CrawlCandidate(
            url="https://example.org/",
            depth=0,
        ),
        urls=[
            "https://example.org/about/",
            "https://example.org/contact/",
            "https://example.org/about/",
        ],
    )

    assert queue.pop() == CrawlCandidate(
        url="https://example.org/about/",
        depth=1,
    )
    assert queue.pop() == CrawlCandidate(
        url="https://example.org/contact/",
        depth=1,
    )

    queue.add_children(
        parent=CrawlCandidate(
            url="https://example.org/contact/",
            depth=1,
        ),
        urls=["https://example.org/contact/team/"],
    )

    assert queue.pop() is None
