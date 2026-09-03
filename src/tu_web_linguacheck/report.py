"""Erzeugung lokaler HTML-Berichte für Sprachprüfungen."""

from collections.abc import Sequence
from html import escape
from pathlib import Path

from tu_web_linguacheck.models import Finding


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
  <td><pre>{escape(finding.context)}</pre></td>
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
