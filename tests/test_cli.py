"""Tests für die Kommandozeilenschnittstelle."""

from typer.testing import CliRunner

from tu_web_linguacheck.cli import app

runner = CliRunner()


def test_help_displays_project_name() -> None:
    """Die CLI-Hilfe nennt den Projektnamen."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "tu-web-linguacheck" in result.output
