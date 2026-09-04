"""Tests für die Projektkonfiguration."""

import pytest
from pydantic import ValidationError

from tu_web_linguacheck.config import (
    CrawlConfig,
    ProjectConfig,
    load_project_config,
)


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


def test_load_project_config_reads_valid_yaml(tmp_path) -> None:
    """Eine gültige lokale YAML-Datei wird als Projektkonfiguration geladen."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
profile: generic-de
crawl:
  allowed_domains:
    - qi-gong-fuer-alle.de
  max_depth: 1
  max_pages: 10
  requests_per_second: 1.0
  obey_robots_txt: true
""".lstrip(),
        encoding="utf-8",
    )

    config = load_project_config(config_path)

    assert config.profile == "generic-de"
    assert config.crawl.allowed_domains == ["qi-gong-fuer-alle.de"]
    assert config.crawl.max_depth == 1


def test_project_config_accepts_documented_extended_configuration() -> None:
    """Das dokumentierte vollständige Konfigurationsformat wird akzeptiert."""
    config = ProjectConfig.model_validate(
        {
            "profile": "generic-de",
            "crawl": {
                "allowed_domains": ["example.org"],
                "max_depth": 1,
                "max_pages": 10,
                "requests_per_second": 1.0,
                "obey_robots_txt": True,
                "strip_fragments": True,
                "tracking_parameters": [
                    "fbclid",
                    "gclid",
                    "utm_source",
                ],
                "exclude_patterns": [
                    r"\.(?:pdf|zip)(?:$|[?#])",
                    r"/wp-admin(?:/|$)",
                ],
            },
            "check": {
                "language": "de-DE",
            },
        }
    )

    assert config.crawl.strip_fragments is True
    assert config.crawl.tracking_parameters == [
        "fbclid",
        "gclid",
        "utm_source",
    ]
    assert config.crawl.exclude_patterns == [
        r"\.(?:pdf|zip)(?:$|[?#])",
        r"/wp-admin(?:/|$)",
    ]
    assert config.check.language == "de-DE"


def test_check_config_accepts_ignored_language_tool_rule_ids() -> None:
    """Prüfkonfiguration akzeptiert gezielt ignorierte LanguageTool-Regeln."""
    config = ProjectConfig.model_validate(
        {
            "profile": "generic-de",
            "crawl": {
                "allowed_domains": ["example.org"],
                "max_depth": 1,
                "max_pages": 10,
                "requests_per_second": 1.0,
                "obey_robots_txt": True,
            },
            "check": {
                "language": "de-DE",
                "ignored_rule_ids": [
                    "DE_SIMPLE_REPLACE_QI_GONG",
                ],
            },
        }
    )

    assert config.check.ignored_rule_ids == [
        "DE_SIMPLE_REPLACE_QI_GONG",
    ]


def test_check_config_accepts_ignored_terms() -> None:
    """Prüfkonfiguration akzeptiert gezielt ignorierte Begriffe."""
    config = ProjectConfig.model_validate(
        {
            "profile": "generic-de",
            "crawl": {
                "allowed_domains": ["example.org"],
                "max_depth": 1,
                "max_pages": 10,
                "requests_per_second": 1.0,
                "obey_robots_txt": True,
            },
            "check": {
                "language": "de-DE",
                "ignored_terms": [
                    "TiMana",
                    "Samtosha",
                ],
            },
        }
    )

    assert config.check.ignored_terms == [
        "TiMana",
        "Samtosha",
    ]


def test_crawl_config_accepts_sitemap_urls() -> None:
    """Die Crawl-Konfiguration akzeptiert optionale Sitemap-URLs."""
    config = CrawlConfig(
        allowed_domains=["qi-gong-fuer-alle.de"],
        max_depth=3,
        max_pages=30,
        requests_per_second=1.0,
        obey_robots_txt=True,
        sitemap_urls=["https://qi-gong-fuer-alle.de/sitemap.xml"],
    )

    assert config.sitemap_urls == [
        "https://qi-gong-fuer-alle.de/sitemap.xml",
    ]
