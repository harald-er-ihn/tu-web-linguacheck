"""Tests für die Terminologieintegration der Kommandozeile."""

from typer.testing import CliRunner

from tu_web_linguacheck.cli import app
from tu_web_linguacheck.config import CrawlConfig, ProjectConfig
from tu_web_linguacheck.html_content import PageContent, TextBlock

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
    cfv_terminology_path = tmp_path / "cfv-terminology.local.json"
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
    cfv_terminology_path.write_text(
        """\
{
  "schema_version": 1,
  "entries": [
    {
      "german": "Begleitservice",
      "preferred_english": "accompaniment service",
      "variants_to_flag": ["escort service"]
    }
  ]
}
""",
        encoding="utf-8",
    )

    config = ProjectConfig(
        profile="tu",
        crawl=CrawlConfig(
            allowed_domains=["example.org"],
            max_depth=1,
            max_pages=10,
            requests_per_second=1.0,
            obey_robots_txt=True,
        ),
        check={
            "language": "de-DE",
            "english_terminology_path": terminology_path,
            "additional_english_terminology_paths": [cfv_terminology_path],
        },
    )
    source_url = "https://example.org/de/testseite/"
    target_url = "https://example.org/en/test-page/"
    written_pdf_reports = []

    checked_languages: list[tuple[str, str]] = []

    def fake_check(_self, *, text: str, language: str) -> list:
        checked_languages.append((text, language))
        return []

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
                text=(
                    "Die Technische Universität Dortmund "
                    "informiert über den Begleitservice."
                ),
                blocks=(
                    TextBlock(
                        text=(
                            "Die Technische Universität Dortmund "
                            "informiert über den Begleitservice."
                        ),
                        language="de",
                    ),
                ),
            )
            if html == "german-html"
            else PageContent(
                title="English",
                text="Dortmund University of Technology provides an escort service.",
                blocks=(
                    TextBlock(
                        text=(
                            "Dortmund University of Technology provides "
                            "an escort service."
                        ),
                        language="en",
                    ),
                ),
            )
        ),
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.find_allowed_page_language_links",
        lambda *_args: [type("Link", (), {"href": target_url, "language": "en"})()],
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.LanguageToolClient.check",
        fake_check,
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
    assert not checked_languages
    assert f"Englische Übersetzungs-URL: {target_url}" in result.output
    assert "Sprachfunde: 3" in result.output
    assert f"URL: {target_url}" in result.output
    assert (
        "Meldung: Die bevorzugte englische Übersetzung fehlt auf der "
        "englischen Zielseite." in result.output
    )
    assert "Deutscher Ausgangsbegriff: Technische Universität Dortmund" in result.output
    assert "Begleitservice" in result.output
    assert "accompaniment service" in result.output
    assert "escort service" in result.output

    assert "Erwartete englische Übersetzung: TU Dortmund University" in result.output
    assert "Meldung: Nicht bevorzugte TU-Terminologie." in result.output
    assert f"PDF-Bericht: {pdf_report_path}" in result.output
    assert written_pdf_reports
    assert (
        next(
            finding
            for finding in written_pdf_reports[0][1]["findings"]
            if finding.source_term == "Begleitservice"
        ).target_context
        == "Dortmund University of Technology provides an escort service."
    )


def test_check_translation_applies_tu_terminology_only_to_matching_languages(
    monkeypatch,
    tmp_path,
) -> None:
    """Der Übersetzungscheck prüft TU-Terminologie nur in passenden Sprachblöcken."""
    config_path = tmp_path / "config.yaml"
    german_terminology_path = tmp_path / "tu-de-terminology.local.json"
    english_terminology_path = tmp_path / "tu-terminology.local.json"
    german_terminology_path.write_text(
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
    english_terminology_path.write_text(
        """\
{
  "schema_version": 1,
  "entries": [
    {
      "german": "Universität",
      "preferred_english": "TU Dortmund University",
      "variants_to_flag": ["Technical University of Dortmund"]
    }
  ]
}
""",
        encoding="utf-8",
    )
    config = ProjectConfig(
        profile="tu",
        crawl=CrawlConfig(
            allowed_domains=["example.org"],
            max_depth=1,
            max_pages=10,
            requests_per_second=1.0,
            obey_robots_txt=True,
        ),
        check={
            "language": "de-DE",
            "german_terminology_path": german_terminology_path,
            "english_terminology_path": english_terminology_path,
        },
    )
    source_url = "https://example.org/de/testseite/"
    target_url = "https://example.org/en/test-page/"
    page_content = PageContent(
        title="Testseite",
        text=(
            "Die Lehrer informieren über die Technical University of Dortmund.\n"
            "The Technical University of Dortmund mentions Lehrer."
        ),
        blocks=(
            TextBlock(
                text=(
                    "Die Lehrer informieren über die Technical University of Dortmund."
                ),
                language="de",
            ),
            TextBlock(
                text="The Technical University of Dortmund mentions Lehrer.",
                language="en",
            ),
        ),
    )

    monkeypatch.setattr(
        "tu_web_linguacheck.cli.load_project_config",
        lambda _path: config,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.prepare_crawl_url",
        lambda url, _crawl_config: url,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.fetch_html",
        lambda url, _allowed_domains: (
            "german-html" if url == source_url else "english-html"
        ),
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.extract_page_content",
        lambda _html: page_content,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.find_allowed_page_language_links",
        lambda *_args: [type("Link", (), {"href": target_url, "language": "en"})()],
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.LanguageToolClient.check",
        lambda _self, *, text, language: [],
    )

    result = runner.invoke(
        app,
        ["check-translation", source_url, str(config_path)],
    )

    assert result.exit_code == 0
    assert "Sprachfunde: 4" in result.output
    assert result.output.count("Regel: TU_DE_INCLUSIVE_LANGUAGE") == 2
    assert result.output.count("Regel: TU_EN_TERMINOLOGY") == 2
