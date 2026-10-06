"""Kommandozeilenschnittstelle für tu-web-linguacheck."""
# pylint: disable=too-many-lines

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError

import typer
from pydantic import ValidationError

from tu_web_linguacheck.config import ProjectConfig, load_project_config
from tu_web_linguacheck.crawler import crawl_pages_with_content
from tu_web_linguacheck.findings import (
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
from tu_web_linguacheck.models import CrawledPage, Finding
from tu_web_linguacheck.ner import mark_html_language_findings_with_person_hints
from tu_web_linguacheck.page_checking import (
    _check_page_blocks,
    _check_page_text,
    _check_text_findings,
)
from tu_web_linguacheck.project_metadata import load_project_metadata
from tu_web_linguacheck.report import ReportContext, write_html_report, write_pdf_report
from tu_web_linguacheck.terminology import (
    TerminologyEntry,
    find_missing_english_translations,
    find_terminology_matches,
    load_terminology,
)
from tu_web_linguacheck.urls import is_url_under_start_path, prepare_crawl_url

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
            if finding.ner_person_name is not None:
                typer.echo(
                    "NER-Prüfmarkierung: möglicher Personenname "
                    f"„{finding.ner_person_name}“."
                )
        typer.echo(f"Position: {finding.offset}–{end_offset}")

        context_start = max(0, finding.offset - 80)
        context_end = min(len(finding.context), end_offset + 80)
        context = finding.context[context_start:context_end]

        if context_start > 0:
            context = f"…{context}"

        if context_end < len(finding.context):
            context = f"{context}…"

        typer.echo(f"Kontext: {context}")


def _ensure_languagetool_available(language: str) -> None:
    """Prüft, ob der lokale LanguageTool-Server erreichbar ist."""
    try:
        LanguageToolClient().check(text="", language=language)
    except LanguageToolUnavailableError as error:
        typer.echo(str(error))
        raise typer.Exit(code=1) from error


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


def _check_url_page_content(
    page_content: PageContent,
    *,
    config: ProjectConfig,
    url: str,
    missing_english_lang_only: bool,
) -> tuple[list[Finding], int]:
    """Prüft extrahierten Seiteninhalt und ergänzt lokale Terminologiefunde."""
    if page_content.blocks:
        findings, checked_blocks = _check_page_blocks(
            page_content.blocks,
            language=config.check.language,
            url=url,
            profile=config.profile,
            disabled_rule_ids=config.check.ignored_rule_ids,
            ignored_terms=config.check.ignored_terms,
        )
    else:
        findings, checked_blocks = _check_page_text(
            page_content.text,
            language=config.check.language,
            url=url,
            profile=config.profile,
            disabled_rule_ids=config.check.ignored_rule_ids,
            ignored_terms=config.check.ignored_terms,
        )

    if missing_english_lang_only:
        return (
            [finding for finding in findings if finding.category == "HTML_LANGUAGE"],
            checked_blocks,
        )

    if config.check.terminology_path is not None:
        terminology_entries = load_terminology(config.check.terminology_path)
        findings.extend(
            finding_from_terminology_match(
                match,
                url=url,
                context=page_content.text,
                profile=config.profile,
            )
            for match in find_terminology_matches(
                page_content.text,
                terminology_entries,
            )
        )

    return findings, checked_blocks


@app.command()
def check_url(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    url: str,
    config_path: Path,
    stay_under_start_path: bool = typer.Option(
        False,
        "--stay-under-start-path",
        help="Beschränkt Redirects auf den Startpfad und dessen Unterpfade.",
    ),
    missing_english_lang_only: bool = typer.Option(
        False,
        "--missing-english-lang-only",
        help=(
            "Prüft ausschließlich, ob vermutlich englische Ausdrücke in deutschen "
            'Texten ohne lang="en" oder lang="en-US" ausgezeichnet sind.'
        ),
    ),
    ner_person_hints: bool = typer.Option(
        False,
        "--ner-person-hints",
        help=(
            "Markiert bestehende Sprach- und Rechtschreibfunde zusätzlich, wenn die "
            "lokale Eigennamenerkennung einen möglichen Personennamen erkennt."
        ),
    ),
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

    fetch_options = {"stay_under_start_path": True} if stay_under_start_path else {}
    html = fetch_html(
        prepared_url,
        config.crawl.allowed_domains,
        **fetch_options,
    )
    page_content = extract_page_content(html)

    typer.echo(f"URL: {prepared_url}")
    typer.echo(f"Titel: {page_content.title}")
    typer.echo(f"Extrahierte Textzeichen: {len(page_content.text)}")

    try:
        findings, checked_blocks = _check_url_page_content(
            page_content,
            config=config,
            url=prepared_url,
            missing_english_lang_only=missing_english_lang_only,
        )
    except LanguageToolUnavailableError as error:
        typer.echo(str(error))
        raise typer.Exit(code=1) from error

    if ner_person_hints:
        findings = mark_html_language_findings_with_person_hints(findings)
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


def _check_crawled_page(
    page: CrawledPage,
    *,
    config: ProjectConfig,
    terminology_entries: tuple[TerminologyEntry, ...] | None,
    missing_english_lang_only: bool,
) -> tuple[list[Finding], int]:
    """Prüft eine gecrawlte Seite und ergänzt lokale Terminologiefunde."""
    if page.blocks:
        findings, checked_blocks = _check_page_blocks(
            page.blocks,
            language=config.check.language,
            url=page.url,
            profile=config.profile,
            disabled_rule_ids=config.check.ignored_rule_ids,
            ignored_terms=config.check.ignored_terms,
        )
    else:
        findings, checked_blocks = _check_page_text(
            page.text,
            language=config.check.language,
            url=page.url,
            profile=config.profile,
            disabled_rule_ids=config.check.ignored_rule_ids,
            ignored_terms=config.check.ignored_terms,
        )
    if missing_english_lang_only:
        findings = [
            finding for finding in findings if finding.category == "HTML_LANGUAGE"
        ]

    if not missing_english_lang_only and terminology_entries is not None:
        findings.extend(
            finding_from_terminology_match(
                match,
                url=page.url,
                context=page.text,
                profile=config.profile,
            )
            for match in find_terminology_matches(page.text, terminology_entries)
        )

    return findings, checked_blocks


def _check_crawled_pages(
    pages: Sequence[CrawledPage],
    *,
    config: ProjectConfig,
    missing_english_lang_only: bool,
) -> tuple[list[Finding], int]:
    """Prüft gecrawlte Seiten und summiert ihre Funde und Prüfblöcke."""
    terminology_entries = (
        load_terminology(config.check.terminology_path)
        if not missing_english_lang_only and config.check.terminology_path is not None
        else None
    )
    findings: list[Finding] = []
    checked_blocks = 0

    try:
        for page in pages:
            page_findings, page_checked_blocks = _check_crawled_page(
                page,
                config=config,
                terminology_entries=terminology_entries,
                missing_english_lang_only=missing_english_lang_only,
            )
            findings.extend(page_findings)
            checked_blocks += page_checked_blocks
    except LanguageToolUnavailableError as error:
        typer.echo(str(error))
        raise typer.Exit(code=1) from error

    return findings, checked_blocks


def _ner_person_hint_command_parts(
    ner_person_hints: bool,
) -> tuple[str, ...]:
    """Gibt den optionalen NER-Schalter für reproduzierbare Befehle zurück."""
    return ("--ner-person-hints",) if ner_person_hints else ()


def _crawl_report_checked_urls(
    pages: Sequence[CrawledPage],
    findings: Sequence[Finding],
    *,
    show_pages_without_findings: bool,
) -> tuple[str, ...]:
    """Wählt Crawl-URLs für Berichte abhängig von der Leer-Seiten-Option aus."""
    if show_pages_without_findings:
        return tuple(page.url for page in pages)

    finding_urls = {finding.url for finding in findings}
    return tuple(page.url for page in pages if page.url in finding_urls)


def _crawl_report_data(  # pylint: disable=too-many-arguments
    *,
    url: str,
    config_path: Path,
    stay_under_start_path: bool,
    missing_english_lang_only: bool,
    ner_person_hints: bool,
    show_pages_without_findings: bool,
    report_path: Path | None,
    pdf_report_path: Path | None,
    config: ProjectConfig,
    pages: Sequence[CrawledPage],
    checked_blocks: int,
    findings: Sequence[Finding],
) -> _ReportData:
    """Erstellt Berichtsdaten für einen regulären Crawl."""
    return _ReportData(
        crawled_pages=len(pages),
        checked_blocks=checked_blocks,
        findings=findings,
        context=ReportContext(
            start_url=url,
            profile=config.profile,
            language=config.check.language,
            checked_urls=_crawl_report_checked_urls(
                pages,
                findings,
                show_pages_without_findings=show_pages_without_findings,
            ),
            command=" ".join(
                part
                for part in (
                    "tu-web-linguacheck",
                    "check-crawl",
                    url,
                    str(config_path),
                    "--stay-under-start-path" if stay_under_start_path else None,
                    "--missing-english-lang-only"
                    if missing_english_lang_only
                    else None,
                    *_ner_person_hint_command_parts(ner_person_hints),
                    "--report" if report_path is not None else None,
                    str(report_path) if report_path is not None else None,
                    "--pdf-report" if pdf_report_path is not None else None,
                    str(pdf_report_path) if pdf_report_path is not None else None,
                )
                if part is not None
            ),
            config_path=str(config_path),
            allowed_domains=tuple(config.crawl.allowed_domains),
            max_depth=config.crawl.max_depth,
            max_pages=config.crawl.max_pages,
            requests_per_second=config.crawl.requests_per_second,
            obey_robots_txt=config.crawl.obey_robots_txt,
            stay_under_start_path=stay_under_start_path,
        ),
    )


@app.command()
def check_crawl(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    url: str,
    config_path: Path,
    stay_under_start_path: bool = typer.Option(
        False,
        "--stay-under-start-path",
        help="Beschränkt den Crawl auf den Startpfad und dessen Unterpfade.",
    ),
    missing_english_lang_only: bool = typer.Option(
        False,
        "--missing-english-lang-only",
        help=(
            "Prüft ausschließlich, ob vermutlich englische Ausdrücke in deutschen "
            'Texten ohne lang="en" oder lang="en-US" ausgezeichnet sind.'
        ),
    ),
    ner_person_hints: bool = typer.Option(
        False,
        "--ner-person-hints",
        help=(
            "Markiert bestehende Sprach- und Rechtschreibfunde zusätzlich, wenn die "
            "lokale Eigennamenerkennung einen möglichen Personennamen erkennt."
        ),
    ),
    show_pages_without_findings: bool = typer.Option(
        False,
        "--show-pages-without-findings",
        help="Zeigt Seiten ohne Funde im Bericht an.",
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

    _ensure_languagetool_available(config.check.language)

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
    findings, checked_blocks = _check_crawled_pages(
        pages,
        config=config,
        missing_english_lang_only=missing_english_lang_only,
    )
    if ner_person_hints:
        findings = mark_html_language_findings_with_person_hints(findings)
    typer.echo(f"Gecrawlte Seiten: {len(pages)}")
    typer.echo(f"Prüfblöcke: {checked_blocks}")
    _display_findings(findings)

    report_data = _crawl_report_data(
        url=url,
        config_path=config_path,
        stay_under_start_path=stay_under_start_path,
        missing_english_lang_only=missing_english_lang_only,
        ner_person_hints=ner_person_hints,
        show_pages_without_findings=show_pages_without_findings,
        report_path=report_path,
        pdf_report_path=pdf_report_path,
        config=config,
        pages=pages,
        checked_blocks=checked_blocks,
        findings=findings,
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


def _load_english_terminology_sources(
    config: ProjectConfig,
) -> tuple[tuple[Path, tuple[TerminologyEntry, ...]], ...]:
    """Lädt englische Terminologiequellen mit ihren jeweiligen Einträgen."""
    terminology_paths = (
        config.check.english_terminology_path,
        config.check.cfv_english_terminology_path,
        *config.check.additional_english_terminology_paths,
    )
    return tuple(
        (terminology_path, load_terminology(terminology_path))
        for terminology_path in terminology_paths
        if terminology_path is not None
    )


def _load_english_terminology(
    config: ProjectConfig,
) -> tuple[TerminologyEntry, ...]:
    """Lädt die Einträge aller englischen Terminologiequellen."""
    return tuple(
        entry
        for _, entries in _load_english_terminology_sources(config)
        for entry in entries
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


def _find_translation_url(
    *,
    source_url: str,
    source_html: str,
    allowed_domains: Sequence[str],
    stay_under_start_path: bool,
) -> str | None:
    """Findet die erste erlaubte englische Übersetzungs-URL."""
    translation_links = find_translation_links(
        find_allowed_page_language_links(
            source_url,
            source_html,
            allowed_domains,
        ),
        "de",
    )
    if stay_under_start_path:
        translation_links = [
            language_link
            for language_link in translation_links
            if is_url_under_start_path(language_link.href, source_url)
        ]

    return translation_links[0].href if translation_links else None


@dataclass(frozen=True)
class _TranslationCrawlPageResult:
    """Ergebnis der Übersetzungsprüfung einer deutschen Crawl-Seite."""

    findings: list[Finding]
    checked_blocks: int
    english_url: str | None
    fetch_error: Exception | None = None


def _check_translation_crawl_pages(
    pages: Sequence[CrawledPage],
    *,
    config: ProjectConfig,
    english_terminology_entries: tuple[TerminologyEntry, ...],
) -> tuple[list[Finding], int, list[str]]:
    """Prüft Übersetzungen gecrawlter deutscher Seiten."""
    findings: list[Finding] = []
    checked_blocks = 0
    checked_urls: list[str] = []

    for german_page in pages:
        checked_urls.append(german_page.url)
        page_result = _check_translation_crawl_page(
            german_page=german_page,
            config=config,
            english_terminology_entries=english_terminology_entries,
        )
        if page_result.fetch_error is not None:
            typer.echo(
                "Überspringe englische Übersetzung wegen Abruffehler: "
                f"{page_result.english_url} ({page_result.fetch_error})"
            )
            continue
        if page_result.english_url is None:
            typer.echo(
                f"Keine erlaubte englische Übersetzungs-URL gefunden: {german_page.url}"
            )
            continue

        findings.extend(page_result.findings)
        checked_blocks += page_result.checked_blocks
        checked_urls.append(page_result.english_url)

    return findings, checked_blocks, checked_urls


def _check_translation_crawl_page(
    *,
    german_page,
    config: ProjectConfig,
    english_terminology_entries: tuple,
) -> _TranslationCrawlPageResult:
    """Prüft eine deutsche Crawl-Seite gegen ihre englische Sprachversion."""
    english_url = _find_translation_url(
        source_url=german_page.url,
        source_html=german_page.html,
        allowed_domains=config.crawl.allowed_domains,
        stay_under_start_path=False,
    )
    if english_url is None:
        return _TranslationCrawlPageResult([], 0, None)

    try:
        english_html = fetch_html(english_url, config.crawl.allowed_domains)
    except (TimeoutError, URLError) as error:
        return _TranslationCrawlPageResult([], 0, english_url, error)
    english_content = extract_page_content(english_html)
    german_content = PageContent(
        title=german_page.title,
        text=german_page.text,
        blocks=german_page.blocks,
    )
    findings, checked_blocks = _check_translation_page_contents(
        german_content,
        english_content,
        german_page.url,
        english_url,
        config,
    )
    findings.extend(
        finding_from_missing_english_translation(
            match,
            occurrence_count=german_content.text.casefold().count(
                match.matched_text.casefold()
            ),
            source_url=german_page.url,
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
            english_terminology_entries,
        )
    )

    return _TranslationCrawlPageResult(
        findings,
        checked_blocks,
        english_url,
    )


def _translation_crawl_report_data(  # pylint: disable=too-many-arguments
    *,
    url: str,
    config_path: Path,
    stay_under_start_path: bool,
    report_path: Path | None,
    pdf_report_path: Path | None,
    config: ProjectConfig,
    checked_urls: Sequence[str],
    checked_blocks: int,
    findings: list[Finding],
    english_terminology_sources: Sequence[tuple[Path, tuple[TerminologyEntry, ...]]],
) -> _ReportData:
    """Erstellt Berichtsdaten für einen Übersetzungs-Crawl."""
    return _ReportData(
        crawled_pages=len(checked_urls),
        checked_blocks=checked_blocks,
        findings=findings,
        context=ReportContext(
            start_url=url,
            profile=config.profile,
            language="de-DE → en-US",
            checked_urls=tuple(checked_urls),
            command=" ".join(
                part
                for part in (
                    "tu-web-linguacheck",
                    "check-translation-crawl",
                    url,
                    str(config_path),
                    "--stay-under-start-path" if stay_under_start_path else None,
                    "--report" if report_path is not None else None,
                    str(report_path) if report_path is not None else None,
                    "--pdf-report" if pdf_report_path is not None else None,
                    str(pdf_report_path) if pdf_report_path is not None else None,
                )
                if part is not None
            ),
            config_path=str(config_path),
            allowed_domains=tuple(config.crawl.allowed_domains),
            max_depth=config.crawl.max_depth,
            max_pages=config.crawl.max_pages,
            requests_per_second=config.crawl.requests_per_second,
            obey_robots_txt=config.crawl.obey_robots_txt,
            stay_under_start_path=stay_under_start_path,
            is_translation_check=True,
            translation_terminology_sources=tuple(
                (terminology_path.name, len(entries))
                for terminology_path, entries in english_terminology_sources
            ),
            translation_uses_cfv_terminology=(
                config.check.cfv_english_terminology_path is not None
            ),
        ),
    )


@app.command()
def check_translation_crawl(
    url: str,
    config_path: Path,
    stay_under_start_path: bool = typer.Option(
        False,
        "--stay-under-start-path",
        help="Beschränkt den deutschen Crawl auf den Startpfad und dessen Unterpfade.",
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
    """Crawlt deutsche Seiten und prüft ihre englischen Sprachversionen."""
    config = load_project_config(config_path)

    if config.check.english_terminology_path is None:
        typer.echo("Für den Übersetzungscheck fehlt english_terminology_path.")
        raise typer.Exit(code=1)

    pages = crawl_pages_with_content(
        start_url=url,
        config=config.crawl,
        stay_under_start_path=stay_under_start_path,
        on_progress=lambda number, candidate: typer.echo(
            f"Crawle deutsche Seite {number}/{config.crawl.max_pages}: {candidate.url}"
        ),
        on_error=lambda candidate, error: typer.echo(
            f"Überspringe deutsche Seite wegen Abruffehler: {candidate.url} ({error})"
        ),
    )
    english_terminology_sources = _load_english_terminology_sources(config)
    english_terminology_entries = tuple(
        entry for _, entries in english_terminology_sources for entry in entries
    )
    findings, checked_blocks, checked_urls = _check_translation_crawl_pages(
        pages,
        config=config,
        english_terminology_entries=english_terminology_entries,
    )

    typer.echo(f"Gecrawlte deutsche Seiten: {len(pages)}")
    typer.echo(f"Geprüfte englische Übersetzungen: {len(checked_urls) - len(pages)}")
    typer.echo(f"Prüfblöcke: {checked_blocks}")
    _display_findings(findings)

    _write_reports(
        report_path=report_path,
        pdf_report_path=pdf_report_path,
        report_data=_translation_crawl_report_data(
            url=url,
            config_path=config_path,
            stay_under_start_path=stay_under_start_path,
            report_path=report_path,
            pdf_report_path=pdf_report_path,
            config=config,
            checked_urls=checked_urls,
            checked_blocks=checked_blocks,
            findings=findings,
            english_terminology_sources=english_terminology_sources,
        ),
    )


def _translation_report_data(  # pylint: disable=too-many-arguments
    *,
    url: str,
    config_path: Path,
    stay_under_start_path: bool,
    report_path: Path | None,
    pdf_report_path: Path | None,
    prepared_url: str,
    english_url: str,
    config: ProjectConfig,
    checked_blocks: int,
    findings: list[Finding],
    terminology_sources: Sequence[tuple[Path, tuple[TerminologyEntry, ...]]],
) -> _ReportData:
    """Erstellt Berichtsdaten für eine einzelne Übersetzungsprüfung."""
    return _ReportData(
        crawled_pages=2,
        checked_blocks=checked_blocks,
        findings=findings,
        context=ReportContext(
            start_url=prepared_url,
            profile=config.profile,
            language="de-DE → en-US",
            checked_urls=(prepared_url, english_url),
            command=" ".join(
                part
                for part in (
                    "tu-web-linguacheck",
                    "check-translation",
                    url,
                    str(config_path),
                    "--stay-under-start-path" if stay_under_start_path else None,
                    "--report" if report_path is not None else None,
                    str(report_path) if report_path is not None else None,
                    "--pdf-report" if pdf_report_path is not None else None,
                    str(pdf_report_path) if pdf_report_path is not None else None,
                )
                if part is not None
            ),
            config_path=str(config_path),
            allowed_domains=tuple(config.crawl.allowed_domains),
            max_depth=config.crawl.max_depth,
            max_pages=config.crawl.max_pages,
            requests_per_second=config.crawl.requests_per_second,
            obey_robots_txt=config.crawl.obey_robots_txt,
            stay_under_start_path=stay_under_start_path,
            is_translation_check=True,
            translation_terminology_sources=tuple(
                (terminology_path.name, len(entries))
                for terminology_path, entries in terminology_sources
            ),
            translation_uses_cfv_terminology=(
                config.check.cfv_english_terminology_path is not None
            ),
        ),
    )


@app.command()
def check_translation(  # pylint: disable=too-many-locals
    url: str,
    config_path: Path,
    stay_under_start_path: bool = typer.Option(
        False,
        "--stay-under-start-path",
        help="Beschränkt die Übersetzungs-URL auf den Startpfad und dessen Unterpfade.",
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
    english_url = _find_translation_url(
        source_url=prepared_url,
        source_html=german_html,
        allowed_domains=config.crawl.allowed_domains,
        stay_under_start_path=stay_under_start_path,
    )
    if english_url is None:
        typer.echo("Keine erlaubte englische Übersetzungs-URL gefunden.")
        raise typer.Exit(code=1)
    english_html = fetch_html(english_url, config.crawl.allowed_domains)
    english_content = extract_page_content(english_html)
    german_terminology_sources = (
        (
            (
                config.check.german_terminology_path,
                load_terminology(config.check.german_terminology_path),
            ),
        )
        if config.check.german_terminology_path is not None
        else ()
    )
    english_terminology_sources = _load_english_terminology_sources(config)
    english_terminology_entries = tuple(
        entry for _, entries in english_terminology_sources for entry in entries
    )
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
            english_terminology_entries,
        )
    ]

    typer.echo(f"Deutsche Quell-URL: {prepared_url}")
    typer.echo(f"Englische Übersetzungs-URL: {english_url}")
    typer.echo(f"Prüfblöcke: {checked_blocks}")
    _display_findings(findings)

    _write_reports(
        report_path=report_path,
        pdf_report_path=pdf_report_path,
        report_data=_translation_report_data(
            url=url,
            config_path=config_path,
            stay_under_start_path=stay_under_start_path,
            report_path=report_path,
            pdf_report_path=pdf_report_path,
            prepared_url=prepared_url,
            english_url=english_url,
            config=config,
            checked_blocks=checked_blocks,
            findings=findings,
            terminology_sources=(
                german_terminology_sources + english_terminology_sources
            ),
        ),
    )
