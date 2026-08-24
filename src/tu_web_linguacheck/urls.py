"""Regeln für URLs und erlaubte Domains."""

from collections.abc import Sequence
from urllib.parse import urlparse


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
