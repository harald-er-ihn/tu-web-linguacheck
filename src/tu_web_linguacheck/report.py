"""Erzeugung lokaler HTML-Berichte für Sprachprüfungen."""

from collections.abc import Sequence
from dataclasses import dataclass
from html import escape
from pathlib import Path

from markdown_it import MarkdownIt

from tu_web_linguacheck.models import Finding
from tu_web_linguacheck.project_metadata import load_project_metadata

_CONTEXT_RADIUS = 80
_MARKDOWN_RENDERER = MarkdownIt("commonmark", {"html": False})
_REPORT_INFORMATION_PATH = (
    Path(__file__).resolve().parents[2] / "docs" / "report-information.md"
)


@dataclass(frozen=True)
class ReportContext:
    """Beschreibt den Kontext eines Sprachprüfberichts."""

    start_url: str
    profile: str
    language: str


def _marked_context(finding: Finding) -> str:
    """Erzeugt einen gekürzten, sicher markierten Fundkontext."""
    match_end = finding.offset + finding.length
    context_start = max(0, finding.offset - _CONTEXT_RADIUS)
    context_end = min(len(finding.context), match_end + _CONTEXT_RADIUS)

    before = finding.context[context_start : finding.offset]
    matched = finding.context[finding.offset : match_end]
    after = finding.context[match_end:context_end]

    prefix = "…" if context_start > 0 else ""
    suffix = "…" if context_end < len(finding.context) else ""
    return (
        f"{prefix}{escape(before)}<mark>{escape(matched)}</mark>{escape(after)}{suffix}"
    )


def _suggestions_text(suggestions: Sequence[str]) -> str:
    """Begrenzt Vorschläge für eine lesbare Funddarstellung."""
    visible_suggestions = suggestions[:5]
    remaining_suggestions = len(suggestions) - len(visible_suggestions)
    visible_text = ", ".join(visible_suggestions) or "-"

    if not remaining_suggestions:
        return visible_text

    remaining_text = (
        "weiteren Vorschlag" if remaining_suggestions == 1 else "weitere Vorschläge"
    )
    return f"{visible_text} … und {remaining_suggestions} {remaining_text}"


def _finding_row(finding: Finding) -> str:
    """Erzeugt eine sicher escapte Tabellenzeile für einen Sprachfund."""
    suggestions = _suggestions_text(finding.suggestions)
    message = escape(finding.message)
    source_rule_id = escape(finding.source_rule_id)
    classification = (
        f"Kategorie: {escape(finding.category)} · "
        f"Schweregrad: {escape(finding.severity)}"
    )
    finding_message = (
        f'<small class="finding-classification">{classification}</small>'
        f'{message}<small class="finding-rule">Regel: {source_rule_id}</small>'
    )

    return f"""\
<tr>
  <td>{finding_message}</td>
  <td>{escape(suggestions)}</td>
  <td><pre>{_marked_context(finding)}</pre></td>
</tr>"""


def _finding_table(url: str, url_index: int, findings: Sequence[Finding]) -> str:
    """Erzeugt eine Fundtabelle mit klickbarer URL-Überschrift."""
    escaped_url = escape(url, quote=True)
    rows = "\n".join(_finding_row(finding) for finding in findings)

    return f"""\
  <section class="findings-by-url" id="findings-url-{url_index}">
    <h2 class="findings-url"><a href="{escaped_url}">{escaped_url}</a></h2>
    <table>
      <colgroup>
        <col class="finding-message">
        <col class="finding-suggestions">
        <col class="finding-context">
      </colgroup>
      <thead>
        <tr>
          <th>Meldung</th>
          <th>Vorschläge</th>
          <th>Kontext</th>
        </tr>
      </thead>
      <tbody>
{rows}
      </tbody>
    </table>
  </section>"""


def _finding_sections(findings: Sequence[Finding]) -> tuple[str, str]:
    """Erzeugt Fundtabellen und bei mehreren URLs ein Inhaltsverzeichnis."""
    finding_groups: dict[str, list[Finding]] = {}
    for finding in findings:
        finding_groups.setdefault(finding.url, []).append(finding)
    grouped_findings = tuple(finding_groups.items())
    finding_tables = "\n".join(
        _finding_table(url, url_index, findings_for_url)
        for url_index, (url, findings_for_url) in enumerate(grouped_findings, start=1)
    )
    table_of_contents = (
        '  <section class="table-of-contents">\n'
        "    <h2>Inhaltsverzeichnis</h2>\n"
        "    <ol>\n"
        + "\n".join(
            (
                f'      <li><a href="#findings-url-{url_index}">{escape(url)}</a> '
                f"({len(findings_for_url)} "
                f"{'Fund' if len(findings_for_url) == 1 else 'Funde'})</li>"
            )
            for url_index, (url, findings_for_url) in enumerate(
                grouped_findings, start=1
            )
        )
        + "\n    </ol>\n"
        "  </section>"
        if len(grouped_findings) > 1
        else ""
    )
    return finding_tables, table_of_contents


