"""Tests für die BFS-Verwaltung kontrollierter Crawl-Kandidaten."""
# pylint: disable=duplicate-code,too-many-arguments

from tu_web_linguacheck.config import CrawlConfig
from tu_web_linguacheck.crawler import (
    CrawlQueue,
    crawl_html_pages,
    crawl_pages_with_content,
    crawl_site,
)
from tu_web_linguacheck.html_content import TextBlock
from tu_web_linguacheck.models import CrawlCandidate, CrawledPage


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


def test_crawl_site_delegates_to_secure_fetch_and_orchestrator(
    monkeypatch,
) -> None:
    """Der Live-Adapter nutzt sicheren Abruf und delegiert die Crawl-Steuerung."""
    config = CrawlConfig(
        allowed_domains=["example.org"],
        max_depth=1,
        max_pages=10,
        requests_per_second=1.0,
        obey_robots_txt=True,
    )
    expected_candidates = [
        CrawlCandidate(
            url="https://example.org/",
            depth=0,
        )
    ]

    def fake_fetch_html(url: str, allowed_domains: list[str]) -> str:
        assert url == "https://example.org/"
        assert allowed_domains == ["example.org"]
        return "<main></main>"

    def fake_sleep(_seconds: float) -> None:
        return None

    def fake_crawl_html_pages(
        *,
        start_url: str,
        config: CrawlConfig,
        fetch_page,
        sleep,
        on_progress=None,
    ) -> list[CrawlCandidate]:
        assert start_url == "https://example.org/"
        assert config.max_pages == 10
        assert on_progress is None
        assert fetch_page(start_url) == "<main></main>"
        assert sleep is fake_sleep
        return expected_candidates

    monkeypatch.setattr(
        "tu_web_linguacheck.crawler.fetch_html",
        fake_fetch_html,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.crawler.time.sleep",
        fake_sleep,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.crawler.crawl_html_pages",
        fake_crawl_html_pages,
    )

    assert (
        crawl_site(
            start_url="https://example.org/",
            config=config,
        )
        == expected_candidates
    )


def test_crawl_pages_with_content_returns_extracted_crawl_results(
    monkeypatch,
) -> None:
    """Der Content-Crawl verbindet Kandidaten mit einmalig abgerufenen Inhalten."""
    config = CrawlConfig(
        allowed_domains=["example.org"],
        max_depth=0,
        max_pages=1,
        requests_per_second=1.0,
        obey_robots_txt=True,
    )

    def fake_fetch_html(url: str, allowed_domains: list[str]) -> str:
        assert url == "https://example.org/"
        assert allowed_domains == ["example.org"]
        return (
            '<html lang="de"><title>Testseite</title><main>'
            '<p>Ein Test.</p><p lang="en">English text.</p>'
            "</main></html>"
        )

    def fake_crawl_html_pages(
        *,
        start_url: str,
        config: CrawlConfig,
        fetch_page,
        sleep,
        on_progress,
        on_error,
    ) -> list[CrawlCandidate]:
        assert start_url == "https://example.org/"
        assert config.max_pages == 1
        assert on_progress is None
        assert on_error is None
        assert fetch_page(start_url) == (
            '<html lang="de"><title>Testseite</title><main>'
            '<p>Ein Test.</p><p lang="en">English text.</p>'
            "</main></html>"
        )
        assert sleep is not None

        return [CrawlCandidate(url=start_url, depth=0)]

    monkeypatch.setattr(
        "tu_web_linguacheck.crawler.fetch_html",
        fake_fetch_html,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.crawler.crawl_html_pages",
        fake_crawl_html_pages,
    )

    pages = crawl_pages_with_content(
        start_url="https://example.org/",
        config=config,
    )

    assert pages == [
        CrawledPage(
            url="https://example.org/",
            depth=0,
            title="Testseite",
            text="Ein Test.\nEnglish text.",
            blocks=(
                TextBlock(text="Ein Test.", language="de"),
                TextBlock(text="English text.", language="en"),
            ),
        )
    ]


def test_crawl_html_pages_reports_progress_before_each_request() -> None:
    """Der Crawl meldet vor jedem Seitenabruf Nummer und Kandidat."""
    config = CrawlConfig(
        allowed_domains=["example.org"],
        max_depth=1,
        max_pages=2,
        requests_per_second=1.0,
        obey_robots_txt=True,
    )
    html_by_url = {
        "https://example.org/": '<main><a href="/about/">Über uns</a></main>',
        "https://example.org/about/": "<main>Über uns</main>",
    }
    progress_events: list[tuple[int, CrawlCandidate]] = []

    crawl_html_pages(
        start_url="https://example.org/",
        config=config,
        fetch_page=html_by_url.__getitem__,
        sleep=lambda _seconds: None,
        on_progress=lambda number, candidate: progress_events.append(
            (number, candidate)
        ),
    )

    assert progress_events == [
        (1, CrawlCandidate(url="https://example.org/", depth=0)),
        (2, CrawlCandidate(url="https://example.org/about/", depth=1)),
    ]


