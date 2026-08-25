"""Modelle für die lokale Projektkonfiguration."""

from pydantic import BaseModel, Field


class CrawlConfig(BaseModel):
    """Grenzen und Sicherheitsvorgaben für einen Crawl."""

    allowed_domains: list[str] = Field(min_length=1)
    max_depth: int = Field(ge=0)
    max_pages: int = Field(ge=1)
    requests_per_second: float = Field(gt=0)
    obey_robots_txt: bool


class ProjectConfig(BaseModel):
    """Minimale Konfiguration für einen Prüflauf."""

    profile: str
    crawl: CrawlConfig
