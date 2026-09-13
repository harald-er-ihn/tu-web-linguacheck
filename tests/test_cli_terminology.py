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


def test_check_url_reports_local_german_inclusive_language(
    monkeypatch, tmp_path
) -> None:
    """Der Check-URL-Befehl meldet lokale inklusive deutsche Terminologie."""
    config_path = tmp_path / "config.yaml"
    terminology_path = tmp_path / "tu-de-terminology.local.json"
    terminology_path.write_text(
        """\
{
  "schema_version": 1,
  "entries": [
    {
      "preferred_term": "Lehrkräfte",
      "variants_to_flag": ["Lehrer"]
    }
  ]
}
""",
        encoding="utf-8",
    )
    config = ProjectConfig(
        profile="tu-de",
        crawl=CrawlConfig(
            allowed_domains=["example.org"],
            max_depth=1,
            max_pages=10,
            requests_per_second=1.0,
            obey_robots_txt=True,
        ),
        check={
            "language": "de-DE",
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
            title="Studium",
            text="Die Lehrer beraten Studierende.",
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
            "https://example.org/studium/",
            str(config_path),
        ],
    )

    assert result.exit_code == 0
    assert "Sprachfunde: 1" in result.output
    assert "Kategorie: terminology" in result.output
    assert "Regel: TU_DE_INCLUSIVE_LANGUAGE" in result.output
    assert "Fundstelle: Lehrer" in result.output
    assert "Vorschläge: Lehrkräfte" in result.output


def test_check_crawl_reports_local_german_inclusive_language(
    monkeypatch, tmp_path
) -> None:
    """Der Crawl-Check meldet lokale inklusive deutsche Terminologie."""
    config_path = tmp_path / "config.yaml"
    terminology_path = tmp_path / "tu-de-terminology.local.json"
    terminology_path.write_text(
        """\
{
  "schema_version": 1,
  "entries": [
    {
      "preferred_term": "Lehrkräfte",
      "variants_to_flag": ["Lehrer"]
    }
  ]
}
""",
        encoding="utf-8",
    )
    config = ProjectConfig(
        profile="tu-de",
        crawl=CrawlConfig(
            allowed_domains=["example.org"],
            max_depth=1,
            max_pages=10,
            requests_per_second=1.0,
            obey_robots_txt=True,
        ),
        check={
            "language": "de-DE",
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
                    "url": "https://example.org/studium/",
                    "depth": 0,
                    "title": "Studium",
                    "text": "Die Lehrer beraten Studierende.",
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
    assert "Regel: TU_DE_INCLUSIVE_LANGUAGE" in result.output
    assert "URL: https://example.org/studium/" in result.output
    assert "Fundstelle: Lehrer" in result.output
    assert "Vorschläge: Lehrkräfte" in result.output


def test_check_translation_reports_missing_english_term_and_writes_pdf(
    monkeypatch,
    tmp_path,
) -> None:
    """Der Übersetzungscheck meldet fehlendes Zielenglisch in einem PDF-Bericht."""
    config_path = tmp_path / "config.yaml"
    terminology_path = tmp_path / "tu-terminology.local.json"
    pdf_report_path = tmp_path / "translation-report.pdf"
    terminology_path.write_text(
        """\
{
  "schema_version": 1,
  "entries": [
    {
      "german": "Technische Universität Dortmund",
      "preferred_english": "TU Dortmund University",
      "variants_to_flag": []
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
    source_url = "https://example.org/de/testseite/"
    target_url = "https://example.org/en/test-page/"
    written_pdf_reports = []

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
        lambda url, allowed_domains: (
            "german-html" if url == source_url else "english-html"
        ),
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.extract_page_content",
        lambda html: (
            PageContent(
                title="Deutsch",
                text="Die Technische Universität Dortmund informiert.",
            )
            if html == "german-html"
            else PageContent(
                title="English",
                text="Dortmund University of Technology provides information.",
            )
        ),
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.find_allowed_page_language_links",
        lambda *_args: [type("Link", (), {"href": target_url, "language": "en"})()],
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.write_pdf_report",
        lambda path, **kwargs: written_pdf_reports.append((path, kwargs)),
    )

    result = runner.invoke(
        app,
        [
            "check-translation",
            source_url,
            str(config_path),
            "--pdf-report",
            str(pdf_report_path),
        ],
    )

    assert result.exit_code == 0
    assert f"Englische Übersetzungs-URL: {target_url}" in result.output
    assert "Sprachfunde: 1" in result.output
    assert "Fundstelle: Technische Universität Dortmund" in result.output
    assert "Vorschläge: TU Dortmund University" in result.output
    assert f"PDF-Bericht: {pdf_report_path}" in result.output
    assert written_pdf_reports
