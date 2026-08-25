# Modell für TU-spezifische Regeln

Dieses Dokument beschreibt die Struktur, nach der spätere TU-spezifische
Terminologie-, Stil- und Whitelist-Regeln modelliert werden.

Eine Regel wird erst technisch umgesetzt, wenn ihre fachliche Grundlage,
Verbindlichkeit und beabsichtigte Prüffolge nachvollziehbar dokumentiert sind.

## Grundstruktur

```yaml
id: tu-de-example-rule
profile: tu-de
category: inclusive_language
authority: recommended
severity: hint
source_ids:
  - tu-de-inclusive-language
status: review_required
```
