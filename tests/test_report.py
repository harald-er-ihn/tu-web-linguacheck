"""Tests für lokale HTML-Berichte."""

from tu_web_linguacheck.models import Finding
from tu_web_linguacheck.report import (
    ReportContext,
    write_html_report,
    write_project_info_page,
)


def test_write_html_report_creates_clickable_escaped_findings(tmp_path) -> None:
    """Der HTML-Bericht enthält Kennzahlen, Links und escaped Fundinhalte."""
    report_path = tmp_path / "crawl-report.html"
    finding = Finding(
        url="https://example.org/seite/?source=report&lang=de",
        category="misspelling",
        severity="warning",
        message="Möglicher <Tippfehler> & Hinweis.",
        offset=12,
        length=4,
        suggestions=("Test",),
        context="Ein <fehlerhafter> Test.",
        profile="generic-de",
        source_rule_id="TEST_RULE",
    )

    write_html_report(
        report_path,
        crawled_pages=2,
        checked_blocks=5,
        findings=[finding],
        context=ReportContext(
            start_url="https://example.org/seite/",
            profile="generic-de",
            language="de-DE",
        ),
    )

    html = report_path.read_text(encoding="utf-8")

    assert "<title>Sprachprüfbericht</title>" in html
    assert "Gecrawlte Seiten: 2" in html
    assert "Prüfblöcke: 5" in html
    assert "Sprachfunde: 1" in html
    assert (
        '<a href="https://example.org/seite/?source=report&amp;lang=de">'
        "https://example.org/seite/?source=report&amp;lang=de</a>"
    ) in html
    assert "Möglicher &lt;Tippfehler&gt; &amp; Hinweis." in html
    assert "Ein &lt;fehlerh<mark>afte</mark>r&gt; Test." in html


def test_write_html_report_limits_and_marks_context(tmp_path) -> None:
    """Der HTML-Bericht kürzt Kontext und markiert die Fundstelle sicher."""
    report_path = tmp_path / "crawl-report.html"
    matched_text = "<istf>"
    finding = Finding(
        url="https://example.org/",
        category="misspelling",
        severity="warning",
        message="Möglicher Tippfehler gefunden.",
        offset=90,
        length=len(matched_text),
        suggestions=(),
        context=f"{'a' * 90}{matched_text}{'b' * 90}",
        profile="generic-de",
        source_rule_id="TEST_RULE",
    )

    write_html_report(
        report_path,
        crawled_pages=1,
        checked_blocks=1,
        findings=[finding],
        context=ReportContext(
            start_url="https://example.org/",
            profile="generic-de",
            language="de-DE",
        ),
    )

    html = report_path.read_text(encoding="utf-8")

    expected_context = f"…{'a' * 80}<mark>&lt;istf&gt;</mark>{'b' * 80}…"
    assert expected_context in html
    assert finding.context not in html


def test_write_project_info_page_renders_safe_markdown(tmp_path) -> None:
    """Die Projektinformationsseite formatiert und escaped README-Markdown."""
    page_path = tmp_path / "projektinformationen.html"
    markdown = """\
# tu-web-linguacheck

Ein **lokales** Werkzeug.

## Ziele

- HTML-Seiten prüfen
- Keine <Cloud-KI> nutzen
"""

    write_project_info_page(page_path, markdown=markdown)

    html = page_path.read_text(encoding="utf-8")

    assert "<title>Über tu-web-linguacheck</title>" in html
    assert "<h1>tu-web-linguacheck</h1>" in html
    assert "<strong>lokales</strong>" in html
    assert "<h2>Ziele</h2>" in html
    assert "<li>HTML-Seiten prüfen</li>" in html
    assert "<li>Keine &lt;Cloud-KI&gt; nutzen</li>" in html


def test_write_html_report_includes_project_information(tmp_path) -> None:
    """Der HTML-Bericht nennt die grundlegenden Projektinformationen."""
    report_path = tmp_path / "crawl-report.html"

    write_html_report(
        report_path,
        crawled_pages=0,
        checked_blocks=0,
        findings=[],
        context=ReportContext(
            start_url="https://example.org/",
            profile="generic-de",
            language="de-DE",
        ),
    )

    html = report_path.read_text(encoding="utf-8")

    assert "<h2>Über dieses Werkzeug</h2>" in html
    assert "tu-web-linguacheck 0.1.0" in html
    assert "Lokale Sprachprüfung für öffentlich erreichbare Websites" in html
    assert "Dr. Harald Hutter" in html
    assert "MIT-Lizenz" in html


def test_write_html_report_shows_empty_state_without_findings(tmp_path) -> None:
    """Der HTML-Bericht zeigt ohne Funde einen klaren Leerzustand."""
    report_path = tmp_path / "crawl-report.html"

    write_html_report(
        report_path,
        crawled_pages=1,
        checked_blocks=3,
        findings=[],
        context=ReportContext(
            start_url="https://example.org/",
            profile="generic-de",
            language="de-DE",
        ),
    )

    html = report_path.read_text(encoding="utf-8")

    assert '<p class="empty-state">Keine Sprachfunde festgestellt.</p>' in html


def test_write_html_report_shows_escaped_check_context(tmp_path) -> None:
    """Der HTML-Bericht zeigt einen sicher escapten Prüfkontext."""
    report_path = tmp_path / "crawl-report.html"

    write_html_report(
        report_path,
        crawled_pages=1,
        checked_blocks=3,
        findings=[],
        context=ReportContext(
            start_url="https://example.org/start?source=<report>",
            profile="tu-de",
            language="de-DE",
        ),
    )

    html = report_path.read_text(encoding="utf-8")

    assert '<section class="check-context">' in html
    assert "<h2>Prüfkontext</h2>" in html
    assert "Start-URL: https://example.org/start?source=&lt;report&gt;" in html
    assert "Profil: tu-de" in html
    assert "Sprache: de-DE" in html
