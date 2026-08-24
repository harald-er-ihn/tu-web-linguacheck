"""Kommandozeilenschnittstelle für tu-web-linguacheck."""

import typer

app = typer.Typer(
    help="Prüft öffentlich erreichbare Websites lokal auf sprachliche Auffälligkeiten.",
    no_args_is_help=True,
)


@app.callback()
def callback() -> None:
    """Stellt die Befehlsgruppe bereit."""


@app.command()
def run() -> None:
    """Startet tu-web-linguacheck."""
    typer.echo("tu-web-linguacheck ist bereit.")


def main() -> None:
    """Startet die Kommandozeilenschnittstelle."""
    app()
