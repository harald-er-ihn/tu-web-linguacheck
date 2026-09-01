# Entwurf: TU-Terminologie für `tu-en`

## Zweck

Dieser Entwurf dokumentiert belegte deutsch-englische Terminologiepaare für
spätere Prüfungen der Übersetzungskonsistenz im Profil `tu-en`.

Er ist noch nicht technisch implementiert und erzeugt noch keine Meldungen.

## Terminologieentwurf

~~~yaml
id: tu-en-staff-unit-equal-opportunities-family-diversity
profile: tu-en
category: university_terminology
authority: mandatory
severity: warning
source_ids:
  - tu-en-styleguide
status: review_required
de_term: Stabsstelle Chancengleichheit, Familie und Vielfalt
en_term: Staff Unit Equal Opportunities, Family and Diversity
~~~

## Fachliche Einordnung

Das TU-Wörterbuch führt die vollständige deutsche Bezeichnung mit der
englischen Entsprechung `Staff Unit Equal Opportunities, Family and Diversity`.

Die allgemeine Übersetzung von `Stabsstelle` als `Staff Unit` wird durch mehrere
weitere Einträge des Wörterbuchs gestützt. Für automatische Prüfungen sollen
jedoch zunächst vollständige, fachlich belegte Bezeichnungspaare verwendet
werden.

## Grenzen der automatisierten Prüfung

Ein fehlender vollständiger englischer Begriff beweist keinen Übersetzungsfehler.
Er kann insbesondere durch einen Rechtschreibfehler, eine zulässige abweichende
Formulierung oder einen anderen Seitenkontext verursacht sein.

Eine spätere Prüfung muss deshalb zwischen diesen Fällen unterscheiden:

- erwartete Terminologie vollständig gefunden,
- erwartete Terminologie nahezu gefunden, aber mit Sprachfehler,
- erwartete Terminologie nicht gefunden und fachlich zu prüfen.

Solange der Status `review_required` gilt, erzeugt dieser Entwurf keine
automatisierte Meldung.

## Noch fachlich zu klären

1. Welche Normalisierungen sind für Bindestriche, Zeilenumbrüche und Leerzeichen
   zulässig?
1. Wie viele und welche zulässigen englischen Varianten darf ein Begriff haben?
1. Wann genügt die Prüfung einzelner Bestandteile statt der vollständigen
   Bezeichnung?
1. Wer kann Terminologieeinträge für `tu-en` fachlich freigeben?
