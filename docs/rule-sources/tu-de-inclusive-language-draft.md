# Entwurf: Geschlechtergerechte Sprache für `tu-de`

## Zweck

Dieser Entwurf beschreibt die erste fachliche Grundlage für spätere
Stilhinweise zur geschlechtergerechten Sprache im Profil `tu-de`.

Er ist noch nicht technisch implementiert und erzeugt noch keine Meldungen.

## Regelentwurf

~~~yaml
id: tu-de-inclusive-language-preferred
profile: tu-de
category: inclusive_language
authority: recommended
severity: hint
source_ids:
  - tu-de-inclusive-language
status: review_required
~~~

## Fachliche Einordnung

Für Personenbezeichnungen sollen geschlechtergerechte, inklusive und
verständliche Formulierungen bevorzugt werden.

Mögliche Formen umfassen insbesondere:

- Personenbezeichnungen mit Gender*stern,
- Personenbezeichnungen mit Gender:Doppelpunkt,
- substantivierte Verlaufsformen,
- genderneutrale Alternativen.

## Grenzen der automatisierten Prüfung

Die Regel darf nicht pauschal jede Verwendung des generischen Maskulinums als
Fehler ausgeben. Eine automatisierte Erkennung muss Kontext, Bedeutung,
grammatische Mehrdeutigkeit und mögliche neutrale Lesarten berücksichtigen.

Meldungen sollen zunächst ausschließlich als `hint` erscheinen. Sie dürfen weder
eine Rechtschreibprüfung unterdrücken noch eine verbindliche sprachliche
Anweisung vortäuschen.

## Noch fachlich zu klären

Vor einer technischen Umsetzung müssen insbesondere diese Fragen beantwortet
werden:

1. Welche konkreten Muster sollen als prüfbare Hinweise gelten?
1. Welche Begriffe oder Kontexte müssen ausdrücklich ausgeschlossen werden?
1. Wann ist der Gender*stern gegenüber dem Gender:Doppelpunkt zu bevorzugen?
1. Welche Anforderungen zur digitalen Barrierefreiheit sind für einzelne
   Schreibweisen zu berücksichtigen?
1. Wer kann Regeln für das Profil `tu-de` fachlich freigeben?
