"""Tests für die Projektkonfiguration."""

import pytest
from pydantic import ValidationError

from tu_web_linguacheck.config import CrawlConfig, ProjectConfig


def test_project_config_accepts_minimal_valid_configuration() -> None:
    """Eine minimale gültige Konfiguration wird akzeptiert."""
    config = ProjectConfig(
        profile="generic-de",
        crawl=CrawlConfig(
            allowed_domains=["qi-gong-fuer-alle.de"],
            max_depth=1,
            max_pages=10,
            requests_per_second=1.0,
            obey_robots_txt=True,
        ),
    )

    assert config.profile == "generic-de"
    assert config.crawl.allowed_domains == ["qi-gong-fuer-alle.de"]
    assert config.crawl.max_depth == 1
    assert config.crawl.max_pages == 10
    assert config.crawl.requests_per_second == 1.0
    assert config.crawl.obey_robots_txt is True


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("max_depth", -1),
        ("max_pages", 0),
        ("requests_per_second", 0),
    ],
)
def test_crawl_config_rejects_invalid_limits(field_name: str, value: int) -> None:
    """Negative oder nicht positive Crawl-Grenzen werden abgelehnt."""
    values = {
        "allowed_domains": ["tu-dortmund.de"],
        "max_depth": 1,
        "max_pages": 10,
        "requests_per_second": 1.0,
        "obey_robots_txt": True,
    }
    values[field_name] = value

    with pytest.raises(ValidationError):
        CrawlConfig(**values)


def test_crawl_config_rejects_empty_allowed_domains() -> None:
    """Mindestens eine erlaubte Domain ist erforderlich."""
    with pytest.raises(ValidationError):
        CrawlConfig(
            allowed_domains=[],
            max_depth=1,
            max_pages=10,
            requests_per_second=1.0,
            obey_robots_txt=True,
        )


def test_crawl_config_rejects_unknown_fields() -> None:
    """Unbekannte Konfigurationsfelder werden nicht stillschweigend ignoriert."""
    with pytest.raises(ValidationError):
        CrawlConfig(
            allowed_domains=["tu-dortmund.de"],
            max_depth=1,
            max_pages=10,
            max_page=10,
            requests_per_second=1.0,
            obey_robots_txt=True,
        )
