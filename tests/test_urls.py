"""Tests für URL- und Domain-Regeln."""

import pytest

from tu_web_linguacheck.config import CrawlConfig
from tu_web_linguacheck.urls import (
    is_allowed_url,
    is_url_under_start_path,
    normalize_url,
    prepare_crawl_url,
    should_crawl_url,
)


@pytest.mark.parametrize(
    "url",
    [
        "https://tu-dortmund.de/",
        "https://www.tu-dortmund.de/",
        "https://dobus.zhb.tu-dortmund.de/",
        "https://stabsstelle-cfv.tu-dortmund.de/vielfalt/",
        "https://ub.tu-dortmund.de/",
    ],
)
def test_root_domain_allows_tu_dortmund_subdomains(url: str) -> None:
    """Die Stamm-Domain erlaubt sich selbst und ihre Subdomains."""
    assert is_allowed_url(url, ["tu-dortmund.de"])


@pytest.mark.parametrize(
    "url",
    [
        "https://tu-dortmund.de.example.org/",
        "https://evil-tu-dortmund.de/",
        "https://example.org/",
        "https://example.org/?redirect=https://tu-dortmund.de/",
    ],
)
def test_root_domain_does_not_allow_similar_foreign_domains(url: str) -> None:
    """Ähnlich aussehende fremde Domains bleiben ausgeschlossen."""
    assert not is_allowed_url(url, ["tu-dortmund.de"])


@pytest.mark.parametrize(
    "url",
    [
        "ftp://tu-dortmund.de/file.txt",
        "mailto:info@tu-dortmund.de",
        "not-a-url",
    ],
)
def test_only_http_and_https_urls_are_allowed(url: str) -> None:
    """Nur HTTP- und HTTPS-URLs können zum Crawl zugelassen werden."""
    assert not is_allowed_url(url, ["tu-dortmund.de"])


def test_normalize_url_removes_fragment_and_tracking_parameters() -> None:
    """Fragmente und konfigurierte Tracking-Parameter werden entfernt."""

    normalized_url = normalize_url(
        "https://Example.org/page/?article=42&utm_source=newsletter&fbclid=abc#section",
        tracking_parameters=["utm_source", "fbclid"],
    )

    assert normalized_url == "https://example.org/page/?article=42"


def test_normalize_url_keeps_relevant_query_parameters() -> None:
    """Nicht als Tracking markierte Query-Parameter bleiben erhalten."""

    normalized_url = normalize_url(
        "https://example.org/search/?q=sprachpruefung&page=2",
        tracking_parameters=["utm_source", "fbclid"],
    )

    assert normalized_url == "https://example.org/search/?q=sprachpruefung&page=2"


@pytest.mark.parametrize(
    ("url", "expected_url"),
    [
        (
            "http://Example.org:80/page/",
            "http://example.org/page/",
        ),
        (
            "https://Example.org:443/page/",
            "https://example.org/page/",
        ),
        (
            "https://Example.org:8443/page/",
            "https://example.org:8443/page/",
        ),
    ],
)
def test_normalize_url_removes_only_standard_ports(
    url: str,
    expected_url: str,
) -> None:
    """HTTP- und HTTPS-Standardports werden entfernt."""
    assert normalize_url(url, tracking_parameters=[]) == expected_url


@pytest.mark.parametrize(
    "url",
    [
        "https://example.org/seminar.pdf",
        "https://example.org/bild.jpg",
        "https://example.org/download.zip",
        "https://example.org/datei.docx?download=1",
        "https://example.org/video.mp4#start",
        "mailto:info@example.org",
        "ftp://example.org/archive.zip",
    ],
)
def test_should_crawl_url_rejects_non_html_or_non_http_urls(url: str) -> None:
    """Nicht-HTML- und Nicht-HTTP(S)-URLs werden ausgeschlossen."""

    exclude_patterns = [
        r"\.(?:docx?|jpe?g|mp4|pdf|zip)(?:$|[?#])",
    ]

    assert not should_crawl_url(url, exclude_patterns)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.org/",
        "https://example.org/startseite/",
        "https://example.org/veranstaltungen/?page=2",
    ],
)
def test_should_crawl_url_accepts_http_urls_without_excluded_pattern(
    url: str,
) -> None:
    """Zulässige HTTP(S)-URLs ohne Ausschlussmuster bleiben erhalten."""

    exclude_patterns = [
        r"\.(?:docx?|jpe?g|mp4|pdf|zip)(?:$|[?#])",
    ]

    assert should_crawl_url(url, exclude_patterns)


def test_prepare_crawl_url_returns_normalized_allowed_html_url() -> None:
    """Eine erlaubte HTML-URL wird normalisiert für den Crawl zurückgegeben."""
    config = CrawlConfig(
        allowed_domains=["example.org"],
        max_depth=1,
        max_pages=10,
        requests_per_second=1.0,
        obey_robots_txt=True,
        tracking_parameters=["utm_source"],
        exclude_patterns=[r"\.(?:pdf|zip)(?:$|[?#])"],
    )

    prepared_url = prepare_crawl_url(
        "https://Example.org/page/?article=42&utm_source=newsletter#section",
        config,
    )

    assert prepared_url == "https://example.org/page/?article=42"


def test_prepare_crawl_url_rejects_foreign_or_excluded_url() -> None:
    """Fremde Domains und ausgeschlossene Ressourcen werden nicht vorbereitet."""
    config = CrawlConfig(
        allowed_domains=["example.org"],
        max_depth=1,
        max_pages=10,
        requests_per_second=1.0,
        obey_robots_txt=True,
        exclude_patterns=[r"\.(?:pdf|zip)(?:$|[?#])"],
    )

    assert prepare_crawl_url("https://external.example/page/", config) is None
    assert prepare_crawl_url("https://example.org/document.pdf", config) is None


@pytest.mark.parametrize(
    ("url", "start_url", "expected"),
    [
        (
            "https://example.org/familie/newsletter/",
            "https://example.org/familie/newsletter/",
            True,
        ),
        (
            "https://example.org/familie/newsletter/september-2026/",
            "https://example.org/familie/newsletter/",
            True,
        ),
        (
            "https://example.org/familie/",
            "https://example.org/familie/newsletter/",
            False,
        ),
        (
            "https://example.org/familie/aktuelles/",
            "https://example.org/familie/newsletter/",
            False,
        ),
        (
            "https://example.org/familie/newsletter-archiv/",
            "https://example.org/familie/newsletter/",
            False,
        ),
    ],
)
def test_is_url_under_start_path(
    url: str,
    start_url: str,
    expected: bool,
) -> None:
    """Nur die Start-URL und echte Unterpfade bleiben im Startbereich."""
    assert is_url_under_start_path(url, start_url) is expected
