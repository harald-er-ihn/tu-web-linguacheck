"""Erzeugung lokaler HTML-Berichte für Sprachprüfungen."""

from collections.abc import Sequence
from html import escape
from pathlib import Path

from tu_web_linguacheck.models import Finding

_CONTEXT_RADIUS = 80


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


def _finding_row(finding: Finding) -> str:
    """Erzeugt eine sicher escapte Tabellenzeile für einen Sprachfund."""
    url = escape(finding.url, quote=True)
    suggestions = ", ".join(finding.suggestions) or "-"

    return f"""\
<tr>
  <td><a href="{url}">{url}</a></td>
  <td>{escape(finding.category)}</td>
  <td>{escape(finding.severity)}</td>
  <td>{escape(finding.message)}</td>
  <td>{escape(finding.source_rule_id)}</td>
  <td>{escape(suggestions)}</td>
  <td><pre>{_marked_context(finding)}</pre></td>
</tr>"""


def _document(
    *,
    crawled_pages: int,
    checked_blocks: int,
    findings: Sequence[Finding],
) -> str:
    """Erzeugt das vollständige HTML-Dokument für den Sprachprüfbericht."""
    rows = "\n".join(_finding_row(finding) for finding in findings)

    return f"""\
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sprachprüfbericht</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1f2933; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 0.6rem; text-align: left; }}
    th {{ background: #e2e8f0; }}
    tr:nth-child(even) {{ background: #f8fafc; }}
    a {{ color: #005aa0; }}
    mark {{ background: #fef08a; padding: 0.1rem; }}
    pre {{ margin: 0; white-space: pre-wrap; font: inherit; }}
  </style>
</head>
<body>
  <h1>Sprachprüfbericht</h1>
  <p>Gecrawlte Seiten: {crawled_pages}</p>
  <p>Prüfblöcke: {checked_blocks}</p>
  <p>Sprachfunde: {len(findings)}</p>
  <table>
    <thead>
      <tr>
        <th>URL</th>
        <th>Kategorie</th>
        <th>Schweregrad</th>
        <th>Meldung</th>
        <th>Regel</th>
        <th>Vorschläge</th>
        <th>Kontext</th>
      </tr>
    </thead>
    <tbody>
{rows}
    </tbody>
  </table>
</body>
</html>
"""


def write_html_report(
    report_path: Path,
    *,
    crawled_pages: int,
    checked_blocks: int,
    findings: Sequence[Finding],
) -> None:
    """Schreibt einen lokalen HTML-Bericht mit Sprachfunden."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _document(
            crawled_pages=crawled_pages,
            checked_blocks=checked_blocks,
            findings=findings,
        ),
        encoding="utf-8",
    )
