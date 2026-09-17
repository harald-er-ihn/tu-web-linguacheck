"""Kommandozeilenschnittstelle für tu-web-linguacheck."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import typer
from pydantic import ValidationError

from tu_web_linguacheck.config import ProjectConfig, load_project_config
from tu_web_linguacheck.crawler import crawl_pages_with_content
from tu_web_linguacheck.findings import (
    filter_ignored_terms,
    finding_from_languagetool_match,
    finding_from_missing_english_translation,
    finding_from_terminology_match,
)
from tu_web_linguacheck.html_content import (
    PageContent,
    TextBlock,
    extract_page_content,
)
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
from tu_web_linguacheck.project_metadata import load_project_metadata
from tu_web_linguacheck.report import ReportContext, write_html_report, write_pdf_report
from tu_web_linguacheck.terminology import (
    find_missing_english_translations,
    find_terminology_matches,
    load_terminology,
)
from tu_web_linguacheck.urls import prepare_crawl_url

app = typer.Typer(
    help=(
        "Prüft öffentlich erreichbare Websites lokal auf sprachliche "
        "Auffälligkeiten.\n\n"
        "Schnellstart für eine einzelne Seite:\n"
        "  tu-web-linguacheck check-url URL CONFIG_PATH --report DATEI.html\n\n"
        "URL ist die Webadresse. CONFIG_PATH ist eine lokale "
        "YAML-Konfigurationsdatei.\n"
        "--report DATEI.html erstellt optional einen lokalen HTML-Bericht.\n"
        "--pdf-report DATEI.pdf erstellt optional einen lokalen PDF-Bericht.\n\n"
        "Weitere Argumente und Optionen: tu-web-linguacheck COMMAND --help"
    ),
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    """Gibt die installierte Programmversion aus."""
    if value:
        typer.echo(load_project_metadata().version)
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
        if finding.source_term is not None:
            typer.echo(f"Deutscher Ausgangsbegriff: {finding.source_term}")
            typer.echo(
                f"Erwartete englische Übersetzung: {', '.join(finding.suggestions)}"
            )
            typer.echo(f"Deutsche Quell-URL: {finding.source_url}")
        else:
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
    pdf_report_path: Path | None = typer.Option(
        None, "--pdf-report", help="Schreibt einen PDF-Bericht in die angegebene Datei."
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
            context=ReportContext(
                start_url=prepared_url,
                profile=config.profile,
                language=config.check.language,
                checked_urls=(prepared_url,),
            ),
        )
        typer.echo(f"HTML-Bericht: {report_path}")
    if pdf_report_path is not None:
        write_pdf_report(
            pdf_report_path,
            crawled_pages=1,
            checked_blocks=checked_blocks,
            findings=findings,
            context=ReportContext(
                start_url=prepared_url,
                profile=config.profile,
                language=config.check.language,
                checked_urls=(prepared_url,),
            ),
        )
        typer.echo(f"PDF-Bericht: {pdf_report_path}")


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
        configured_primary_language = language.split("-", maxsplit=1)[0]
        block_language = (
            language
            if block.language is None
            or block.language.casefold() == configured_primary_language.casefold()
            else "en-US"
            if block.language.casefold() == "en"
            else block.language
        )
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


def _find_terminology_in_language_blocks(
    blocks: tuple[TextBlock, ...],
    *,
    terminology_entries: tuple,
    language: str,
    url: str,
    profile: str,
) -> list[Finding]:
    """Findet Terminologie nur in Blöcken der angegebenen Primärsprache."""
    findings: list[Finding] = []
    context = "\n".join(block.text for block in blocks)
    block_offset = 0

    for block in blocks:
        block_primary_language = (
            block.language.split("-", maxsplit=1)[0].casefold()
            if block.language is not None
            else None
        )
        if block_primary_language == language:
            findings.extend(
                finding_from_terminology_match(
                    match,
                    url=url,
                    context=context,
                    profile=profile,
                ).model_copy(update={"offset": match.offset + block_offset})
                for match in find_terminology_matches(block.text, terminology_entries)
            )
        block_offset += len(block.text) + 1

    return findings


@dataclass(frozen=True)
class _ReportData:
    """Bündelt die gemeinsamen Daten für lokale Berichtsformate."""

    crawled_pages: int
    checked_blocks: int
    findings: Sequence[Finding]
    context: ReportContext


def _write_reports(
    *,
    report_path: Path | None,
    pdf_report_path: Path | None,
    report_data: _ReportData,
) -> None:
    """Schreibt angeforderte lokale HTML- und PDF-Berichte."""
    if report_path is not None:
        write_html_report(
            report_path,
            crawled_pages=report_data.crawled_pages,
            checked_blocks=report_data.checked_blocks,
            findings=report_data.findings,
            context=report_data.context,
        )
        typer.echo(f"HTML-Bericht: {report_path}")

    if pdf_report_path is not None:
        write_pdf_report(
            pdf_report_path,
            crawled_pages=report_data.crawled_pages,
            checked_blocks=report_data.checked_blocks,
            findings=report_data.findings,
            context=report_data.context,
        )
        typer.echo(f"PDF-Bericht: {pdf_report_path}")


@app.command()
def check_crawl(
    url: str,
    config_path: Path,
    stay_under_start_path: bool = typer.Option(
        False,
        "--stay-under-start-path",
        help="Beschränkt den Crawl auf den Startpfad und dessen Unterpfade.",
    ),
    report_path: Path | None = typer.Option(
        None,
        "--report",
        help="Schreibt einen HTML-Bericht in die angegebene Datei.",
    ),
    pdf_report_path: Path | None = typer.Option(
        None,
        "--pdf-report",
        help="Schreibt einen PDF-Bericht in die angegebene Datei.",
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
        stay_under_start_path=stay_under_start_path,
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

    report_data = _ReportData(
        crawled_pages=len(pages),
        checked_blocks=checked_blocks,
        findings=findings,
        context=ReportContext(
            start_url=url,
            profile=config.profile,
            language=config.check.language,
            checked_urls=tuple(page.url for page in pages),
        ),
    )
    _write_reports(
        report_path=report_path,
        pdf_report_path=pdf_report_path,
        report_data=report_data,
    )


def _target_context_for_source_offset(
    source_blocks: tuple[TextBlock, ...],
    target_blocks: tuple[TextBlock, ...],
    source_offset: int,
) -> str | None:
    """Liefert den Zielblock an der Position des deutschen Quellblocks."""
    block_offset = 0

    for index, block in enumerate(source_blocks):
        block_end = block_offset + len(block.text)
        if block_offset <= source_offset < block_end:
            return target_blocks[index].text if index < len(target_blocks) else None
        block_offset = block_end + 1

    return None


def _load_english_terminology(config: ProjectConfig):
    """Lädt die primäre und alle zusätzlichen englischen Terminologiequellen."""
    terminology_paths = [
        config.check.english_terminology_path,
        *config.check.additional_english_terminology_paths,
    ]
    return tuple(
        entry
        for terminology_path in terminology_paths
        if terminology_path is not None
        for entry in load_terminology(terminology_path)
    )


def _check_translation_page_contents(
    german_content: PageContent,
    english_content: PageContent,
    german_url: str,
    english_url: str,
    config: ProjectConfig,
) -> tuple[list[Finding], int]:
    """Prüft Quell- und Zielseite auf TU-Terminologie."""
    terminology_findings: list[Finding] = []
    if config.check.german_terminology_path is not None:
        german_terminology_entries = load_terminology(
            config.check.german_terminology_path
        )
        for content, url in (
            (german_content, german_url),
            (english_content, english_url),
        ):
            terminology_findings.extend(
                _find_terminology_in_language_blocks(
                    content.blocks,
                    terminology_entries=german_terminology_entries,
                    language="de",
                    url=url,
                    profile="tu-de",
                )
            )
    english_terminology_entries = _load_english_terminology(config)
    if english_terminology_entries:
        for content, url in (
            (german_content, german_url),
            (english_content, english_url),
        ):
            terminology_findings.extend(
                _find_terminology_in_language_blocks(
                    content.blocks,
                    terminology_entries=english_terminology_entries,
                    language="en",
                    url=url,
                    profile="tu-en",
                )
            )

    return terminology_findings, 0


@app.command()
def check_translation(
    url: str,
    config_path: Path,
    report_path: Path | None = typer.Option(
        None,
        "--report",
        help="Schreibt einen HTML-Bericht in die angegebene Datei.",
    ),
    pdf_report_path: Path | None = typer.Option(
        None,
        "--pdf-report",
        help="Schreibt einen PDF-Bericht in die angegebene Datei.",
    ),
) -> None:
    """Prüft deutsche Begriffe gegen die englische Sprachversion einer Seite."""
    config = load_project_config(config_path)
    prepared_url = prepare_crawl_url(url, config.crawl)

    if prepared_url is None:
        typer.echo("URL ist gemäß Crawl-Konfiguration nicht erlaubt.")
        raise typer.Exit(code=1)

    if config.check.english_terminology_path is None:
        typer.echo("Für den Übersetzungscheck fehlt english_terminology_path.")
        raise typer.Exit(code=1)

    german_html = fetch_html(prepared_url, config.crawl.allowed_domains)
    german_content = extract_page_content(german_html)
    translation_links = find_translation_links(
        find_allowed_page_language_links(
            prepared_url,
            german_html,
            config.crawl.allowed_domains,
        ),
        "de",
    )
    if not translation_links:
        typer.echo("Keine erlaubte englische Übersetzungs-URL gefunden.")
        raise typer.Exit(code=1)

    english_url = translation_links[0].href
    english_html = fetch_html(english_url, config.crawl.allowed_domains)
    english_content = extract_page_content(english_html)
    language_findings, checked_blocks = _check_translation_page_contents(
        german_content,
        english_content,
        prepared_url,
        english_url,
        config,
    )
    findings = language_findings + [
        finding_from_missing_english_translation(
            match,
            occurrence_count=german_content.text.casefold().count(
                match.matched_text.casefold()
            ),
            source_url=prepared_url,
            target_url=english_url,
            source_context=german_content.text,
            target_context=_target_context_for_source_offset(
                german_content.blocks,
                english_content.blocks,
                match.offset,
            ),
            profile=config.profile,
        )
        for match in find_missing_english_translations(
            german_content.text,
            english_content.text,
            _load_english_terminology(config),
        )
    ]

    typer.echo(f"Deutsche Quell-URL: {prepared_url}")
    typer.echo(f"Englische Übersetzungs-URL: {english_url}")
    typer.echo(f"Prüfblöcke: {checked_blocks}")
    _display_findings(findings)

    _write_reports(
        report_path=report_path,
        pdf_report_path=pdf_report_path,
        report_data=_ReportData(
            crawled_pages=2,
            checked_blocks=checked_blocks,
            findings=findings,
            context=ReportContext(
                start_url=prepared_url,
                profile=config.profile,
                language="de-DE → en-US",
                checked_urls=(prepared_url, english_url),
            ),
        ),
    )
