"""Tests für lokale HTML-Berichte."""

from tu_web_linguacheck.models import Finding
from tu_web_linguacheck.report import write_html_report


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
    assert "Ein &lt;fehlerhafter&gt; Test." in html
