"""Tests für CLI-Hilfetexte und HTML-Berichte."""

from pathlib import Path

from typer.testing import CliRunner

from tu_web_linguacheck.cli import app
from tu_web_linguacheck.config import CrawlConfig, ProjectConfig
from tu_web_linguacheck.html_content import PageContent
from tu_web_linguacheck.models import Finding
from tu_web_linguacheck.report import ReportContext, write_html_report

runner = CliRunner()


def test_help_explains_single_url_check_arguments() -> None:
    """Die allgemeine CLI-Hilfe erklärt den Einzelurl-Schnellstart."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Schnellstart für eine einzelne Seite:" in result.output
    assert "check-url URL CONFIG_PATH --report DATEI.html" in result.output
    assert "URL ist die Webadresse." in result.output
    assert "CONFIG_PATH ist eine lokale YAML-Konfigurationsdatei." in result.output
    assert "--report DATEI.html erstellt optional einen lokalen HTML-Bericht." in (
        result.output
    )
    assert "tu-web-linguacheck COMMAND --help" in result.output


def test_check_url_writes_html_report(monkeypatch, tmp_path) -> None:
    """Der Einzelurl-Check schreibt auf Wunsch einen HTML-Bericht."""
    config_path = tmp_path / "config.yaml"
    report_path = tmp_path / "url-report.html"
    config = ProjectConfig(
        profile="generic-de",
        crawl=CrawlConfig(
            allowed_domains=["example.org"],
            max_depth=0,
            max_pages=1,
            requests_per_second=1.0,
            obey_robots_txt=True,
        ),
    )
    written_reports: list[tuple[Path, int, int, list[Finding], ReportContext]] = []

    monkeypatch.setattr(
        "tu_web_linguacheck.cli.load_project_config",
        lambda _path: config,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.prepare_crawl_url",
        lambda _url, _config: "https://example.org/",
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.fetch_html",
        lambda _url, _domains: "<main>Ein Test.</main>",
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.extract_page_content",
        lambda _html: PageContent(title="Testseite", text="Ein Test."),
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.LanguageToolClient.check",
        lambda _self, **_kwargs: [],
    )

    def fake_write_html_report(
        path: Path,
        *,
        crawled_pages: int,
        checked_blocks: int,
        findings: list[Finding],
        context: ReportContext,
    ) -> None:
        written_reports.append((path, crawled_pages, checked_blocks, findings, context))

    monkeypatch.setattr(
        "tu_web_linguacheck.cli.write_html_report",
        fake_write_html_report,
    )

    result = runner.invoke(
        app,
        [
            "check-url",
            "https://example.org/",
            str(config_path),
            "--report",
            str(report_path),
        ],
    )

    assert result.exit_code == 0
    assert written_reports == [
        (
            report_path,
            1,
            1,
            [],
            ReportContext("https://example.org/", "generic-de", "de-DE"),
        )
    ]
    assert f"HTML-Bericht: {report_path}" in result.output


def test_check_url_embeds_report_information(monkeypatch, tmp_path) -> None:
    """Der Einzelurl-Report enthält eingebettete Sprachbericht-Informationen."""

    config_path = tmp_path / "config.yaml"
    report_path = tmp_path / "url-report.html"
    config = ProjectConfig(
        profile="generic-de",
        crawl=CrawlConfig(
            allowed_domains=["example.org"],
            max_depth=0,
            max_pages=1,
            requests_per_second=1.0,
            obey_robots_txt=True,
        ),
    )

    monkeypatch.setattr(
        "tu_web_linguacheck.cli.load_project_config", lambda _path: config
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.prepare_crawl_url",
        lambda _url, _config: "https://example.org/",
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.fetch_html", lambda _url, _domains: "<main>Test</main>"
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.extract_page_content",
        lambda _html: PageContent(title="Testseite", text="Test"),
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.LanguageToolClient.check",
        lambda _self, **_kwargs: [],
    )
    monkeypatch.setattr("tu_web_linguacheck.cli.write_html_report", write_html_report)

    result = runner.invoke(
        app,
        [
            "check-url",
            "https://example.org/",
            str(config_path),
            "--report",
            str(report_path),
        ],
    )

    html = report_path.read_text(encoding="utf-8")

    assert result.exit_code == 0
    assert not (tmp_path / "report-information.html").exists()
    assert 'href="#report-information"' in html
    assert '<section id="report-information">' in html
    assert "<h1>Informationen zum Sprachprüfbericht</h1>" in html
    assert 'href="#report-top">Nach oben</a>' in html
