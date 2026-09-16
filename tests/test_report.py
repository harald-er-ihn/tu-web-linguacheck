"""Tests für lokale HTML-Berichte."""

from unittest.mock import Mock

from tu_web_linguacheck.findings import (
    finding_from_missing_english_translation,
)
from tu_web_linguacheck.models import Finding
from tu_web_linguacheck.project_metadata import ProjectMetadata
from tu_web_linguacheck.report import (
    ReportContext,
    write_html_report,
    write_pdf_report,
)
from tu_web_linguacheck.terminology import TerminologyMatch


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
    assert '<header class="report-header">' in html
    assert "<h1>Sprachprüfbericht</h1>" in html
    assert '<section class="result-overview">' in html
    assert (
        '<p class="result-status result-status--findings">'
        "1 Sprachfund festgestellt.</p>"
    ) in html
    assert (
        '<div class="metric-card"><p class="metric-label">Gecrawlte Seiten</p>'
        '<p class="metric-value">2</p></div>' in html
    )
    assert (
        '<div class="metric-card"><p class="metric-label">Prüfblöcke</p>'
        '<p class="metric-value">5</p></div>' in html
    )
    assert (
        '<div class="metric-card"><p class="metric-label">Sprachfunde</p>'
        '<p class="metric-value">1</p></div>' in html
    )
    assert ".report-header {" in html
    assert ".metric-cards {\n      display: grid;" in html
    assert ".result-status--findings {" in html
    assert ".result-status--clear {" in html
    assert (
        '<a href="https://example.org/seite/?source=report&amp;lang=de">'
        "https://example.org/seite/?source=report&amp;lang=de</a>"
    ) in html
    assert "Möglicher &lt;Tippfehler&gt; &amp; Hinweis." in html
    assert "Ein &lt;fehlerh<mark>afte</mark>r&gt; Test." in html


