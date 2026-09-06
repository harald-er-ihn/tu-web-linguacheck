"""Kommandozeilenschnittstelle für tu-web-linguacheck."""

from collections.abc import Sequence
from pathlib import Path

import typer
from pydantic import ValidationError

from tu_web_linguacheck import __version__
from tu_web_linguacheck.config import load_project_config
from tu_web_linguacheck.crawler import crawl_pages_with_content
from tu_web_linguacheck.findings import (
    filter_ignored_terms,
    finding_from_languagetool_match,
    finding_from_terminology_match,
)
from tu_web_linguacheck.html_content import TextBlock, extract_page_content
from tu_web_linguacheck.http import fetch_html
from tu_web_linguacheck.language_links import (
    find_allowed_page_language_links,
    find_translation_links,
)
from tu_web_linguacheck.languagetool import (
    LanguageToolClient,
    LanguageToolUnavailableError,
)
from tu_web_linguacheck.models import Finding
from tu_web_linguacheck.report import write_html_report
from tu_web_linguacheck.terminology import find_terminology_matches, load_terminology
from tu_web_linguacheck.urls import prepare_crawl_url

app = typer.Typer(
    help=(
        "Prüft öffentlich erreichbare Websites lokal auf sprachliche "
        "Auffälligkeiten.\n\n"
        "Schnellstart für eine einzelne Seite:\n"
        "  tu-web-linguacheck check-url URL CONFIG_PATH --report DATEI.html\n\n"
        "URL ist die Webadresse. CONFIG_PATH ist eine lokale "
        "YAML-Konfigurationsdatei.\n"
        "--report DATEI.html erstellt optional einen lokalen HTML-Bericht.\n\n"
        "Weitere Argumente und Optionen: tu-web-linguacheck COMMAND --help"
    ),
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


def _check_text_findings(
    text: str,
    *,
    language: str,
    url: str,
    profile: str,
    disabled_rule_ids: Sequence[str] = (),
    ignored_terms: Sequence[str] = (),
) -> list[Finding]:
    """Prüft Text lokal und überführt Ergebnisse in interne Funde."""
    client = LanguageToolClient()

    if disabled_rule_ids:
        matches = client.check(
            text=text,
            language=language,
            disabled_rule_ids=disabled_rule_ids,
        )
    else:
        matches = client.check(text=text, language=language)

    findings = [
        finding_from_languagetool_match(
            match,
            url=url,
            context=text,
            profile=profile,
        )
        for match in matches
    ]

    return filter_ignored_terms(
        findings,
        ignored_terms=list(ignored_terms),
    )


def _display_findings(findings: Sequence[Finding]) -> None:
    """Gibt Sprachfunde lesbar in der Kommandozeile aus."""
    typer.echo(f"Sprachfunde: {len(findings)}")

    for finding in findings:
        typer.echo(f"URL: {finding.url}")
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
    try:
        findings = _check_text_findings(
            text,
            language=language,
            url=url,
            profile=profile,
        )
    except LanguageToolUnavailableError as error:
        typer.echo(str(error))
        raise typer.Exit(code=1) from error
    _display_findings(findings)


@app.command()
def check_url(
    url: str,
    config_path: Path,
    report_path: Path | None = typer.Option(
        None, "--report", help="Schreibt einen HTML-Bericht in die angegebene Datei."
    ),
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

    try:
        if page_content.blocks:
            findings, checked_blocks = _check_page_blocks(
                page_content.blocks,
                language=config.check.language,
                url=prepared_url,
                profile=config.profile,
                disabled_rule_ids=config.check.ignored_rule_ids,
                ignored_terms=config.check.ignored_terms,
            )
        else:
            findings, checked_blocks = _check_page_text(
                page_content.text,
                language=config.check.language,
                url=prepared_url,
                profile=config.profile,
                disabled_rule_ids=config.check.ignored_rule_ids,
                ignored_terms=config.check.ignored_terms,
            )
    except LanguageToolUnavailableError as error:
        typer.echo(str(error))
        raise typer.Exit(code=1) from error

    if config.check.terminology_path is not None:
        terminology_entries = load_terminology(config.check.terminology_path)
        findings.extend(
            finding_from_terminology_match(
                match,
                url=prepared_url,
                context=page_content.text,
                profile=config.profile,
            )
            for match in find_terminology_matches(
                page_content.text,
                terminology_entries,
            )
        )

    typer.echo(f"Prüfblöcke: {checked_blocks}")
    _display_findings(findings)

    if report_path is not None:
        write_html_report(
            report_path,
            crawled_pages=1,
            checked_blocks=checked_blocks,
            findings=findings,
        )
        typer.echo(f"HTML-Bericht: {report_path}")


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


def _check_page_text(
    text: str,
    *,
    language: str,
    url: str,
    profile: str,
    disabled_rule_ids: Sequence[str] = (),
    ignored_terms: Sequence[str] = (),
) -> tuple[list[Finding], int]:
    """Prüft nichtleere Textblöcke mit globalen Offsets und Seitenkontext."""
    findings: list[Finding] = []
    checked_blocks = 0
    block_offset = 0

    for line in text.splitlines(keepends=True):
        block = line.rstrip("\r\n")

        if block:
            checked_blocks += 1
            block_findings = _check_text_findings(
                block,
                language=language,
                url=url,
                profile=profile,
                disabled_rule_ids=disabled_rule_ids,
                ignored_terms=ignored_terms,
            )
            findings.extend(
                finding.model_copy(
                    update={
                        "context": text,
                        "offset": finding.offset + block_offset,
                    }
                )
                for finding in block_findings
            )

        block_offset += len(line)

    return findings, checked_blocks


def _check_page_blocks(
    blocks: tuple[TextBlock, ...],
    *,
    language: str,
    url: str,
    profile: str,
    disabled_rule_ids: Sequence[str] = (),
    ignored_terms: Sequence[str] = (),
) -> tuple[list[Finding], int]:
    """Prüft Textblöcke mit ihrer HTML-Sprache und globalen Offsets."""
    findings: list[Finding] = []
    context = "\n".join(block.text for block in blocks)
    block_offset = 0

    for block in blocks:
        is_english = block.language is not None and (
            block.language.casefold() == "en"
            or block.language.casefold().startswith("en-")
        )
        block_language = "en-US" if is_english else language
        block_findings = _check_text_findings(
            block.text,
            language=block_language,
            url=url,
            profile=profile,
            disabled_rule_ids=disabled_rule_ids,
            ignored_terms=ignored_terms,
        )
        findings.extend(
            finding.model_copy(
                update={
                    "context": context,
                    "offset": finding.offset + block_offset,
                }
            )
            for finding in block_findings
        )
        block_offset += len(block.text) + 1

    return findings, len(blocks)


@app.command()
def check_crawl(
    url: str,
    config_path: Path,
    report_path: Path | None = typer.Option(
        None,
        "--report",
        help="Schreibt einen HTML-Bericht in die angegebene Datei.",
    ),
) -> None:
    """Crawlt erlaubte HTML-Seiten und prüft ihre sichtbaren Texte lokal."""
    config = load_project_config(config_path)

    try:
        LanguageToolClient().check(
            text="",
            language=config.check.language,
        )
    except LanguageToolUnavailableError as error:
        typer.echo(str(error))
        raise typer.Exit(code=1) from error

    pages = crawl_pages_with_content(
        start_url=url,
        config=config.crawl,
        on_progress=lambda number, candidate: typer.echo(
            f"Crawle Seite {number}/{config.crawl.max_pages}: {candidate.url}"
        ),
        on_error=lambda candidate, error: typer.echo(
            f"Überspringe Seite wegen Abruffehler: {candidate.url} ({error})"
        ),
    )
    findings: list[Finding] = []
    checked_blocks = 0

    terminology_entries = None
    if config.check.terminology_path is not None:
        terminology_entries = load_terminology(config.check.terminology_path)

    try:
        for page in pages:
            if page.blocks:
                page_findings, page_checked_blocks = _check_page_blocks(
                    page.blocks,
                    language=config.check.language,
                    url=page.url,
                    profile=config.profile,
                    disabled_rule_ids=config.check.ignored_rule_ids,
                    ignored_terms=config.check.ignored_terms,
                )
            else:
                page_findings, page_checked_blocks = _check_page_text(
                    page.text,
                    language=config.check.language,
                    url=page.url,
                    profile=config.profile,
                    disabled_rule_ids=config.check.ignored_rule_ids,
                    ignored_terms=config.check.ignored_terms,
                )
            if terminology_entries is not None:
                findings.extend(
                    finding_from_terminology_match(
                        match,
                        url=page.url,
                        context=page.text,
                        profile=config.profile,
                    )
                    for match in find_terminology_matches(
                        page.text,
                        terminology_entries,
                    )
                )
            findings.extend(page_findings)
            checked_blocks += page_checked_blocks
    except LanguageToolUnavailableError as error:
        typer.echo(str(error))
        raise typer.Exit(code=1) from error

    typer.echo(f"Gecrawlte Seiten: {len(pages)}")
    typer.echo(f"Prüfblöcke: {checked_blocks}")
    _display_findings(findings)

    if report_path is not None:
        write_html_report(
            report_path,
            crawled_pages=len(pages),
            checked_blocks=checked_blocks,
            findings=findings,
        )
        typer.echo(f"HTML-Bericht: {report_path}")
