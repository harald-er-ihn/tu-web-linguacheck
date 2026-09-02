"""Tests für die BFS-Verwaltung kontrollierter Crawl-Kandidaten."""

from tu_web_linguacheck.config import CrawlConfig
from tu_web_linguacheck.crawler import CrawlQueue, crawl_html_pages
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


def test_crawl_html_pages_uses_bfs_order_and_page_limit() -> None:
    """Der simulierte Crawl verarbeitet nur erlaubte Seiten bis zum Limit."""
    config = CrawlConfig(
        allowed_domains=["example.org"],
        max_depth=2,
        max_pages=2,
        requests_per_second=1.0,
        obey_robots_txt=True,
        exclude_patterns=[r"\.(?:pdf|zip)(?:$|[?#])"],
    )
    html_by_url = {
        "https://example.org/": """
        <main>
          <a href="/about/">Über uns</a>
          <a href="/contact/">Kontakt</a>
          <a href="/download/report.pdf">PDF</a>
          <a href="https://external.example/">Extern</a>
        </main>
        """,
        "https://example.org/about/": """
        <main>
          <a href="/about/team/">Team</a>
        </main>
        """,
    }
    fetched_urls: list[str] = []

    def fetch_page(url: str) -> str:
        fetched_urls.append(url)
        return html_by_url[url]

    candidates = crawl_html_pages(
        start_url="https://example.org/",
        config=config,
        fetch_page=fetch_page,
        sleep=lambda _seconds: None,
    )

    assert candidates == [
        CrawlCandidate(url="https://example.org/", depth=0),
        CrawlCandidate(url="https://example.org/about/", depth=1),
    ]
    assert fetched_urls == [
        "https://example.org/",
        "https://example.org/about/",
    ]


def test_crawl_html_pages_waits_between_page_requests() -> None:
    """Der Crawl wartet gemäß requests_per_second zwischen Seitenabrufen."""
    config = CrawlConfig(
        allowed_domains=["example.org"],
        max_depth=1,
        max_pages=2,
        requests_per_second=2.0,
        obey_robots_txt=True,
    )
    html_by_url = {
        "https://example.org/": '<main><a href="/about/">Über uns</a></main>',
        "https://example.org/about/": "<main></main>",
    }
    requested_waits: list[float] = []
    candidates = crawl_html_pages(
        start_url="https://example.org/",
        config=config,
        fetch_page=html_by_url.__getitem__,
        sleep=requested_waits.append,
    )
    assert candidates == [
        CrawlCandidate(url="https://example.org/", depth=0),
        CrawlCandidate(url="https://example.org/about/", depth=1),
    ]
    assert requested_waits == [0.5]
