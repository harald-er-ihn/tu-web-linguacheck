"""Tests für die Kommandozeilenschnittstelle."""

from typer.testing import CliRunner

from tu_web_linguacheck.cli import app
from tu_web_linguacheck.html_content import PageContent
from tu_web_linguacheck.language_links import LanguageLink
from tu_web_linguacheck.languagetool import LanguageToolMatch

runner = CliRunner()


def test_help_displays_project_name_and_run_command() -> None:
    """Die CLI-Hilfe nennt den Projektnamen und den Platzhalterbefehl."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "tu-web-linguacheck" in result.output
    assert "run" in result.output


def test_version_displays_package_version() -> None:
    """Die CLI gibt ihre Paketversion aus."""
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.output == "0.1.0\n"


def test_inspect_displays_detected_translation_links(monkeypatch) -> None:
    """Der Inspect-Befehl zeigt erkannte Übersetzungsziele an."""

    def fake_fetch_html(url: str, allowed_domains: list[str]) -> str:
        assert url == "https://example.tu-dortmund.de/de/page/"
        assert allowed_domains == ["tu-dortmund.de"]

        return "<html></html>"

    def fake_extract_page_content(html: str) -> PageContent:
        assert html == "<html></html>"

        return PageContent(
            title="Testseite",
            text="Dies ist ein sichtbarer Testinhalt.",
        )

    def fake_find_allowed_page_language_links(
        base_url: str,
        html: str,
        allowed_domains: list[str],
    ) -> list[LanguageLink]:
        assert base_url == "https://example.tu-dortmund.de/de/page/"
        assert html == "<html></html>"
        assert allowed_domains == ["tu-dortmund.de"]

        return [
            LanguageLink(href, language, "hreflang")
            for href, language in [
                ("https://example.tu-dortmund.de/de/page/", "de"),
                ("https://example.tu-dortmund.de/en/page/", "en"),
            ]
        ]

    def fake_find_translation_links(
        language_links: list[LanguageLink],
        source_language: str,
    ) -> list[LanguageLink]:
        assert source_language == "de"

        return language_links[1:]

    monkeypatch.setattr(
        "tu_web_linguacheck.cli.fetch_html",
        fake_fetch_html,
    )

    monkeypatch.setattr(
        "tu_web_linguacheck.cli.extract_page_content",
        fake_extract_page_content,
    )

    monkeypatch.setattr(
        "tu_web_linguacheck.cli.find_allowed_page_language_links",
        fake_find_allowed_page_language_links,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.find_translation_links",
        fake_find_translation_links,
    )

    result = runner.invoke(
        app,
        [
            "inspect",
            "https://example.tu-dortmund.de/de/page/",
            "--allowed-domain",
            "tu-dortmund.de",
            "--source-language",
            "de",
        ],
    )

    assert result.exit_code == 0
    assert "HTML-Zeichen: 13" in result.output
    assert "Erkannte erlaubte Sprachlinks: 2" in result.output
    assert "Englische Übersetzungsziele: 1" in result.output
    assert "https://example.tu-dortmund.de/en/page/ [hreflang]" in result.output
    assert "Titel: Testseite" in result.output
    assert "Extrahierte Textzeichen: 35" in result.output
    assert "Textvorschau: Dies ist ein sichtbarer Testinhalt." in result.output


def test_check_text_displays_normalized_findings(monkeypatch) -> None:
    """Der Check-Text-Befehl zeigt normalisierte lokale Sprachfunde an."""

    def fake_check(
        _self: object,
        *,
        text: str,
        language: str,
    ) -> list[LanguageToolMatch]:
        assert text == "Das istf ein Test."
        assert language == "de-DE"

        return [
            LanguageToolMatch(
                message="Möglicher Rechtschreibfehler gefunden.",
                offset=4,
                length=4,
                rule_id="GERMAN_SPELLER_RULE",
                category="TYPOS",
                issue_type="misspelling",
                replacements=("ist",),
            )
        ]

    monkeypatch.setattr(
        "tu_web_linguacheck.cli.LanguageToolClient.check",
        fake_check,
    )

    result = runner.invoke(
        app,
        [
            "check-text",
            "Das istf ein Test.",
            "--language",
            "de-DE",
            "--url",
            "https://example.org/test/",
            "--profile",
            "generic-de",
        ],
    )

    assert result.exit_code == 0
    assert "Sprachfunde: 1" in result.output
    assert "Kategorie: misspelling" in result.output
    assert "Schweregrad: warning" in result.output
    assert "Regel: GERMAN_SPELLER_RULE" in result.output
    assert "Vorschläge: ist" in result.output
    assert "Fundstelle: istf" in result.output
    assert "Position: 4–8" in result.output
    assert "Kontext: Das istf ein Test." in result.output


def test_validate_config_accepts_valid_local_yaml(tmp_path) -> None:
    """Der CLI-Befehl bestätigt eine gültige lokale Konfiguration."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
profile: generic-de
crawl:
  allowed_domains:
    - example.org
  max_depth: 1
  max_pages: 10
  requests_per_second: 1.0
  obey_robots_txt: true
""".lstrip(),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate-config", str(config_path)])

    assert result.exit_code == 0
    assert "Konfiguration gültig." in result.output
    assert "Profil: generic-de" in result.output
    assert "Erlaubte Domains: example.org" in result.output


def test_validate_config_reports_invalid_values(tmp_path) -> None:
    """Der CLI-Befehl meldet ungültige Konfigurationswerte verständlich."""
    config_path = tmp_path / "invalid-config.yaml"
    config_path.write_text(
        """
profile: generic-de
crawl:
  allowed_domains:
    - example.org
  max_depth: 1
  max_pages: 0
  requests_per_second: 1.0
  obey_robots_txt: true
""".lstrip(),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate-config", str(config_path)])

    assert result.exit_code == 1
    assert "Konfiguration ungültig." in result.output
    assert "max_pages" in result.output
    assert "Traceback" not in result.output