def _document(
    *,
    crawled_pages: int,
    checked_blocks: int,
    findings: Sequence[Finding],
    context: ReportContext,
) -> str:
    """Erzeugt das vollständige HTML-Dokument für den Sprachprüfbericht."""
    finding_tables, table_of_contents = _finding_sections(findings)
    report_information = _MARKDOWN_RENDERER.render(
        _REPORT_INFORMATION_PATH.read_text(encoding="utf-8")
    )
    empty_state = (
        "" if findings else '<p class="empty-state">Keine Sprachfunde festgestellt.</p>'
    )
    result_status = (
        (
            '<p class="result-status result-status--findings">'
            f"{len(findings)} Sprachfund{'e' if len(findings) != 1 else ''} "
            "festgestellt.</p>"
        )
        if findings
        else (
            '<p class="result-status result-status--clear">'
            "Keine Sprachfunde festgestellt.</p>"
        )
    )
    metric_cards = "\n".join(
        (
            '<div class="metric-card"><span>Gecrawlte Seiten</span>'
            f"<strong>{crawled_pages}</strong></div>",
            '<div class="metric-card"><span>Prüfblöcke</span>'
            f"<strong>{checked_blocks}</strong></div>",
            '<div class="metric-card"><span>Sprachfunde</span>'
            f"<strong>{len(findings)}</strong></div>",
        )
    )
    escaped_start_url = escape(context.start_url)
    escaped_profile = escape(context.profile)
    escaped_language = escape(context.language)
    project_metadata = load_project_metadata()
    project_name_and_version = " ".join(
        (escape(project_metadata.name), escape(project_metadata.version))
    )

    return f"""\
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sprachprüfbericht</title>
  <style>
    body {{
      max-width: 76rem;
      margin: 0 auto;
      padding: 2.5rem;
      color: #172033;
      background: #f6f8fb;
      font-family: system-ui, sans-serif;
      line-height: 1.5;
    }}
    h1, h2 {{ color: #102a43; }}
    h1 {{ margin: 0.25rem 0 0; font-size: 2rem; }}
    h2 {{ margin-top: 0; font-size: 1.25rem; }}
    .report-header {{
      margin-bottom: 1.5rem;
      padding-bottom: 1.25rem;
      border-bottom: 0.25rem solid #005aa0;
    }}
    .report-identity {{
      margin: 0;
      color: #486581;
      font-weight: 700;
      letter-spacing: 0.03em;
    }}
    .result-overview {{
      margin-bottom: 1.5rem;
      padding: 1.5rem;
      border: 1px solid #d9e2ec;
      border-radius: 0.5rem;
      background: #ffffff;
    }}
    .metric-cards {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 1rem;
    }}
    .metric-card {{
      padding: 1rem;
      border: 1px solid #d9e2ec;
      border-radius: 0.375rem;
      background: #f8fafc;
    }}
    .metric-card span {{ display: block; color: #486581; font-size: 0.875rem; }}
    .metric-card strong {{ display: block; color: #102a43; font-size: 1.75rem; }}
    .result-status {{
      margin: 0 0 1rem;
      padding: 0.75rem 1rem;
      border-radius: 0.25rem;
      font-weight: 700;
    }}
    .result-status--findings {{ color: #7c2d12; background: #fff7ed; }}
    .result-status--clear {{ color: #166534; background: #f0fdf4; }}
    table {{
      border-collapse: collapse;
      width: 100%;
      table-layout: fixed;
      background: #ffffff;
    }}
    .finding-message {{ width: 36%; }}
    .finding-classification {{
      display: block;
      margin-bottom: 0.25rem;
      color: #486581;
      font-size: 0.875rem;
      font-weight: 700;
    }}
    .finding-rule {{
      display: block;
      margin-top: 0.25rem;
      color: #486581;
      font-size: 0.875rem;
    }}
    .finding-suggestions {{ width: 22%; }}
    .finding-context {{ width: 42%; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 0.6rem; text-align: left; }}
    th {{ background: #e2e8f0; }}
    tr:nth-child(even) {{ background: #f8fafc; }}
    a {{ color: #005aa0; }}
    mark {{ background: #fef08a; padding: 0.1rem; }}
    .empty-state {{
      padding: 1rem;
      border: 1px solid #86efac;
      border-radius: 0.25rem;
      background: #ecfdf5;
    }}
    .check-context {{
      margin-bottom: 1.5rem;
      padding: 1.25rem;
      border: 1px solid #93c5fd;
      border-radius: 0.5rem;
      background: #eff6ff;
    }}
    pre {{ margin: 0; white-space: pre-wrap; font: inherit; }}
    @media (max-width: 48rem) {{
      body {{ padding: 1rem; }}
      .metric-cards {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body id="report-top">
  <header class="report-header">
    <p class="report-identity">{project_name_and_version}</p>
    <h1>Sprachprüfbericht</h1>
  </header>
  <section class="result-overview">
    <h2>Ergebnisübersicht</h2>
    {result_status}
    <div class="metric-cards">
      {metric_cards}
    </div>
  </section>
  {empty_state}
  <section class="check-context">
    <h2>Prüfkontext</h2>
    <p>Start-URL: {escaped_start_url}</p>
    <p>Profil: {escaped_profile}</p>
    <p>Sprache: {escaped_language}</p>
  </section>
  <h2>Über dieses Werkzeug</h2>
  <p><strong>{project_name_and_version}</strong></p>
  <p>{escape(project_metadata.description)}</p>
  <p>Autor: {escape(project_metadata.author)}</p>
  <p>Lizenz: {escape(project_metadata.license_name)}</p>
  <p><a href="#report-information">Informationen zum Sprachprüfbericht</a></p>
  {table_of_contents}
  {finding_tables}
  <section id="report-information">
    {report_information}
    <p><a href="#report-top">Nach oben</a></p>
  </section>
</body>
</html>
"""


def write_html_report(
    report_path: Path,
    *,
    crawled_pages: int,
    checked_blocks: int,
    findings: Sequence[Finding],
    context: ReportContext,
) -> None:
    """Schreibt einen lokalen HTML-Bericht mit Sprachfunden."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _document(
            crawled_pages=crawled_pages,
            checked_blocks=checked_blocks,
            findings=findings,
            context=context,
        ),
        encoding="utf-8",
    )
