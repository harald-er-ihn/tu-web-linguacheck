# Installation unter Windows mit WSL2

Diese Anleitung beschreibt die lokale Installation von
`tu-web-linguacheck` unter Windows mit WSL2 und Ubuntu.

Das Werkzeug prüft Website-Inhalte ausschließlich lokal. Für jede
Sprachprüfung ist ein lokaler LanguageTool-Server erforderlich, der auf
`127.0.0.1:8081` erreichbar sein muss.

## Voraussetzungen

Benötigt werden:

- Windows 10 oder Windows 11 mit aktiviertem WSL2
- eine aktuelle Ubuntu-Distribution in WSL2
- Internetzugang zum Klonen des Repositorys, zum Installieren von Paketen und
  zum Abrufen geprüfter Websites
- Python 3.12 oder neuer
- eine Java-Laufzeit für den verpflichtenden lokalen LanguageTool-Server

Prüfe in einer Ubuntu-WSL-Shell, ob WSL2 verwendet wird:

```bash
uname -a
```

Die Ausgabe sollte `microsoft` oder `WSL2` enthalten.

## Systempakete installieren

Aktualisiere zunächst die Paketlisten und installiere Python, Java sowie die
für PDF-Berichte benötigten Systembibliotheken:

```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip \
  openjdk-17-jre-headless unzip curl libcairo2 libffi-dev \
  libgdk-pixbuf-2.0-0 libpango-1.0-0 libpangocairo-1.0-0 \
  libharfbuzz-subset0 shared-mime-info
```

Prüfe anschließend die Python-Version:

```bash
python3.12 --version
```

Die ausgegebene Version muss mindestens `3.12` sein.

## Repository klonen

Klone das öffentliche Repository per HTTPS in dein Linux-Dateisystem. Ein
Projektverzeichnis unter dem Linux-Home-Verzeichnis ist unter WSL2 empfohlen:

```bash
git clone https://github.com/harald-er-ihn/tu-web-linguacheck.git
cd tu-web-linguacheck
```

## Virtuelle Python-Umgebung anlegen

Erstelle eine virtuelle Umgebung mit Python 3.12 und aktiviere sie:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Installiere anschließend das Werkzeug aus dem geklonten Repository:

```bash
python -m pip install --upgrade pip
python -m pip install .
```

Prüfe die Installation:

```bash
tu-web-linguacheck --version
tu-web-linguacheck --help
```

## Verpflichtenden lokalen LanguageTool-Server installieren

`tu-web-linguacheck` überträgt keine Texte an externe Sprachprüfungsdienste.
Stattdessen prüft es Texte mit einem lokalen LanguageTool-Server. Dieser Server
ist zwingend erforderlich: Ohne ihn funktionieren `check-text`, `check-url`
und `check-crawl` nicht.

Prüfe zunächst die Java-Laufzeit:

```bash
java -version
```

Lade LanguageTool herunter und entpacke es in dem Verzeichnis, das das
mitgelieferte Startskript standardmäßig erwartet:

```bash
mkdir -p ~/.local/share/languagetool
curl -L -o /tmp/LanguageTool-6.6.zip \
  https://languagetool.org/download/LanguageTool-6.6.zip
unzip -q /tmp/LanguageTool-6.6.zip -d ~/.local/share/languagetool
```

Prüfe, ob die benötigte Server-JAR vorhanden ist:

```bash
test -f "$HOME/.local/share/languagetool/LanguageTool-6.6/languagetool-server.jar"
```

Der Befehl beendet sich ohne Ausgabe und mit Status `0`, wenn die Datei
vorhanden ist.

Starte den lokalen Server aus dem Projektverzeichnis:

```bash
tools/languagetool_server.sh
```

Das Skript startet LanguageTool im Hintergrund auf Port `8081` und schreibt
sein Protokoll nach `data/languagetool-server.log`.

Prüfe den laufenden Server mit einem lokalen Texttest:

```bash
tu-web-linguacheck check-text "Das istf ein Test." --language de-DE \
  --url https://example.org/ --profile generic-de
```

Wenn der Server nicht erreichbar ist, prüfe zunächst das Protokoll:

```bash
cat data/languagetool-server.log
```

Für eine abweichende LanguageTool-Installation kann vor dem Start der
Umgebungswert `LANGUAGETOOL_HOME` auf das Verzeichnis gesetzt werden, das
`languagetool-server.jar` enthält.

## Erste Konfiguration erstellen

Kopiere die mitgelieferte Vorlage in eine lokale Konfiguration:

```bash
cp config/example.yaml config/meine-seite.local.yaml
```

Passe in `config/meine-seite.local.yaml` mindestens
`crawl.allowed_domains` an die Domain an, die geprüft werden darf. Lokale
Dateien mit dem Namensmuster `*.local.yaml` werden nicht versioniert.

Validiere die Konfiguration:

```bash
tu-web-linguacheck validate-config config/meine-seite.local.yaml
```

## Erste Website prüfen

Prüfe eine einzelne erlaubte HTML-Seite und speichere einen lokalen
HTML-Bericht:

```bash
tu-web-linguacheck check-url https://example.org/ \
  config/meine-seite.local.yaml --report reports/erster-bericht.html
```

Ersetze `https://example.org/` durch eine URL innerhalb einer in der
Konfiguration erlaubten Domain.

Weitere Konfigurationsoptionen, Crawl-Grenzen und Sicherheitsregeln beschreibt
die [Konfigurationsdokumentation](../config/README.md).

## Aktualisierung

Wechsle in das geklonte Projektverzeichnis, aktiviere die virtuelle Umgebung
und installiere die aktuelle lokale Projektversion erneut:

```bash
cd ~/tu-web-linguacheck
source .venv/bin/activate
git pull
python -m pip install .
```

Prüfe danach erneut die installierte Version:

```bash
tu-web-linguacheck --version
```
