# Mitwirken

Vielen Dank für Dein Interesse an `tu-web-linguacheck`.

## Entwicklungsprinzipien

- Änderungen klein, nachvollziehbar und fokussiert halten.
- Für neue Funktionen oder Fehlerkorrekturen zuerst einen passenden Test
  schreiben, sofern sinnvoll.
- Vor einem Commit Tests und Linting ausführen.
- Änderungen vor dem Commit mit `git diff` prüfen.
- Generierte Crawl-Daten, Berichte, Logs und lokale Umgebungen nicht
  versionieren.

## Datenschutz

Website-Inhalte, Crawl-Daten, Prüfergebnisse und Projektinhalte dürfen nicht an
externe Cloud-KI- oder Sprachprüfungs-APIs übertragen werden. Die Sprachprüfung
soll ausschließlich über lokale Komponenten erfolgen.

## Entwicklungsumgebung

Erstelle und aktiviere eine virtuelle Python-Umgebung wie in der
[WSL2-Installationsanleitung](docs/installation-wsl2.md). Installiere für die
Mitarbeit anschließend das Projekt mit den Entwicklungsabhängigkeiten:

```bash
python -m pip install ".[dev]"
```

## Codequalität

Vor jedem Commit führe den vollständigen Qualitätslauf aus:

```bash
tools/code_audit.sh
```

`tools/code_audit.sh` bündelt Ruff, pytest, Pylint, Xenon, die Markdown-Prüfung sowie
Git-Prüfungen für Diff und Arbeitsverzeichnis.

## Änderungen einreichen

1. Einen eigenen Branch anlegen.
1. Änderung und zugehörige Tests erstellen.
1. Tests und Ruff ausführen.
1. Den Diff prüfen.
1. Einen klaren, kleinen Commit erstellen.
1. Einen Pull Request mit kurzer Beschreibung eröffnen.

## Sicherheits- und Crawl-Regeln

Neue Crawl-Funktionen müssen standardmäßig diese Prinzipien einhalten:

- Nur ausdrücklich erlaubte Domains crawlen.
- `robots.txt` beachten, sofern nicht bewusst und dokumentiert abweichend
  konfiguriert.
- Rate-Limits und Obergrenzen für Seitenzahl und Crawl-Tiefe ermöglichen.
- PDFs sowie nicht HTML-basierte Dateien ignorieren.