def test_crawl_pages_with_content_forwards_progress_callback(monkeypatch) -> None:
    """Der Content-Crawl leitet Fortschrittsmeldungen an den HTML-Crawl weiter."""
    config = CrawlConfig(
        allowed_domains=["example.org"],
        max_depth=0,
        max_pages=1,
        requests_per_second=1.0,
        obey_robots_txt=True,
    )
    reported_events: list[tuple[int, CrawlCandidate]] = []
    expected_candidate = CrawlCandidate(url="https://example.org/", depth=0)

    def fake_crawl_html_pages(
        *,
        start_url,
        config,
        fetch_page,
        sleep,
        on_progress,
        on_error,
    ):
        assert start_url == "https://example.org/"
        assert config.max_pages == 1
        assert on_error is None
        assert fetch_page(start_url) == "<main>Ein Test.</main>"
        assert sleep is not None
        assert on_progress is not None
        on_progress(1, expected_candidate)

        return [expected_candidate]

    monkeypatch.setattr(
        "tu_web_linguacheck.crawler.fetch_html",
        lambda _url, _domains: "<main>Ein Test.</main>",
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.crawler.crawl_html_pages",
        fake_crawl_html_pages,
    )

    crawl_pages_with_content(
        start_url="https://example.org/",
        config=config,
        on_progress=lambda number, candidate: reported_events.append(
            (number, candidate)
        ),
    )

    assert reported_events == [(1, expected_candidate)]


def test_crawl_html_pages_continues_after_timeout_and_reports_error() -> None:
    """Der Crawl überspringt Timeouts und verarbeitet weitere Kandidaten."""
    config = CrawlConfig(
        allowed_domains=["example.org"],
        max_depth=1,
        max_pages=3,
        requests_per_second=1.0,
        obey_robots_txt=True,
    )
    html_by_url = {
        "https://example.org/": (
            '<main><a href="/slow/">Langsam</a><a href="/about/">Über uns</a></main>'
        ),
        "https://example.org/about/": "<main>Über uns</main>",
    }
    reported_errors: list[tuple[CrawlCandidate, Exception]] = []

    def fetch_page(url: str) -> str:
        if url == "https://example.org/slow/":
            raise TimeoutError("Zeitüberschreitung")

        return html_by_url[url]

    candidates = crawl_html_pages(
        start_url="https://example.org/",
        config=config,
        fetch_page=fetch_page,
        sleep=lambda _seconds: None,
        on_error=lambda candidate, error: reported_errors.append((candidate, error)),
    )

    assert candidates == [
        CrawlCandidate(url="https://example.org/", depth=0),
        CrawlCandidate(url="https://example.org/about/", depth=1),
    ]
    assert len(reported_errors) == 1
    candidate, error = reported_errors[0]
    assert candidate == CrawlCandidate(
        url="https://example.org/slow/",
        depth=1,
    )
    assert isinstance(error, TimeoutError)
    assert str(error) == "Zeitüberschreitung"


def test_crawl_pages_with_content_forwards_error_callback(monkeypatch) -> None:
    """Der Content-Crawl leitet Abruffehler an den HTML-Crawl weiter."""
    config = CrawlConfig(
        allowed_domains=["example.org"],
        max_depth=0,
        max_pages=1,
        requests_per_second=1.0,
        obey_robots_txt=True,
    )
    reported_errors: list[tuple[CrawlCandidate, Exception]] = []
    expected_candidate = CrawlCandidate(url="https://example.org/", depth=0)

    def fake_crawl_html_pages(
        *,
        start_url,
        config,
        fetch_page,
        sleep,
        on_progress,
        on_error,
    ):
        assert start_url == "https://example.org/"
        assert config.max_pages == 1
        assert fetch_page(start_url) == "<main>Ein Test.</main>"
        assert sleep is not None
        assert on_progress is None
        assert on_error is not None
        on_error(expected_candidate, TimeoutError("Zeitüberschreitung"))

        return []

    monkeypatch.setattr(
        "tu_web_linguacheck.crawler.fetch_html",
        lambda _url, _domains: "<main>Ein Test.</main>",
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.crawler.crawl_html_pages",
        fake_crawl_html_pages,
    )

    crawl_pages_with_content(
        start_url="https://example.org/",
        config=config,
        on_error=lambda candidate, error: reported_errors.append((candidate, error)),
    )

    assert len(reported_errors) == 1
    candidate, error = reported_errors[0]
    assert candidate == expected_candidate
    assert isinstance(error, TimeoutError)
    assert str(error) == "Zeitüberschreitung"


def test_crawl_html_pages_crawls_additional_start_urls_at_depth_zero() -> None:
    """Zusätzliche Start-URLs werden als unabhängige Tiefe-null-Seiten gecrawlt."""
    config = CrawlConfig(
        allowed_domains=["example.org"],
        max_depth=0,
        max_pages=3,
        requests_per_second=1.0,
        obey_robots_txt=True,
    )
    fetched_urls: list[str] = []

    def fetch_page(url: str) -> str:
        fetched_urls.append(url)
        return "<main></main>"

    candidates = crawl_html_pages(
        start_url="https://example.org/",
        additional_start_urls=[
            "https://example.org/aus-sitemap/",
            "https://example.org/weitere-seite/",
        ],
        config=config,
        fetch_page=fetch_page,
        sleep=lambda _seconds: None,
    )

    assert candidates == [
        CrawlCandidate(url="https://example.org/", depth=0),
        CrawlCandidate(url="https://example.org/aus-sitemap/", depth=0),
        CrawlCandidate(url="https://example.org/weitere-seite/", depth=0),
    ]
    assert fetched_urls == [
        "https://example.org/",
        "https://example.org/aus-sitemap/",
        "https://example.org/weitere-seite/",
    ]
