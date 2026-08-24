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


def test_version_displays_package_version() -> None:
    """Die CLI gibt ihre Paketversion aus."""
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.output == "0.1.0\n"