def test_write_html_report_limits_suggestions(tmp_path) -> None:
    """Der HTML-Bericht begrenzt lange Vorschlagslisten nachvollziehbar."""
    report_path = tmp_path / "crawl-report.html"
    finding = Finding(
        url="https://example.org/",
        category="misspelling",
        severity="warning",
        message="Testmeldung.",
        offset=0,
        length=4,
        suggestions=(
            "Vorschlag 1",
            "Vorschlag 2",
            "Vorschlag 3",
            "Vorschlag 4",
            "Vorschlag 5",
            "Vorschlag 6",
            "Vorschlag 7",
        ),
        context="Testkontext",
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

    assert "Vorschlag 1, Vorschlag 2, Vorschlag 3, Vorschlag 4, Vorschlag 5" in html
    assert "… und 2 weitere Vorschläge" in html
    assert "Vorschlag 6" not in html


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


def test_write_html_report_uses_escaped_project_metadata(monkeypatch, tmp_path) -> None:
    """Der HTML-Bericht nutzt sicher escapte zentrale Projektmetadaten."""
    report_path = tmp_path / "crawl-report.html"
    monkeypatch.setattr(
        "tu_web_linguacheck.report.load_project_metadata",
        lambda: ProjectMetadata(
            name="Test <Werkzeug>",
            version="2.3.4",
            description="Testbeschreibung & Hinweis",
            author="Test & Autor",
            license_name="Test-Lizenz",
        ),
    )

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
    assert "Test &lt;Werkzeug&gt; 2.3.4" in html
    assert "Testbeschreibung &amp; Hinweis" in html
    assert "Test &amp; Autor" in html
    assert "Test-Lizenz" in html


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
    assert (
        '<p class="result-status result-status--clear">'
        "Keine Sprachfunde festgestellt.</p>"
    ) in html


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


def test_write_html_report_lists_checked_urls_without_findings(tmp_path) -> None:
    """Der Bericht führt auch geprüfte URLs ohne Sprachfunde auf."""
    report_path = tmp_path / "crawl-report.html"
    finding = Finding(
        url="https://example.org/mit-fund/",
        category="grammar",
        severity="warning",
        message="Testmeldung.",
        offset=0,
        length=4,
        suggestions=(),
        context="Testkontext.",
        profile="generic-de",
        source_rule_id="TEST_RULE",
    )

    write_html_report(
        report_path,
        crawled_pages=3,
        checked_blocks=3,
        findings=[finding],
        context=ReportContext(
            start_url="https://example.org/",
            profile="generic-de",
            language="de-DE",
            checked_urls=(
                "https://example.org/mit-fund/",
                "https://example.org/ohne-fund/",
                "https://example.org/ebenfalls-ohne-fund/",
            ),
        ),
    )

    html = report_path.read_text(encoding="utf-8")

    assert "<h2>Inhaltsverzeichnis</h2>" in html
    assert (
        '<a href="#findings-url-1">https://example.org/mit-fund/</a> (1 Fund)' in html
    )
    assert (
        '<a href="#findings-url-2">https://example.org/ohne-fund/</a> (0 Funde)' in html
    )
    assert (
        '<a href="#findings-url-3">https://example.org/ebenfalls-ohne-fund/</a> '
        "(0 Funde)" in html
    )
    assert '<section class="findings-by-url" id="findings-url-2">' in html
    assert '<section class="findings-by-url" id="findings-url-3">' in html
    assert (
        '<section class="findings-by-url" id="findings-url-2">\n'
        '    <h2 class="findings-url"><a href="https://example.org/ohne-fund/">'
        "https://example.org/ohne-fund/</a></h2>\n"
        '    <p class="empty-state">Keine Sprachfunde festgestellt.</p>\n'
        "  </section>"
    ) in html
    assert html.count("<table>") == 1


def test_write_html_report_groups_findings_by_url(tmp_path) -> None:
    """Der HTML-Bericht gruppiert Funde in Tabellen unter ihren URLs."""
    report_path = tmp_path / "crawl-report.html"
    findings = [
        Finding(
            url="https://example.org/erste-seite/",
            category="grammar",
            severity="warning",
            message="Erste Meldung.",
            offset=0,
            length=6,
            suggestions=("Erste Korrektur",),
            context="Erster Fundkontext.",
            profile="generic-de",
            source_rule_id="FIRST_RULE",
        ),
        Finding(
            url="https://example.org/erste-seite/",
            category="grammar",
            severity="warning",
            message="Dritte Meldung.",
            offset=0,
            length=6,
            suggestions=("Dritte Korrektur",),
            context="Dritter Fundkontext.",
            profile="generic-de",
            source_rule_id="THIRD_RULE",
        ),
        Finding(
            url="https://example.org/zweite-seite/",
            category="spelling",
            severity="warning",
            message="Zweite Meldung.",
            offset=0,
            length=7,
            suggestions=("Zweite Korrektur",),
            context="Zweiter Fundkontext.",
            profile="generic-de",
            source_rule_id="SECOND_RULE",
        ),
    ]

    write_html_report(
        report_path,
        crawled_pages=2,
        checked_blocks=2,
        findings=findings,
        context=ReportContext(
            start_url="https://example.org/",
            profile="generic-de",
            language="de-DE",
        ),
    )

    html = report_path.read_text(encoding="utf-8")

    assert "<th>URL</th>" not in html
    assert (
        '<h2 class="findings-url"><a href="https://example.org/erste-seite/">'
        "https://example.org/erste-seite/</a></h2>"
    ) in html
    assert (
        '<h2 class="findings-url"><a href="https://example.org/zweite-seite/">'
        "https://example.org/zweite-seite/</a></h2>"
    ) in html
    assert html.count("<table>") == 2
    assert "<h2>Inhaltsverzeichnis</h2>" in html
    assert (
        '<a href="#findings-url-1">https://example.org/erste-seite/</a> (2 Funde)'
        in html
    )
    assert (
        '<a href="#findings-url-2">https://example.org/zweite-seite/</a> (1 Fund)'
        in html
    )
    assert '<section class="findings-by-url" id="findings-url-1">' in html
    assert '<section class="findings-by-url" id="findings-url-2">' in html
    back_to_top_link = '<p class="back-to-top"><a href="#report-top">Nach oben</a></p>'
    assert html.count(back_to_top_link) == 2
    assert html.count('<a href="#report-top">Nach oben</a>') == 3
    assert (
        "  </section>\n"
        f"  {back_to_top_link}\n"
        '  <section class="findings-by-url" id="findings-url-2">'
    ) in html
    assert (
        f'  </section>\n  {back_to_top_link}\n  <section id="report-information">'
    ) in html
    assert '<section id="report-information">' in html
    assert '<p><a href="#report-top">Nach oben</a></p>' in html


def test_write_html_report_sets_readable_finding_column_widths(tmp_path) -> None:
    """Der HTML-Bericht reserviert breite Spalten für Fundinhalte."""
    report_path = tmp_path / "report.html"
    finding = Finding(
        url="https://example.org/",
        category="grammar<test>",
        severity="warning",
        message="Testmeldung.",
        offset=0,
        length=4,
        suggestions=("Test",),
        context="Testkontext.",
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

    assert '<col class="finding-category">' not in html
    assert '<col class="finding-severity">' not in html
    assert '<col class="finding-message">' in html
    assert '<col class="finding-suggestions">' in html
    assert '<col class="finding-context">' in html
    assert '<col class="finding-rule">' not in html
    assert "<th>Regel</th>" not in html
    assert '<p class="finding-rule">Regel: TEST_RULE</p>' in html
    assert '<strong class="finding-badge">warning</strong>' in html
    assert '<strong class="finding-badge">grammar&lt;test&gt;</strong>' in html
    assert "finding-classification" not in html
    assert "Kategorie:" not in html
    assert "Schweregrad:" not in html
    assert ".finding-category { width:" not in html
    assert ".finding-severity { width:" not in html
    assert ".finding-context { width: 42%; }" in html
    assert '<section class="table-of-contents">' not in html


def test_write_pdf_report_creates_pdf_file(tmp_path) -> None:
    """Der PDF-Bericht wird als echte lokale PDF-Datei geschrieben."""
    report_path = tmp_path / "reports" / "crawl-report.pdf"

    write_pdf_report(
        report_path,
        crawled_pages=1,
        checked_blocks=1,
        findings=[],
        context=ReportContext(
            start_url="https://example.org/",
            profile="generic-de",
            language="de-DE",
        ),
    )

    assert report_path.is_file()
    assert report_path.read_bytes().startswith(b"%PDF-")


def test_write_pdf_report_requests_pdf_ua_1(monkeypatch, tmp_path) -> None:
    """Der PDF-Bericht fordert bei WeasyPrint PDF/UA-1 an."""
    report_path = tmp_path / "report.pdf"
    fake_html = Mock()
    monkeypatch.setattr(
        "tu_web_linguacheck.report.HTML",
        lambda *, string: fake_html,
    )

    write_pdf_report(
        report_path,
        crawled_pages=1,
        checked_blocks=1,
        findings=[],
        context=ReportContext(
            start_url="https://example.org/",
            profile="generic-de",
            language="de-DE",
        ),
    )

    fake_html.write_pdf.assert_called_once_with(
        report_path,
        pdf_variant="pdf/ua-1",
        uncompressed_pdf=False,
    )


def test_write_html_report_adds_print_rules_for_finding_tables(tmp_path) -> None:
    """Der HTML-Bericht schützt Fundzeilen und wiederholt Köpfe beim Drucken."""
    report_path = tmp_path / "report.html"

    write_html_report(
        report_path,
        crawled_pages=1,
        checked_blocks=1,
        findings=[],
        context=ReportContext(
            start_url="https://example.org/",
            profile="generic-de",
            language="de-DE",
        ),
    )

    html = report_path.read_text(encoding="utf-8")

    assert "@media print {" in html
    assert "thead { display: table-header-group; }" in html
    assert "tbody tr { break-inside: avoid; }" in html


def test_write_html_report_shows_source_and_target_context_for_translation(
    tmp_path,
) -> None:
    """Ein Übersetzungsfund zeigt getrennte deutsche und englische Nachweise."""
    report_path = tmp_path / "translation-report.html"
    source_url = "https://example.org/de/testseite/"
    target_url = "https://example.org/en/test-page/"
    source_term = "Technische Universität Dortmund"
    source_context = f"Die {source_term} informiert."
    target_context = "Dortmund University of Technology provides information."
    finding = finding_from_missing_english_translation(
        TerminologyMatch(
            matched_text=source_term,
            offset=4,
            length=len(source_term),
            preferred_term="TU Dortmund University",
        ),
        occurrence_count=3,
        source_url=source_url,
        target_url=target_url,
        source_context=source_context,
        target_context=target_context,
        profile="tu-en",
    )

    write_html_report(
        report_path,
        crawled_pages=2,
        checked_blocks=2,
        findings=[finding],
        context=ReportContext(
            start_url=source_url,
            profile="tu-en",
            language="de-DE → en-US",
            checked_urls=(source_url, target_url),
        ),
    )

    html = report_path.read_text(encoding="utf-8")

    assert "Deutscher Quellnachweis" in html
    assert "Englischer Zieltext" in html
    assert f"<mark>{source_term}</mark>" in html
    assert target_context in html
    assert "Deutsch: Technische Universität Dortmund" in html
    assert "Englisch: TU Dortmund University" in html
    assert "Vorkommen im Quelltext: 3" in html
    assert "<mark>Dortmund University of Technology</mark>" not in html
    assert "<td>" + chr(92) + "\n" not in html
