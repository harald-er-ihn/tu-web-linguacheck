"""Kommandozeilenschnittstelle für tu-web-linguacheck."""

from pathlib import Path

import typer
from pydantic import ValidationError

from tu_web_linguacheck import __version__
from tu_web_linguacheck.config import load_project_config
from tu_web_linguacheck.findings import finding_from_languagetool_match
from tu_web_linguacheck.html_content import extract_page_content
from tu_web_linguacheck.http import fetch_html
from tu_web_linguacheck.language_links import (
    find_allowed_page_language_links,
    find_translation_links,
)
from tu_web_linguacheck.languagetool import LanguageToolClient
from tu_web_linguacheck.urls import prepare_crawl_url

app = typer.Typer(
    help="Prüft öffentlich erreichbare Websites lokal auf sprachliche Auffälligkeiten.",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    """Gibt die installierte Programmversion aus."""
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def callback(
    _version: bool = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Zeigt die Programmversion an und beendet das Programm.",
    ),
) -> None:
    """Stellt die Befehlsgruppe bereit."""


@app.command()
def run() -> None:
    """Startet tu-web-linguacheck."""
    typer.echo("tu-web-linguacheck ist bereit.")


@app.command()
def inspect(
    url: str,
    allowed_domains: list[str] = typer.Option(
        ...,
        "--allowed-domain",
        help="Erlaubte Domain; Option kann mehrfach angegeben werden.",
    ),
    source_language: str = typer.Option(
        ...,
        "--source-language",
        help="Sprache der untersuchten Ausgangsseite, zum Beispiel de oder en.",
    ),
) -> None:
    """Ruft eine einzelne erlaubte HTML-Seite ab und zeigt Sprachlinks an."""
    html = fetch_html(url, allowed_domains)
    page_content = extract_page_content(html)
    language_links = find_allowed_page_language_links(
        url,
        html,
        allowed_domains,
    )
    translation_links = find_translation_links(language_links, source_language)

    typer.echo(f"Titel: {page_content.title}")
    typer.echo(f"Extrahierte Textzeichen: {len(page_content.text)}")
    typer.echo(f"Textvorschau: {page_content.text[:500]}")
    typer.echo(f"HTML-Zeichen: {len(html)}")
    typer.echo(f"Erkannte erlaubte Sprachlinks: {len(language_links)}")

    for language_link in language_links:
        typer.echo(
            f"- {language_link.language}: {language_link.href} "
            f"[{language_link.detection_method}]"
        )

    if source_language.casefold() == "de":
        translation_heading = "Englische Übersetzungsziele"
    elif source_language.casefold() == "en":
        translation_heading = "Deutsche Übersetzungsziele"
    else:
        translation_heading = "Übersetzungsziele"

    typer.echo(f"{translation_heading}: {len(translation_links)}")

    for language_link in translation_links:
        typer.echo(f"- {language_link.href} [{language_link.detection_method}]")


@app.command()
def check_text(
    text: str,
    language: str = typer.Option(
        ...,
        "--language",
        help="LanguageTool-Sprachcode, zum Beispiel de-DE oder en-US.",
    ),
    url: str = typer.Option(
        ...,
        "--url",
        help="Herkunfts-URL für die gespeicherten Sprachfunde.",
    ),
    profile: str = typer.Option(
        ...,
        "--profile",
        help="Prüfprofil, zum Beispiel generic-de.",
    ),
) -> None:
    """Prüft Text ausschließlich mit dem lokalen LanguageTool-Server."""
    matches = LanguageToolClient().check(text=text, language=language)
    findings = [
        finding_from_languagetool_match(
            match,
            url=url,
            context=text,
            profile=profile,
        )
        for match in matches
    ]

    typer.echo(f"Sprachfunde: {len(findings)}")

    for finding in findings:
        matched_text = finding.context[finding.offset : finding.offset + finding.length]
        end_offset = finding.offset + finding.length

        typer.echo(f"Kategorie: {finding.category}")
        typer.echo(f"Meldung: {finding.message}")
        typer.echo(f"Schweregrad: {finding.severity}")
        typer.echo(f"Regel: {finding.source_rule_id}")
        typer.echo(f"Vorschläge: {', '.join(finding.suggestions) or '-'}")
        typer.echo(f"Fundstelle: {matched_text}")
        typer.echo(f"Position: {finding.offset}–{end_offset}")
        context_start = max(0, finding.offset - 80)
        context_end = min(len(finding.context), end_offset + 80)
        context = finding.context[context_start:context_end]

        if context_start > 0:
            context = f"…{context}"

        if context_end < len(finding.context):
            context = f"{context}…"

        typer.echo(f"Kontext: {context}")


@app.command()
def check_url(
    url: str,
    config_path: Path,
) -> None:
    """Prüft genau eine erlaubte HTML-Seite mit lokalem LanguageTool."""
    config = load_project_config(config_path)
    prepared_url = prepare_crawl_url(url, config.crawl)

    if prepared_url is None:
        typer.echo("URL ist gemäß Crawl-Konfiguration nicht erlaubt.")
        raise typer.Exit(code=1)

    html = fetch_html(prepared_url, config.crawl.allowed_domains)
    page_content = extract_page_content(html)

    typer.echo(f"URL: {prepared_url}")
    typer.echo(f"Titel: {page_content.title}")
    typer.echo(f"Extrahierte Textzeichen: {len(page_content.text)}")

    check_text(
        page_content.text,
        language=config.check.language,
        url=prepared_url,
        profile=config.profile,
    )


@app.command()
def validate_config(
    config_path: Path,
) -> None:
    """Lädt und validiert eine lokale YAML-Konfiguration."""
    try:
        config = load_project_config(config_path)
    except ValidationError as error:
        typer.echo("Konfiguration ungültig.")
        typer.echo(str(error))
        raise typer.Exit(code=1) from error

    typer.echo("Konfiguration gültig.")
    typer.echo(f"Profil: {config.profile}")
    typer.echo(f"Erlaubte Domains: {', '.join(config.crawl.allowed_domains)}")


def main() -> None:
    """Startet die Kommandozeilenschnittstelle."""
    app()
