"""Interne Modelle für Ergebnisse der Sprachprüfung."""

from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

Severity = Literal["error", "warning", "hint", "info"]


@dataclass(frozen=True)
class CrawlCandidate:
    """Eine vorbereitete Crawl-URL mit ihrer Entfernung vom Startpunkt."""

    url: str
    depth: int


@dataclass(frozen=True)
class CrawledPage:
    """Eine abgerufene Seite mit extrahiertem sichtbaren Inhalt."""

    url: str
    depth: int
    title: str
    text: str


# pylint: disable=too-few-public-methods
class Finding(BaseModel):
    """Ein einzelner Fund aus einer Sprach- oder Regelprüfung."""

    model_config = ConfigDict(extra="forbid")

    url: str
    category: str = Field(min_length=1)
    severity: Severity
    message: str = Field(min_length=1)
    offset: int = Field(ge=0)
    length: int = Field(gt=0)
    suggestions: tuple[str, ...]
    context: str = Field(min_length=1)
    profile: str = Field(min_length=1)
    source_rule_id: str = Field(min_length=1)

    @field_validator("url")
    @classmethod
    def validate_http_url(cls, value: str) -> str:
        """Akzeptiert ausschließlich vollständige HTTP(S)-URLs."""
        parsed_url = urlsplit(value)

        if parsed_url.scheme not in {"http", "https"} or parsed_url.hostname is None:
            raise ValueError("URL muss eine vollständige HTTP(S)-URL sein.")

        return value
