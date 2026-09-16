"""Regeln für URLs, erlaubte Domains und URL-Normalisierung."""

import re
from collections.abc import Sequence
from urllib.parse import parse_qsl, urlencode, urlparse, urlsplit, urlunsplit

from tu_web_linguacheck.config import CrawlConfig


def is_allowed_url(url: str, allowed_domains: Sequence[str]) -> bool:
    """Prüft, ob eine HTTP(S)-URL zu einer erlaubten Domain gehört."""
    parsed_url = urlparse(url)

    if parsed_url.scheme not in {"http", "https"}:
        return False

    hostname = parsed_url.hostname
    if hostname is None:
        return False

    normalized_hostname = hostname.lower().rstrip(".")

    return any(
        normalized_hostname == domain or normalized_hostname.endswith(f".{domain}")
        for domain in (item.lower().rstrip(".") for item in allowed_domains)
    )


def is_url_under_start_path(url: str, start_url: str) -> bool:
    """Prüft, ob eine URL innerhalb des Startpfads derselben Origin liegt."""
    parsed_url = urlsplit(url)
    parsed_start_url = urlsplit(start_url)

    if (
        parsed_url.scheme != parsed_start_url.scheme
        or parsed_url.netloc.lower() != parsed_start_url.netloc.lower()
    ):
        return False

    start_path = parsed_start_url.path.rstrip("/") or "/"

    return parsed_url.path == start_path or parsed_url.path.startswith(
        f"{start_path.rstrip('/')}/"
    )


def normalize_url(url: str, tracking_parameters: Sequence[str]) -> str:
    """Entfernt Fragmente und konfigurierte Tracking-Parameter aus einer URL."""
    parsed_url = urlsplit(url)
    normalized_netloc = parsed_url.netloc.lower()

    if (parsed_url.scheme == "http" and parsed_url.port == 80) or (
        parsed_url.scheme == "https" and parsed_url.port == 443
    ):
        normalized_netloc = normalized_netloc.rsplit(":", maxsplit=1)[0]

    tracking_parameter_names = {
        parameter.casefold() for parameter in tracking_parameters
    }
    query_parameters = parse_qsl(parsed_url.query, keep_blank_values=True)
    relevant_query_parameters = [
        (name, value)
        for name, value in query_parameters
        if name.casefold() not in tracking_parameter_names
    ]

    return urlunsplit(
        (
            parsed_url.scheme,
            normalized_netloc,
            parsed_url.path,
            urlencode(relevant_query_parameters),
            "",
        )
    )


def should_crawl_url(url: str, exclude_patterns: Sequence[str]) -> bool:
    """Prüft, ob eine HTTP(S)-URL nicht auf ein Ausschlussmuster passt."""
    parsed_url = urlsplit(url)

    if parsed_url.scheme not in {"http", "https"} or parsed_url.hostname is None:
        return False

    return not any(
        re.search(pattern, url, flags=re.IGNORECASE) is not None
        for pattern in exclude_patterns
    )


def prepare_crawl_url(url: str, config: CrawlConfig) -> str | None:
    """Bereitet eine erlaubte, crawlbare URL gemäß Crawl-Konfiguration vor."""
    normalized_url = normalize_url(url, config.tracking_parameters)

    if not is_allowed_url(normalized_url, config.allowed_domains):
        return None

    if not should_crawl_url(normalized_url, config.exclude_patterns):
        return None

    return normalized_url
