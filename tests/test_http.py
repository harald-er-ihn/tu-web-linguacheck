"""Tests für lokale HTTP-Hilfsfunktionen."""

import ssl
from urllib.error import URLError

import pytest

from tu_web_linguacheck import http
from tu_web_linguacheck.http import (
    fetch_html,
    fetch_xml,
    is_html_content_type,
    is_xml_content_type,
)


def test_recognizes_html_content_type() -> None:
    """HTML-Antworten werden anhand ihres Content-Types erkannt."""
    assert is_html_content_type("text/html; charset=utf-8")


def test_rejects_non_html_content_type() -> None:
    """Nicht-HTML-Antworten werden nicht als HTML akzeptiert."""
    assert not is_html_content_type("application/pdf")


def test_recognizes_standard_xml_content_types() -> None:
    """XML-Sitemaps werden anhand üblicher XML-Content-Types erkannt."""
    assert is_xml_content_type("application/xml; charset=utf-8")
    assert is_xml_content_type("text/xml")


def test_fetch_html_rejects_url_outside_allowed_domains() -> None:
    """Eine nicht erlaubte URL wird vor einem HTTP-Abruf abgelehnt."""
    with pytest.raises(ValueError, match="nicht erlaubt"):
        fetch_html(
            "https://external.example/page/",
            allowed_domains=["tu-dortmund.de"],
        )


def test_fetch_xml_rejects_url_outside_allowed_domains() -> None:
    """Eine nicht erlaubte Sitemap-URL wird vor dem Abruf abgelehnt."""
    with pytest.raises(ValueError, match="nicht erlaubt"):
        fetch_xml(
            "https://external.example/sitemap.xml",
            allowed_domains=["tu-dortmund.de"],
        )


class _FakeHeaders:
    """Minimaler Header-Ersatz für HTTP-Tests."""

    def __init__(self, content_type: str) -> None:
        self._content_type = content_type

    def get(self, name: str, default: str | None = None) -> str | None:
        """Liefert den konfigurierten Content-Type."""
        if name == "Content-Type":
            return self._content_type
        return default

    def get_content_charset(self) -> str:
        """Liefert den Zeichensatz der Testantwort."""
        return "utf-8"


class _FakeResponse:
    """Minimaler Context-Manager für kontrollierte HTTP-Antworten."""

    def __init__(self, url: str, body: bytes, content_type: str) -> None:
        self._url = url
        self._body = body
        self.headers = _FakeHeaders(content_type)

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        pass

    def geturl(self) -> str:
        """Liefert die finale URL."""
        return self._url

    def read(self, _size: int = -1) -> bytes:
        """Liefert den Antwortinhalt."""
        return self._body


def test_http_opener_limits_tls_to_version_1_2(monkeypatch: pytest.MonkeyPatch) -> None:
    """Der HTTPS-Handler verwendet einen Context mit TLS 1.2 als Obergrenze."""
    captured: dict[str, object] = {}
    context = ssl.create_default_context()

    def fake_https_handler(*, context: ssl.SSLContext) -> object:
        captured["context"] = context
        return object()

    monkeypatch.setattr(http.ssl, "create_default_context", lambda: context)
    monkeypatch.setattr(http, "HTTPSHandler", fake_https_handler)
    monkeypatch.setattr(http, "build_opener", lambda _handler: object())

    http._build_http_opener()  # pylint: disable=protected-access

    assert captured["context"] is context
    assert context.maximum_version is ssl.TLSVersion.TLSv1_2


def test_fetch_html_loads_robots_through_controlled_http_opener(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """robots.txt wird über denselben kontrollierten Opener wie HTML geladen."""
    requested_urls: list[str] = []

    class FakeOpener:  # pylint: disable=too-few-public-methods
        """Opener mit vorgegebenen Robots- und HTML-Antworten."""

        def open(self, request: object, *, timeout: int) -> _FakeResponse:
            """Liefert die zur angefragten URL passende Testantwort."""
            assert timeout == 15
            requested_urls.append(request.full_url)
            if request.full_url.endswith("/robots.txt"):
                return _FakeResponse(
                    request.full_url,
                    b"User-agent: *\nAllow: /\n",
                    "text/plain",
                )
            return _FakeResponse(
                request.full_url,
                b"<html><body>Inhalt</body></html>",
                "text/html",
            )

    opener = FakeOpener()

    def fake_build_http_opener() -> FakeOpener:
        """Liefert den kontrollierten Test-Opener."""
        return opener

    monkeypatch.setattr(http, "_build_http_opener", fake_build_http_opener)

    assert (
        http.fetch_html(
            "https://www.tu-dortmund.de/seite/",
            allowed_domains=["tu-dortmund.de"],
        )
        == "<html><body>Inhalt</body></html>"
    )
    assert requested_urls == [
        "https://www.tu-dortmund.de/robots.txt",
        "https://www.tu-dortmund.de/seite/",
    ]


def test_fetch_html_does_not_fetch_document_when_robots_request_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ein Fehler beim Abruf von robots.txt verhindert den Dokumentabruf."""

    requested_urls: list[str] = []

    class FailingOpener:  # pylint: disable=too-few-public-methods
        """Opener, dessen robots.txt-Abruf fehlschlägt."""

        def open(self, request: object, *, timeout: int) -> _FakeResponse:
            """Protokolliert den Abruf und simuliert einen Netzwerkfehler."""
            assert timeout == 15
            requested_urls.append(request.full_url)
            raise URLError("robots.txt nicht erreichbar")

    opener = FailingOpener()

    def fake_build_http_opener() -> FailingOpener:
        """Liefert den fehlschlagenden Test-Opener."""
        return opener

    monkeypatch.setattr(http, "_build_http_opener", fake_build_http_opener)

    with pytest.raises(URLError, match="robots.txt nicht erreichbar"):
        http.fetch_html(
            "https://www.tu-dortmund.de/seite/",
            allowed_domains=["tu-dortmund.de"],
        )

    assert requested_urls == ["https://www.tu-dortmund.de/robots.txt"]


def test_fetch_html_rejects_redirect_outside_start_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ein begrenzter Abruf lehnt Redirects außerhalb des Startpfads ab."""

    class RedirectingOpener:  # pylint: disable=too-few-public-methods
        """Opener mit erlaubter robots.txt und Redirect-Antwort."""

        def open(self, request: object, *, timeout: int) -> _FakeResponse:
            """Liefert robots.txt oder die finale Redirect-Antwort."""
            assert timeout == 15
            if request.full_url.endswith("/robots.txt"):
                return _FakeResponse(
                    request.full_url,
                    b"User-agent: *\nAllow: /\n",
                    "text/plain",
                )
            return _FakeResponse(
                "https://example.org/ausserhalb/",
                b"<html><body>Inhalt</body></html>",
                "text/html",
            )

    opener = RedirectingOpener()
    monkeypatch.setattr(http, "_build_http_opener", lambda: opener)

    with pytest.raises(ValueError, match="Startpfad"):
        fetch_html(
            "https://example.org/start/pfad/",
            allowed_domains=["example.org"],
            stay_under_start_path=True,
        )
