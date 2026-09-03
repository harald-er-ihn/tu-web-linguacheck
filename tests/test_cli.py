"""Tests für die Kommandozeilenschnittstelle."""

# pylint: disable=duplicate-code
from typer.testing import CliRunner

from tu_web_linguacheck.cli import _check_page_blocks, _check_page_text, app
from tu_web_linguacheck.config import CrawlConfig, ProjectConfig
from tu_web_linguacheck.html_content import PageContent, TextBlock
from tu_web_linguacheck.language_links import LanguageLink
from tu_web_linguacheck.languagetool import (
    LanguageToolMatch,
    LanguageToolUnavailableError,
)

runner = CliRunner()


def test_check_page_text_checks_blocks_with_global_offsets(monkeypatch) -> None:
    """Die Seitenprüfung verbindet Blockfunde mit dem gesamten Seitenkontext."""
    checked_texts: list[str] = []

    def fake_check(_self, *, text: str, language: str) -> list[LanguageToolMatch]:
        assert language == "de-DE"
        checked_texts.append(text)

        if text == "Das istf ein Test.":
            return [
                LanguageToolMatch(
                    message="Testmeldung.",
                    offset=4,
                    length=4,
                    rule_id="TEST_RULE",
                    category="TEST",
                    issue_type="misspelling",
                    replacements=("ist",),
                )
            ]

        return []

    monkeypatch.setattr(
        "tu_web_linguacheck.cli.LanguageToolClient.check",
        fake_check,
    )

    text = "Überschrift\nDas istf ein Test."
    findings, checked_blocks = _check_page_text(
        text,
        language="de-DE",
        url="https://example.org/startseite/",
        profile="generic-de",
    )

    assert checked_texts == ["Überschrift", "Das istf ein Test."]
    assert checked_blocks == 2
    assert len(findings) == 1
    assert findings[0].offset == 16
    assert findings[0].context == text


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
    assert "Meldung: Möglicher Rechtschreibfehler gefunden." in result.output
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


def test_check_url_checks_one_allowed_html_page(monkeypatch, tmp_path) -> None:
    """Der Check-URL-Befehl prüft genau eine erlaubte HTML-Seite lokal."""

    config_path = tmp_path / "config.yaml"
    config = ProjectConfig(
        profile="generic-de",
        crawl=CrawlConfig(
            allowed_domains=["example.org"],
            max_depth=1,
            max_pages=10,
            requests_per_second=1.0,
            obey_robots_txt=True,
        ),
        check={
            "language": "de-DE",
            "ignored_rule_ids": ["DE_SIMPLE_REPLACE_QI_GONG"],
            "ignored_terms": ["istf"],
        },
    )

    def fake_load_project_config(path):
        assert path == config_path
        return config

    def fake_prepare_crawl_url(url, crawl_config):
        assert url == "https://example.org/startseite/"
        assert crawl_config == config.crawl
        return "https://example.org/startseite/"

    def fake_fetch_html(url, allowed_domains):
        assert url == "https://example.org/startseite/"
        assert allowed_domains == ["example.org"]
        return "<html><body><main>Das istf ein Test.</main></body></html>"

    def fake_extract_page_content(html):
        assert "<main>Das istf ein Test.</main>" in html
        return PageContent(
            title="Testseite",
            text="Das istf ein Test.",
        )

    def fake_check(_self, *, text, language, disabled_rule_ids):
        assert text == "Das istf ein Test."
        assert language == "de-DE"
        assert disabled_rule_ids == ["DE_SIMPLE_REPLACE_QI_GONG"]

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
        "tu_web_linguacheck.cli.load_project_config",
        fake_load_project_config,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.prepare_crawl_url",
        fake_prepare_crawl_url,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.fetch_html",
        fake_fetch_html,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.extract_page_content",
        fake_extract_page_content,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.LanguageToolClient.check",
        fake_check,
    )

    result = runner.invoke(
        app,
        [
            "check-url",
            "https://example.org/startseite/",
            str(config_path),
        ],
    )

    assert result.exit_code == 0
    assert "URL: https://example.org/startseite/" in result.output
    assert "Titel: Testseite" in result.output
    assert "Extrahierte Textzeichen: 18" in result.output
    assert "Sprachfunde: 0" in result.output
    assert "Fundstelle: istf" not in result.output


def test_check_text_limits_long_context_to_match_surroundings(monkeypatch) -> None:
    """Der Check-Text-Befehl kürzt langen Kontext um die Fundstelle."""
    text = f"{'a' * 100}istf{'b' * 100}"

    def fake_check(_self, *, text: str, language: str) -> list[LanguageToolMatch]:
        assert text == f"{'a' * 100}istf{'b' * 100}"
        assert language == "de-DE"

        return [
            LanguageToolMatch(
                message="Möglicher Rechtschreibfehler gefunden.",
                offset=100,
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
            text,
            "--language",
            "de-DE",
            "--url",
            "https://example.org/test/",
            "--profile",
            "generic-de",
        ],
    )

    expected_context = f"Kontext: …{'a' * 80}istf{'b' * 80}…"

    assert result.exit_code == 0
    assert expected_context in result.output
    assert f"Kontext: {text}" not in result.output


