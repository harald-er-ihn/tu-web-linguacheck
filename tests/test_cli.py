"""Tests für die Kommandozeilenschnittstelle."""

from typer.testing import CliRunner

from tu_web_linguacheck.cli import app

runner = CliRunner()


def test_help_displays_project_name_and_run_command() -> None:
    """Die CLI-Hilfe nennt den Projektnamen und den Platzhalterbefehl."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "tu-web-linguacheck" in result.output
    assert "run" in result.output
