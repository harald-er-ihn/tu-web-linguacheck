"""Modelle und Laden für die lokale Projektkonfiguration."""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field


class CrawlConfig(BaseModel):
    """Grenzen und Sicherheitsvorgaben für einen Crawl."""

    model_config = ConfigDict(extra="forbid")

    allowed_domains: list[str] = Field(min_length=1)
    max_depth: int = Field(ge=0)
    max_pages: int = Field(ge=1)
    requests_per_second: float = Field(gt=0)
    obey_robots_txt: bool
    strip_fragments: bool = True
    tracking_parameters: list[str] = Field(default_factory=list)
    exclude_patterns: list[str] = Field(default_factory=list)
    sitemap_urls: list[str] = Field(default_factory=list)


class CheckConfig(BaseModel):
    """Einstellungen für die lokale Sprachprüfung."""

    model_config = ConfigDict(extra="forbid")

    language: str = Field(default="de-DE", min_length=1)
    ignored_rule_ids: list[str] = Field(default_factory=list)
    ignored_terms: list[str] = Field(default_factory=list)
    terminology_path: Path | None = None
    german_terminology_path: Path | None = None
    english_terminology_path: Path | None = None
    additional_english_terminology_paths: list[Path] = Field(default_factory=list)


class ProjectConfig(BaseModel):
    """Minimale Konfiguration für einen Prüflauf."""

    model_config = ConfigDict(extra="forbid")

    profile: str
    crawl: CrawlConfig
    check: CheckConfig = Field(default_factory=CheckConfig)


def load_project_config(path: Path) -> ProjectConfig:
    """Lädt und validiert eine lokale YAML-Projektkonfiguration."""
    config_data = yaml.safe_load(path.read_text(encoding="utf-8"))

    config = ProjectConfig.model_validate(config_data)
    for terminology_path_name in (
        "terminology_path",
        "german_terminology_path",
        "english_terminology_path",
    ):
        terminology_path = getattr(config.check, terminology_path_name)
        if terminology_path is not None and not terminology_path.is_absolute():
            setattr(
                config.check,
                terminology_path_name,
                (path.parent / terminology_path).resolve(),
            )
    config.check.additional_english_terminology_paths = [
        (path.parent / terminology_path).resolve()
        if not terminology_path.is_absolute()
        else terminology_path
        for terminology_path in config.check.additional_english_terminology_paths
    ]

    return config
