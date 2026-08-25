"""Hilfsfunktionen für lokale HTTP-Antworten."""

from collections.abc import Sequence
from urllib import robotparser
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from tu_web_linguacheck.urls import is_allowed_url

_USER_AGENT = "tu-web-linguacheck/0.1"
_DEFAULT_TIMEOUT_SECONDS = 15
_MAX_RESPONSE_BYTES = 2_000_000


def is_html_content_type(content_type: str) -> bool:
    """Prüft, ob ein Content-Type eine HTML-Antwort bezeichnet."""
    media_type = content_type.split(";", maxsplit=1)[0].strip().casefold()

    return media_type == "text/html"


def fetch_html(url: str, allowed_domains: Sequence[str]) -> str:
    """Ruft eine erlaubte, per robots.txt erlaubte HTML-Seite lokal ab."""
    if not is_allowed_url(url, allowed_domains):
        raise ValueError(f"URL ist nicht erlaubt: {url}")

    parsed_url = urlsplit(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

    robots = robotparser.RobotFileParser()
    robots.set_url(robots_url)
    robots.read()

    if not robots.can_fetch(_USER_AGENT, url):
        raise ValueError(f"robots.txt erlaubt keinen Abruf: {url}")

    request = Request(url, headers={"User-Agent": _USER_AGENT})

    with urlopen(request, timeout=_DEFAULT_TIMEOUT_SECONDS) as response:
        final_url = response.geturl()

        if not is_allowed_url(final_url, allowed_domains):
            raise ValueError(f"Weiterleitung zu nicht erlaubter URL: {final_url}")

        content_type = response.headers.get("Content-Type", "")

        if not is_html_content_type(content_type):
            raise ValueError(f"Antwort ist kein HTML-Dokument: {content_type}")

        content_length = response.headers.get("Content-Length")

        if content_length is not None and int(content_length) > _MAX_RESPONSE_BYTES:
            raise ValueError("HTML-Antwort überschreitet die maximale Größe.")

        html_bytes = response.read(_MAX_RESPONSE_BYTES + 1)
        charset = response.headers.get_content_charset() or "utf-8"

    if len(html_bytes) > _MAX_RESPONSE_BYTES:
        raise ValueError("HTML-Antwort überschreitet die maximale Größe.")

    return html_bytes.decode(charset, errors="replace")
