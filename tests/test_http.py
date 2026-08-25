"""Tests für lokale HTTP-Hilfsfunktionen."""

from tu_web_linguacheck.http import is_html_content_type


def test_recognizes_html_content_type() -> None:
    """HTML-Antworten werden anhand ihres Content-Types erkannt."""
    assert is_html_content_type("text/html; charset=utf-8")


def test_rejects_non_html_content_type() -> None:
    """Nicht-HTML-Antworten werden nicht als HTML akzeptiert."""
    assert not is_html_content_type("application/pdf")
