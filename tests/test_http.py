"""Tests für lokale HTTP-Hilfsfunktionen."""

import pytest

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
