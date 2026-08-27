"""Regeln für URLs, erlaubte Domains und URL-Normalisierung."""

from collections.abc import Sequence
from urllib.parse import parse_qsl, urlencode, urlparse, urlsplit, urlunsplit


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