def test_check_url_checks_extracted_text_blocks_separately(
    monkeypatch,
    tmp_path,
) -> None:
    """Der Check-URL-Befehl prüft getrennte Textblöcke einzeln."""
    config_path = tmp_path / "config.yaml"
    config = ProjectConfig(
        profile="generic-de",
        crawl=CrawlConfig(
            allowed_domains=["example.org"],
            max_depth=1,
            max_pages=10,
            requests_per_second=1.0,
            obey_robots_txt=True,
        ),
    )

    checked_blocks: list[tuple[str, str]] = []

    def fake_load_project_config(path):
        assert path == config_path
        return config

    def fake_prepare_crawl_url(url, crawl_config):
        assert url == "https://example.org/startseite/"
        assert crawl_config == config.crawl
        return "https://example.org/startseite/"

    def fake_fetch_html(url, allowed_domains):
        assert url == "https://example.org/startseite/"
        assert allowed_domains == ["example.org"]
        return "<html></html>"

    def fake_extract_page_content(html):
        assert html == "<html></html>"

        return PageContent(
            title="Testseite",
            text="Überschrift\nEnglish text.",
            blocks=(
                TextBlock(text="Überschrift", language="de"),
                TextBlock(text="English text.", language="en"),
            ),
        )

    def fake_check(_self, *, text, language):
        checked_blocks.append((text, language))

        if text == "Überschrift":
            return [
                LanguageToolMatch(
                    message="Testmeldung.",
                    offset=0,
                    length=2,
                    rule_id="TEST_RULE",
                    category="TEST",
                    issue_type="grammar",
                    replacements=(),
                )
            ]

        return []

    monkeypatch.setattr(
        "tu_web_linguacheck.cli.load_project_config",
        fake_load_project_config,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.prepare_crawl_url",
        fake_prepare_crawl_url,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.fetch_html",
        fake_fetch_html,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.extract_page_content",
        fake_extract_page_content,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.LanguageToolClient.check",
        fake_check,
    )

    result = runner.invoke(
        app,
        [
            "check-url",
            "https://example.org/startseite/",
            str(config_path),
        ],
    )

    assert result.exit_code == 0
    assert checked_blocks == [
        ("Überschrift", "de-DE"),
        ("English text.", "en-US"),
    ]
    assert "Prüfblöcke: 2" in result.output
    assert "Sprachfunde: 1" in result.output
    assert "Fundstelle: Üb" in result.output
    assert "Position: 0–2" in result.output


def test_check_text_reports_unavailable_local_languagetool_server(
    monkeypatch,
) -> None:
    """Der Check-Text-Befehl meldet einen nicht erreichbaren Dienst klar."""

    def fake_check(_self, *, text: str, language: str) -> list[LanguageToolMatch]:
        assert text == "Ein Test."
        assert language == "de-DE"
        raise LanguageToolUnavailableError(
            "Der lokale LanguageTool-Server unter 127.0.0.1:8081 ist nicht erreichbar."
        )

    monkeypatch.setattr(
        "tu_web_linguacheck.cli.LanguageToolClient.check",
        fake_check,
    )
    result = runner.invoke(
        app,
        [
            "check-text",
            "Ein Test.",
            "--language",
            "de-DE",
            "--url",
            "https://example.org/test/",
            "--profile",
            "generic-de",
        ],
    )
    assert result.exit_code == 1
    assert "127.0.0.1:8081 ist nicht erreichbar." in result.output
    assert "Traceback" not in result.output


def test_check_url_reports_unavailable_local_languagetool_server(
    monkeypatch,
    tmp_path,
) -> None:
    """Der Check-URL-Befehl meldet einen nicht erreichbaren Dienst klar."""
    config_path = tmp_path / "config.yaml"
    config = ProjectConfig(
        profile="generic-de",
        crawl=CrawlConfig(
            allowed_domains=["example.org"],
            max_depth=1,
            max_pages=10,
            requests_per_second=1.0,
            obey_robots_txt=True,
        ),
    )

    def fake_load_project_config(path):
        assert path == config_path
        return config

    def fake_prepare_crawl_url(url, crawl_config):
        assert url == "https://example.org/startseite/"
        assert crawl_config == config.crawl
        return "https://example.org/startseite/"

    def fake_fetch_html(url, allowed_domains):
        assert url == "https://example.org/startseite/"
        assert allowed_domains == ["example.org"]
        return "<html></html>"

    def fake_extract_page_content(html):
        assert html == "<html></html>"
        return PageContent(title="Testseite", text="Ein Test.")

    def fake_check(_self, *, text: str, language: str) -> list[LanguageToolMatch]:
        assert text == "Ein Test."
        assert language == "de-DE"
        raise LanguageToolUnavailableError(
            "Der lokale LanguageTool-Server unter 127.0.0.1:8081 ist nicht erreichbar."
        )

    monkeypatch.setattr(
        "tu_web_linguacheck.cli.load_project_config",
        fake_load_project_config,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.prepare_crawl_url",
        fake_prepare_crawl_url,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.fetch_html",
        fake_fetch_html,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.extract_page_content",
        fake_extract_page_content,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.LanguageToolClient.check",
        fake_check,
    )

    result = runner.invoke(
        app,
        [
            "check-url",
            "https://example.org/startseite/",
            str(config_path),
        ],
    )

    assert result.exit_code == 1
    assert "127.0.0.1:8081 ist nicht erreichbar." in result.output
    assert "Traceback" not in result.output


