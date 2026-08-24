"""Tests für URL- und Domain-Regeln."""

import pytest

from tu_web_linguacheck.urls import is_allowed_url


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
