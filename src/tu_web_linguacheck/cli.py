"""Kommandozeilenschnittstelle für tu-web-linguacheck."""

import typer

from tu_web_linguacheck import __version__

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
    version: bool = typer.Option(
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


def main() -> None:
    """Startet die Kommandozeilenschnittstelle."""
    app()
