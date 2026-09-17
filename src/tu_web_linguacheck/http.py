"""Hilfsfunktionen für lokale HTTP-Antworten."""

import ssl
from collections.abc import Callable, Sequence
from urllib import robotparser
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPSHandler, OpenerDirector, Request, build_opener

from tu_web_linguacheck.urls import is_allowed_url

_USER_AGENT = "tu-web-linguacheck/0.1"
_DEFAULT_TIMEOUT_SECONDS = 15
_MAX_RESPONSE_BYTES = 2_000_000


def is_html_content_type(content_type: str) -> bool:
    """Prüft, ob ein Content-Type eine HTML-Antwort bezeichnet."""
    media_type = content_type.split(";", maxsplit=1)[0].strip().casefold()

    return media_type == "text/html"


def is_xml_content_type(content_type: str) -> bool:
    """Prüft, ob ein Content-Type eine XML-Antwort bezeichnet."""
    media_type = content_type.split(";", maxsplit=1)[0].strip().casefold()

    return media_type in {"application/xml", "text/xml"}


def _build_http_opener() -> OpenerDirector:
    """Erstellt einen Opener mit TLS 1.2 als maximaler TLS-Version."""
    context = ssl.create_default_context()
    context.maximum_version = ssl.TLSVersion.TLSv1_2

    return build_opener(HTTPSHandler(context=context))


def _load_robots(
    robots_url: str, opener: OpenerDirector
) -> robotparser.RobotFileParser:
    """Lädt robots.txt über den kontrollierten Opener."""
    robots = robotparser.RobotFileParser()
    robots.set_url(robots_url)
    request = Request(robots_url, headers={"User-Agent": _USER_AGENT})

    try:
        with opener.open(request, timeout=_DEFAULT_TIMEOUT_SECONDS) as response:
            robots.parse(response.read().decode("utf-8").splitlines())
    except HTTPError as error:
        if error.code in (401, 403):
            robots.disallow_all = True
        elif 400 <= error.code < 500:
            robots.allow_all = True

    return robots


def _fetch_document(
    url: str,
    allowed_domains: Sequence[str],
    *,
    document_name: str,
    accepts_content_type: Callable[[str], bool],
) -> str:
    """Ruft ein erlaubtes, per robots.txt erlaubtes Dokument sicher ab."""
    if not is_allowed_url(url, allowed_domains):
        raise ValueError(f"URL ist nicht erlaubt: {url}")

    parsed_url = urlsplit(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    opener = _build_http_opener()
    robots = _load_robots(robots_url, opener)

    if not robots.can_fetch(_USER_AGENT, url):
        raise ValueError(f"robots.txt erlaubt keinen Abruf: {url}")

    request = Request(url, headers={"User-Agent": _USER_AGENT})

    with opener.open(request, timeout=_DEFAULT_TIMEOUT_SECONDS) as response:
        final_url = response.geturl()

        if not is_allowed_url(final_url, allowed_domains):
            raise ValueError(f"Weiterleitung zu nicht erlaubter URL: {final_url}")

        content_type = response.headers.get("Content-Type", "")

        if not accepts_content_type(content_type):
            raise ValueError(
                f"Antwort ist kein {document_name}-Dokument: {content_type}"
            )

        content_length = response.headers.get("Content-Length")

        if content_length is not None and int(content_length) > _MAX_RESPONSE_BYTES:
            raise ValueError(
                f"{document_name}-Antwort überschreitet die maximale Größe."
            )

        document_bytes = response.read(_MAX_RESPONSE_BYTES + 1)
        charset = response.headers.get_content_charset() or "utf-8"

    if len(document_bytes) > _MAX_RESPONSE_BYTES:
        raise ValueError(f"{document_name}-Antwort überschreitet die maximale Größe.")

    return document_bytes.decode(charset, errors="replace")


def fetch_html(url: str, allowed_domains: Sequence[str]) -> str:
    """Ruft eine erlaubte, per robots.txt erlaubte HTML-Seite lokal ab."""
    return _fetch_document(
        url,
        allowed_domains,
        document_name="HTML",
        accepts_content_type=is_html_content_type,
    )


def fetch_xml(url: str, allowed_domains: Sequence[str]) -> str:
    """Ruft eine erlaubte, per robots.txt erlaubte XML-Sitemap lokal ab."""
    return _fetch_document(
        url,
        allowed_domains,
        document_name="XML",
        accepts_content_type=is_xml_content_type,
    )
