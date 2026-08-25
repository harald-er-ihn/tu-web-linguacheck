"""Tests für die Kommandozeilenschnittstelle."""

from typer.testing import CliRunner

from tu_web_linguacheck.cli import app
from tu_web_linguacheck.language_links import LanguageLink

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
