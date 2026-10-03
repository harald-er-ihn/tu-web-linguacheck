# Evaluation lokaler Eigennamenerkennung

## Zweck

Dieses Dokument enthält eine kleine, manuell geprüfte Goldstandard-Stichprobe
zur Evaluation lokaler Named-Entity-Recognition-Modelle für deutschsprachige
Webinhalte.

Die Stichprobe bewertet, ob ein Modell Personenentitäten erkennt. Sie ist keine
produktive Prüfregel und unterdrückt keine LanguageTool- oder
`HTML_LANGUAGE`-Funde.

Die Textauszüge stammen aus öffentlich sichtbaren Inhalten des praktischen
CFV-Crawls. Sie wurden auf die für die Evaluation benötigten Kontexte begrenzt.

## Bewertungsregel

Eine erwartete Personenentität muss vollständig als Personenentität erkannt
werden. Nicht-Personen dürfen nicht als Personenentität erkannt werden.

Für eine spätere automatische Unterdrückung von Sprachhinweisen genügt eine
gute allgemeine Modellbewertung nicht. Entscheidend ist insbesondere, dass
tatsächliche englische Ausdrücke nicht fälschlich als Person klassifiziert
werden.

## Goldstandard-Stichprobe

### `person-saloua-mohammed`

- Textauszug: `Saloua Mohammed ist Referentin für Rassismuskritik und
  Rechtsextremismusprävention.`
- Erwartete Personenspanne: `Saloua Mohammed`
- Erwartete Nicht-Personenspanne: keine

### `person-simon-sidney-hoelscher`

- Textauszug: `Simon Sidney Hölscher ist Politikwissenschaftler, Historiker und
  Bildungswissenschaftler.`
- Erwartete Personenspanne: `Simon Sidney Hölscher`
- Erwartete Nicht-Personenspanne: keine

### `person-atahan-demirel`

- Textauszug: `Workshop mit Atahan Demirel.`
- Erwartete Personenspanne: `Atahan Demirel`
- Erwartete Nicht-Personenspanne: `Workshop`

### `person-mahtab-dadarsefatmahboob`

- Textauszug: `Der Safer Space wird von Mahtab Dadarsefatmahboob moderiert.`
- Erwartete Personenspanne: `Mahtab Dadarsefatmahboob`
- Erwartete Nicht-Personenspanne: `Safer Space`

### `person-stephan-grigat`

- Textauszug: `Projektleitung: Prof. Dr. Stephan Grigat.`
- Erwartete Personenspanne: `Stephan Grigat`
- Erwartete Nicht-Personenspanne: `Projektleitung`

### `person-single-saloua`

- Textauszug: `Saloua ist Referentin für Rassismuskritik.`
- Erwartete Personenspanne: `Saloua`
- Erwartete Nicht-Personenspanne: keine

### `person-single-sidney`

- Textauszug: `Sidney ist Politikwissenschaftler.`
- Erwartete Personenspanne: `Sidney`
- Erwartete Nicht-Personenspanne: keine

### `person-single-atahan`

- Textauszug: `Atahan moderiert den Workshop.`
- Erwartete Personenspanne: `Atahan`
- Erwartete Nicht-Personenspanne: `Workshop`

### `person-single-grigat`

- Textauszug: `Grigat hält einen Vortrag.`
- Erwartete Personenspanne: `Grigat`
- Erwartete Nicht-Personenspanne: keine

### `english-active-bystanding`

- Textauszug: `Dieses Modell bietet Orientierung für active Bystanding.`
- Erwartete Personenspanne: keine
- Erwartete Nicht-Personenspanne: `active Bystanding`

### `english-language-makes-racism`

- Textauszug: `Language makes racism - workshop for employees.`
- Erwartete Personenspanne: keine
- Erwartete Nicht-Personenspannen: `Language makes racism`;
  `workshop for employees`

### `english-ride-the-leaky-pipeline`

- Textauszug: `Das Spiel Ride the Leaky Pipeline war besonders gefragt.`
- Erwartete Personenspanne: keine
- Erwartete Nicht-Personenspanne: `Ride the Leaky Pipeline`

### `organization-centrum`

- Textauszug: `Das Centrum für Antisemitismus- und Rassismusstudien
  informiert.`
- Erwartete Personenspanne: keine
- Erwartete Nicht-Personenspanne:
  `Centrum für Antisemitismus- und Rassismusstudien`

### `term-flinta`

- Textauszug: `Die FLINTA*-Person wird bis zur Professur begleitet.`
- Erwartete Personenspanne: keine
- Erwartete Nicht-Personenspanne: `FLINTA`

## Bekannte anspruchsvolle Fälle

`Workshop mit Atahan Demirel.` ist ein bewusst aufgenommener Negativfall.
Das bisher lokal evaluierte spaCy-Modell `de_core_news_sm` erkannte
`Workshop` fälschlich als Personenentität. Eine spätere Regel darf deshalb
nicht allein jede vom Modell erkannte Personenentität übernehmen.

## Lokale Modellauswertung

Die folgende Auswertung wurde lokal mit spaCy `3.8.16` und
`de_core_news_lg` `3.8.0` gegen die 14 Fälle dieser Goldstandard-Stichprobe
ermittelt. Das große deutsche Modell wurde ausschließlich für die Evaluation
in einer lokalen virtuellen Umgebung installiert.

| Modell | Version | Personen | Fehlalarme | Präzision | Recall |
| --- | --- | ---: | ---: | ---: | ---: |
| `de_core_news_lg` | `3.8.0` | 9 von 9 | keine | 9 von 9 | 9 von 9 |

Das kleine Modell `de_core_news_sm` wurde bislang nur gegen die ursprünglichen
zehn Fälle ausgewertet. Es erkannte damals 5 von 5 Personen, klassifizierte
jedoch `Workshop` fälschlich als Personenentität.

Das große Modell erkannte in der erweiterten Stichprobe alle erwarteten
Personen und klassifizierte keinen der dokumentierten Nicht-Personenfälle als
Person. Die Stichprobe ist jedoch weiterhin zu klein für eine automatische
Unterdrückung von Sprachhinweisen. Sie rechtfertigt zunächst nur eine
weiterführende Evaluation des großen Modells.

## Status

Die Stichprobe dient ausschließlich der Evaluation. Eine Integration lokaler
Eigennamenerkennung in die Produktionsprüfung erfordert vorab:

1. eine dokumentierte Auswertung gegen diese Stichprobe,
2. eine fachliche Entscheidung über zulässige Fehlerraten,
3. eine getrennte Entscheidung, ob Modelle nur zusätzliche Hinweise liefern
   oder Funde automatisch unterdrücken dürfen.
