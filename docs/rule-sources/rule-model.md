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

## Pflichtfelder

| Feld | Bedeutung |
| --- | --- |
| `id` | Eindeutige, stabile Regel-ID |
| `profile` | Zielprofil, zum Beispiel `tu-de` oder `tu-en` |
| `category` | Fachliche Kategorie der Regel |
| `authority` | Verbindlichkeitsstatus gemäß Quellenlage |
| `severity` | Schweregrad einer späteren Meldung |
| `source_ids` | Eine oder mehrere Quellen-IDs aus `sources.yaml` |
| `status` | Bearbeitungs- und Freigabestatus der Regel |

## Verbindlichkeit und Meldungsschwere

Die technische Meldungsschwere darf nicht stärker sein als die fachliche
Verbindlichkeit einer Regel.

| `authority` | Typische `severity` | Bedeutung |
| --- | --- | --- |
| `mandatory` | `warning` | Klar verbindliche institutionelle Vorgabe |
| `recommended` | `hint` | Empfohlene Schreibweise oder Stilregel |
| `voluntary` | `info` | Freiwilliger Hinweis ohne Beanstandung |
| `informational` | `info` | Hintergrundinformation |
| `review_required` | Keine automatische Meldung | Fachliche Prüfung steht aus |

## Regelstatus

| Status | Bedeutung |
| --- | --- |
| `draft` | Entwurf, noch nicht fachlich geprüft |
| `review_required` | Fachliche Auslegung oder Freigabe erforderlich |
| `approved` | Fachlich freigegeben |
| `implemented` | Technisch umgesetzt und getestet |
| `deprecated` | Nicht mehr verwenden |

## Kategorien

Voraussichtlich werden mindestens diese Kategorien benötigt:

```text
inclusive_language
salutations
pronouns
university_terminology
spelling
grammar
punctuation
translation_consistency
```

## Whitelists und Ausnahmen

Whitelists sind keine allgemeine Sammlung erwünschter Wörter. Sie dürfen nur
konkret dokumentierte Fehlalarme vermeiden.

Jeder Whitelist-Eintrag benötigt künftig mindestens:

```yaml
term: example-term
profile: tu-de
reason: false_positive_prevention
source_ids:
  - tu-de-example-source
status: approved
```

Eine Whitelist darf keine Rechtschreib-, Grammatik- oder Stilprüfung pauschal
unterdrücken.
