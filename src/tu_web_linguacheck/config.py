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


class ProjectConfig(BaseModel):
    """Minimale Konfiguration für einen Prüflauf."""

    model_config = ConfigDict(extra="forbid")

    profile: str
    crawl: CrawlConfig


def load_project_config(path: Path) -> ProjectConfig:
    """Lädt und validiert eine lokale YAML-Projektkonfiguration."""
    config_data = yaml.safe_load(path.read_text(encoding="utf-8"))

    return ProjectConfig.model_validate(config_data)
