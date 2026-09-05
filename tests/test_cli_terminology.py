"""Tests für die Terminologieintegration der Kommandozeile."""

from typer.testing import CliRunner

from tu_web_linguacheck.cli import app
from tu_web_linguacheck.config import CrawlConfig, ProjectConfig
from tu_web_linguacheck.html_content import PageContent

runner = CliRunner()


def test_check_url_reports_local_tu_terminology(monkeypatch, tmp_path) -> None:
    """Der Check-URL-Befehl meldet Varianten aus der lokalen TU-Terminologie."""
    config_path = tmp_path / "config.yaml"
    terminology_path = tmp_path / "tu-terminology.local.json"
    terminology_path.write_text(
        """\
{
  "schema_version": 1,
  "entries": [
    {
      "preferred_english": "TU Dortmund University",
      "variants_to_flag": ["Technical University of Dortmund"]
    }
  ]
}
""",
        encoding="utf-8",
    )
    config = ProjectConfig(
        profile="tu-en",
        crawl=CrawlConfig(
            allowed_domains=["example.org"],
            max_depth=1,
            max_pages=10,
            requests_per_second=1.0,
            obey_robots_txt=True,
        ),
        check={
            "language": "en-US",
            "terminology_path": terminology_path,
        },
    )

    monkeypatch.setattr(
        "tu_web_linguacheck.cli.load_project_config",
        lambda path: config,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.prepare_crawl_url",
        lambda url, crawl_config: url,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.fetch_html",
        lambda url, allowed_domains: "<html></html>",
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.extract_page_content",
        lambda html: PageContent(
            title="About",
            text="The Technical University of Dortmund is located in Germany.",
        ),
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.LanguageToolClient.check",
        lambda _self, *, text, language: [],
    )

    result = runner.invoke(
        app,
        [
            "check-url",
            "https://example.org/about/",
            str(config_path),
        ],
    )

    assert result.exit_code == 0
    assert "Sprachfunde: 1" in result.output
    assert "Kategorie: terminology" in result.output
    assert "Regel: TU_EN_TERMINOLOGY" in result.output
    assert "Fundstelle: Technical University of Dortmund" in result.output
    assert "Vorschläge: TU Dortmund University" in result.output


def test_check_crawl_reports_local_tu_terminology(monkeypatch, tmp_path) -> None:
    """Der Crawl-Check meldet Varianten aus der lokalen TU-Terminologie."""
    config_path = tmp_path / "config.yaml"
    terminology_path = tmp_path / "tu-terminology.local.json"
    terminology_path.write_text(
        """\
{
  "schema_version": 1,
  "entries": [
    {
      "preferred_english": "TU Dortmund University",
      "variants_to_flag": ["Technical University of Dortmund"]
    }
  ]
}
""",
        encoding="utf-8",
    )
    config = ProjectConfig(
        profile="tu-en",
        crawl=CrawlConfig(
            allowed_domains=["example.org"],
            max_depth=1,
            max_pages=10,
            requests_per_second=1.0,
            obey_robots_txt=True,
        ),
        check={
            "language": "en-US",
            "terminology_path": terminology_path,
        },
    )

    monkeypatch.setattr(
        "tu_web_linguacheck.cli.load_project_config",
        lambda path: config,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.crawl_pages_with_content",
        lambda **_kwargs: [
            type(
                "Page",
                (),
                {
                    "url": "https://example.org/about/",
                    "depth": 0,
                    "title": "About",
                    "text": (
                        "The Technical University of Dortmund is located in Germany."
                    ),
                    "blocks": (),
                },
            )()
        ],
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.LanguageToolClient.check",
        lambda _self, *, text, language: [],
    )

    result = runner.invoke(
        app,
        [
            "check-crawl",
            "https://example.org/",
            str(config_path),
        ],
    )

    assert result.exit_code == 0
    assert "Sprachfunde: 1" in result.output
    assert "Kategorie: terminology" in result.output
    assert "Regel: TU_EN_TERMINOLOGY" in result.output
    assert "URL: https://example.org/about/" in result.output
    assert "Fundstelle: Technical University of Dortmund" in result.output
    assert "Vorschläge: TU Dortmund University" in result.output
