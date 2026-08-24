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

## Codequalität

Das Projekt verwendet:

- `pytest` für Tests,
- `ruff` für Linting und Formatierung.

Die konkreten Befehle und Konfigurationen werden mit dem Python-Projektgerüst
ergänzt.

## Änderungen einreichen

1. Einen eigenen Branch anlegen.
2. Änderung und zugehörige Tests erstellen.
3. Tests und Ruff ausführen.
4. Den Diff prüfen.
5. Einen klaren, kleinen Commit erstellen.
6. Einen Pull Request mit kurzer Beschreibung eröffnen.

## Sicherheits- und Crawl-Regeln

Neue Crawl-Funktionen müssen standardmäßig diese Prinzipien einhalten:

- Nur ausdrücklich erlaubte Domains crawlen.
- `robots.txt` beachten, sofern nicht bewusst und dokumentiert abweichend
  konfiguriert.
- Rate-Limits und Obergrenzen für Seitenzahl und Crawl-Tiefe ermöglichen.
- PDFs sowie nicht HTML-basierte Dateien ignorieren.