def test_check_crawl_checks_content_of_crawled_pages(monkeypatch, tmp_path) -> None:
    """Der Crawl-Check prüft die sichtbaren Inhalte aller gecrawlten Seiten."""
    config_path = tmp_path / "config.yaml"
    config = ProjectConfig(
        profile="tu-de",
        crawl=CrawlConfig(
            allowed_domains=["example.org"],
            max_depth=3,
            max_pages=10,
            requests_per_second=1.0,
            obey_robots_txt=True,
        ),
    )

    def fake_load_project_config(path):
        assert path == config_path
        return config

    def fake_crawl_pages_with_content(*, start_url, config):
        assert start_url == "https://example.org/"
        assert config.max_depth == 3

        return [
            type(
                "Page",
                (),
                {
                    "url": "https://example.org/",
                    "depth": 0,
                    "title": "Startseite",
                    "text": "Ein Test.",
                    "blocks": (TextBlock(text="Ein Test.", language="de"),),
                },
            )(),
            type(
                "Page",
                (),
                {
                    "url": "https://example.org/seite/",
                    "depth": 1,
                    "title": "Unterseite",
                    "text": "English text.",
                    "blocks": (TextBlock(text="English text.", language="en"),),
                },
            )(),
        ]

    checked_blocks: list[tuple[str, str]] = []

    def fake_check(_self, *, text: str, language: str) -> list[LanguageToolMatch]:
        checked_blocks.append((text, language))
        return []

    monkeypatch.setattr(
        "tu_web_linguacheck.cli.load_project_config",
        fake_load_project_config,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.crawl_pages_with_content",
        fake_crawl_pages_with_content,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.LanguageToolClient.check",
        fake_check,
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
    assert checked_blocks == [
        ("Ein Test.", "de-DE"),
        ("English text.", "en-US"),
    ]
    assert "Gecrawlte Seiten: 2" in result.output
    assert "Prüfblöcke: 2" in result.output
    assert "Sprachfunde: 0" in result.output


def test_check_crawl_displays_url_for_each_finding(monkeypatch, tmp_path) -> None:
    """Der Crawl-Check ordnet jeden Sprachfund seiner Seiten-URL zu."""
    config_path = tmp_path / "config.yaml"
    config = ProjectConfig(
        profile="tu-de",
        crawl=CrawlConfig(
            allowed_domains=["example.org"],
            max_depth=3,
            max_pages=10,
            requests_per_second=1.0,
            obey_robots_txt=True,
        ),
    )

    def fake_load_project_config(path):
        assert path == config_path
        return config

    def fake_crawl_pages_with_content(*, start_url, config):
        assert start_url == "https://example.org/"
        assert config.max_depth == 3

        return [
            type(
                "Page",
                (),
                {
                    "url": "https://example.org/seite/",
                    "depth": 1,
                    "title": "Unterseite",
                    "text": "Das istf ein Test.",
                    "blocks": (),
                },
            )(),
        ]

    def fake_check(_self, *, text: str, language: str) -> list[LanguageToolMatch]:
        assert text == "Das istf ein Test."
        assert language == "de-DE"

        return [
            LanguageToolMatch(
                message="Testmeldung.",
                offset=4,
                length=4,
                rule_id="TEST_RULE",
                category="TEST",
                issue_type="misspelling",
                replacements=("ist",),
            )
        ]

    monkeypatch.setattr(
        "tu_web_linguacheck.cli.load_project_config",
        fake_load_project_config,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.crawl_pages_with_content",
        fake_crawl_pages_with_content,
    )
    monkeypatch.setattr(
        "tu_web_linguacheck.cli.LanguageToolClient.check",
        fake_check,
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
    assert "URL: https://example.org/seite/" in result.output


def test_check_page_blocks_uses_en_us_for_english_html_blocks(
    monkeypatch,
) -> None:
    """Englische HTML-Blöcke werden mit dem en-US-Prüfcode geprüft."""
    checked_languages: list[tuple[str, str]] = []

    def fake_check(_self, *, text: str, language: str) -> list[LanguageToolMatch]:
        checked_languages.append((text, language))
        return []

    monkeypatch.setattr(
        "tu_web_linguacheck.cli.LanguageToolClient.check",
        fake_check,
    )

    findings, checked_blocks = _check_page_blocks(
        (
            TextBlock(text="Deutscher Text.", language="de"),
            TextBlock(text="English text.", language="en"),
        ),
        language="de-DE",
        url="https://example.org/startseite/",
        profile="generic-de",
    )

    assert not findings
    assert checked_blocks == 2
    assert checked_languages == [
        ("Deutscher Text.", "de-DE"),
        ("English text.", "en-US"),
    ]
