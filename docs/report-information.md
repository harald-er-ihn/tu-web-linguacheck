# Informationen zum Sprachprüfbericht

## Zweck des Berichts

Dieser Bericht dokumentiert die lokale sprachliche Prüfung öffentlich
erreichbarer HTML-Seiten. Das Werkzeug prüft Rechtschreibung, Grammatik,
Zeichensetzung und – abhängig vom gewählten Profil – projektbezogene
Terminologie und Stilregeln.

PDF-Dateien und andere Nicht-HTML-Inhalte werden nicht geprüft.

Das Inhaltsverzeichnis führt alle erfolgreich geprüften Seiten auf. Der Eintrag
`0 Funde` bedeutet, dass für die Seite keine Sprachfunde festgestellt wurden.

## Berichtsausgaben

Die Prüfung kann einen lokalen HTML-Bericht oder einen lokalen PDF/UA-1-Bericht
erzeugen. Beide Berichtsausgaben enthalten die geprüften Seiten und die
festgestellten Sprachfunde.

## Prüfungsergebnisse richtig einordnen

Jeder Fund ist ein Hinweis zur fachlichen Prüfung, keine automatische
Feststellung eines Fehlers. Insbesondere Eigennamen, Fachbegriffe,
Abkürzungen, Zitate, fremdsprachige Textstellen und bewusst gewählte
Schreibweisen können als Fund erscheinen.

Prüfe deshalb den jeweiligen Fundkontext und entscheide anschließend, ob eine
Änderung angemessen ist. Die Vorschläge des Sprachprüfwerkszeugs dienen als
Unterstützung und müssen nicht übernommen werden.

Bei langen Vorschlagslisten zeigt der Bericht höchstens fünf Vorschläge direkt
an. Weitere Vorschläge werden nur als Anzahl zusammengefasst, damit die
Fundübersicht übersichtlich bleibt.

Der Bericht zeigt für jeden Fund bis zu 80 Zeichen vor und nach der Fundstelle.
Die Fundstelle selbst ist im HTML-Bericht hervorgehoben. Dadurch bleibt der
Kontext für die Bewertung nachvollziehbar, ohne den vollständigen Seitentext zu
wiederholen.

## Prüfprofile

- `generic-de` prüft deutschsprachige Websites auf Rechtschreibung,
  Grammatik, Zeichensetzung und ungewöhnliche Wörter.
- `tu-de` ergänzt die deutsche Prüfung für TU-Dortmund-Websites um
  Terminologie- und Stilregeln.
- `tu-en` prüft englischsprachige TU-Dortmund-Websites mit `en-US` sowie
  ergänzender Terminologie und Stilregeln.
- `tu` kombiniert die deutsche und englische TU-Terminologieprüfung für
  sprachsegmentierte Websites.

## Übersetzungsfunde

Bei fehlenden bevorzugten englischen Übersetzungen zeigt der Bericht den
deutschen Quellbegriff, die erwartete englische Übersetzung und die Anzahl der
Vorkommen des Quellbegriffs im vollständigen deutschen Quelltext. Derselbe
fehlende Terminologieeintrag wird je deutschem Quell- und englischem Zielseitenpaar
nur einmal berichtet.

## Sprachprüfwerkzeug und Sprachen

Für Rechtschreibung, Grammatik und Zeichensetzung nutzt das Werkzeug einen
lokal betriebenen [LanguageTool](https://languagetool.org/)-Server. Die
Regelmenge richtet sich nach der effektiven HTML-Sprache eines Textsegments:

- Ohne `lang` gilt die in der Konfiguration angegebene Fallbacksprache, zum
  Beispiel `de-DE`.
- `lang="de"` wird mit der konfigurierten deutschen Sprachvariante geprüft.
- `lang="en"` wird mit `en-US` geprüft.
- Explizite Varianten wie `lang="en-GB"` sowie weitere Sprachen wie `fr` oder
  `es` werden entsprechend an LanguageTool übergeben.

Lokale TU-Terminologie wird derzeit nur für deutsche und englische Segmente
geprüft.

## Datenschutz und lokale Verarbeitung

Website-Texte, Crawl-Daten und Prüfergebnisse bleiben lokal. Das Werkzeug
nutzt keine externen Cloud-KI- oder Sprachprüfungs-APIs.

## Regelquellen

TU-spezifische Regeln werden nachvollziehbar über Quellen-IDs dokumentiert.
Zugriffsgeschützte, interne oder in der Weitergabe ungeklärte
Originaldokumente werden nicht in das öffentliche Projekt aufgenommen.

## Installation

Das freie Werkzeug kann lokal selbst installiert werden. Eine Anleitung für
Windows mit WSL2 ist im
[öffentlichen Repository](https://github.com/harald-er-ihn/tu-web-linguacheck/blob/main/docs/installation-wsl2.md)
verfügbar.
