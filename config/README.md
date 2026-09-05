# Konfigurationen

Dieses Verzeichnis enthält YAML-Konfigurationen für `tu-web-linguacheck`.

- `example.yaml` ist eine versionierte Vorlage.
- Dateien mit dem Namen `*.local.yaml` sowie `local.yaml` sind für lokale
  Konfigurationen vorgesehen und werden von Git ignoriert.
- Lokale Konfigurationen dürfen domainspezifische Einstellungen und
  projektspezifische Ausnahmen enthalten.

Eine Konfiguration wird vor der Nutzung validiert:

```bash
tu-web-linguacheck validate-config config/meine-seite.local.yaml
```

Einen Crawl mit Sprachprüfung startest du beispielsweise so:

```bash
tu-web-linguacheck check-crawl https://example.org/ config/meine-seite.local.yaml
```

## Grundstruktur

```yaml
profile: generic-de

crawl:
  allowed_domains:
    - example.org
  max_depth: 2
  max_pages: 100
  requests_per_second: 1.0
  obey_robots_txt: true
  strip_fragments: true
  tracking_parameters: []
  exclude_patterns: []
  sitemap_urls: []

check:
  language: de-DE
  ignored_rule_ids: []
  ignored_terms: []
```

## `profile`

Das Profil legt den Regelbestand fest:

- `generic-de`: allgemeine deutsche Prüfung.
- `tu-de`: deutsche Prüfung mit TU-Dortmund-Regeln.
- `tu-en`: englische Prüfung mit TU-Dortmund-Regeln.

## Bereich `crawl`

| Feld | Bedeutung |
| --- | --- |
| `allowed_domains` | Erlaubte Domains; echte Subdomains sind erlaubt. |
| `max_depth` | Maximale Linktiefe; Sitemap-URLs starten bei `0`. |
| `max_pages` | Maximale Anzahl abzurufender HTML-Seiten. |
| `requests_per_second` | Höchste Abrufrate; muss größer als `0` sein. |
| `obey_robots_txt` | `true` oder `false`; robots.txt wird beachtet. |
| `strip_fragments` | Entfernt URL-Fragmente wie `#abschnitt`. |
| `tracking_parameters` | Vor dem Crawl entfernte Query-Parameter. |
| `exclude_patterns` | Reguläre Ausdrücke für auszuschließende URLs. |
| `sitemap_urls` | Optionale Liste veröffentlichter XML-Sitemaps. |

### `exclude_patterns`

Ausschlussmuster gelten sowohl für normale Links als auch für URLs aus
XML-Sitemaps. Sie eignen sich für nicht relevante Archive, einzelne Seiten
oder Nicht-HTML-Dateien.

```yaml
exclude_patterns:
  - '/tag(?:/|$)'
  - '/author/cri-stian/'
  - '/wpa-stats-type(?:/|$)'
  - '/uo-recipe(?:/|$)'
  - '/qi-gong-und-schwarze-tusche/'
```

### `sitemap_urls`

`tu-web-linguacheck` ruft die angegebenen XML-Sitemaps lokal und geschützt ab.
Sitemap-Indizes mit untergeordneten Sitemaps werden rekursiv verarbeitet.
Zulässige Seiten-URLs werden als zusätzliche Start-URLs mit Tiefe `0` in den
BFS-Crawl aufgenommen.

```yaml
sitemap_urls:
  - https://example.org/sitemap.xml
```

Die Sitemap muss mit dem Content-Type `application/xml` oder `text/xml`
ausgeliefert werden. HTML-Sitemap-Seiten wie `https://example.org/sitemap/`
können derzeit nicht unter `sitemap_urls` verwendet werden.

Direkte Seiten-URLs aus `<url><loc>` und untergeordnete Sitemaps aus
`<sitemap><loc>` werden berücksichtigt. Verschachtelte Bild-URLs wie
`<image:loc>` werden ignoriert.

## Bereich `check`

| Feld | Bedeutung |
| --- | --- |
| `language` | LanguageTool-Sprache, etwa `de-DE` oder `en-US`. |
| `ignored_rule_ids` | Regel-IDs, deren Funde nicht berichtet werden. |
| `ignored_terms` | Begriffe, die nicht als Rechtschreibfund berichtet werden. |

Mit `ignored_rule_ids` lassen sich bekannte, für das Projekt nicht relevante
Regeln ausblenden:

```yaml
check:
  ignored_rule_ids:
    - DE_SIMPLE_REPLACE_QI_GONG
```

Mit `ignored_terms` können projektspezifische Eigennamen ergänzt werden:

```yaml
check:
  ignored_terms:
    - TiMana
    - Samtosha
```
