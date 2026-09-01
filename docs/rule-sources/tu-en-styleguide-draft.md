# Entwurf: Englischer Sprachgebrauch für `tu-en`

## Zweck

Dieser Entwurf dokumentiert erste fachliche Grundlagen für spätere
Terminologie- und Stilhinweise im Profil `tu-en`.

Er ist noch nicht technisch implementiert und erzeugt noch keine Meldungen.

## Regelentwürfe

~~~yaml
id: tu-en-american-english
profile: tu-en
category: spelling
authority: mandatory
severity: warning
source_ids:
  - tu-en-styleguide
status: review_required
~~~

~~~yaml
id: tu-en-university-name
profile: tu-en
category: university_terminology
authority: mandatory
severity: warning
source_ids:
  - tu-en-styleguide
status: review_required
~~~

## Fachliche Einordnung

Englischsprachige Texte und die Kommunikation mit internationalen Kontakten
folgen den Prinzipien des amerikanischen Englischs. Dies betrifft insbesondere
Schreibweise, Wortwahl und Layout in formalisierten Kontexten.

Die Universität wird auf Englisch grundsätzlich als `TU Dortmund University`
bezeichnet. Abweichende oder teilweise übersetzte Bezeichnungen müssen vor einer
späteren automatisierten Meldung fachlich eindeutig abgegrenzt werden.

## Grenzen der automatisierten Prüfung

Die Wahl zwischen amerikanischen und anderen englischen Varianten darf nicht
pauschal anhand einzelner Wörter beanstandet werden. Eine spätere Prüfung muss
Kontext, Eigennamen, Zitate, externe Organisationen und bewusst verwendete
Originalschreibweisen berücksichtigen.

Die Terminologieregel zum Universitätsnamen darf nicht in Eigennamen, URLs,
Zitaten oder Bezeichnungen anderer Institutionen eingreifen.

Solange beide Regeln den Status `review_required` haben, erzeugen sie keine
automatisierten Meldungen.

## Noch fachlich zu klären

Vor einer technischen Umsetzung müssen insbesondere diese Fragen beantwortet
werden:

1. Welche amerikanischen und britischen Schreibvarianten sind konkret prüfbar?
1. Welche Ausnahmen gelten für Zitate, Publikationstitel und externe Eigennamen?
1. Welche unzulässigen Varianten des Universitätsnamens sollen erkannt werden?
1. In welchen Kontexten ist eine Kurzform wie `TU Dortmund` zulässig?
1. Wer kann Regeln für das Profil `tu-en` fachlich freigeben?
