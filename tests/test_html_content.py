"""Tests für die Extraktion sichtbarer HTML-Inhalte."""

from tu_web_linguacheck.html_content import extract_page_content


def test_extracts_title_and_visible_main_text() -> None:
    """Seitentitel und sichtbarer Hauptinhalt werden extrahiert."""
    html = """
    <html>
      <head>
        <title>Geschlechtergerechte Sprache | TU Dortmund</title>
      </head>
      <body>
        <nav>Navigation sollte nicht erscheinen</nav>
        <main>
          <h1>Geschlechtergerechte Sprache</h1>
          <p>Dieser Inhalt soll geprüft werden.</p>
          <script>console.log("Nicht sichtbarer Code");</script>
          <style>.hidden { display: none; }</style>
        </main>
        <footer>Footer sollte nicht erscheinen</footer>
      </body>
    </html>
    """

    content = extract_page_content(html)

    assert content.title == "Geschlechtergerechte Sprache | TU Dortmund"
    assert content.text == (
        "Geschlechtergerechte Sprache\nDieser Inhalt soll geprüft werden."
    )


def test_uses_body_when_main_is_missing() -> None:
    """Ohne main-Element wird sichtbarer Body-Text verwendet."""
    html = """
    <html>
      <head><title>Ohne Hauptbereich</title></head>
      <body>
        <p>Dieser Text steht im Body.</p>
      </body>
    </html>
    """

    content = extract_page_content(html)

    assert content.title == "Ohne Hauptbereich"
    assert content.text == "Dieser Text steht im Body."


def test_preserves_visible_block_boundaries() -> None:
    """Überschriften und Absätze bleiben als getrennte Textblöcke erhalten."""
    html = """
    <html>
      <body>
        <main>
          <h1>Überschrift</h1>
          <p>Dieser Satz beginnt korrekt.</p>
          <p>Ein weiterer korrekter Satz.</p>
        </main>
      </body>
    </html>
    """

    content = extract_page_content(html)

    assert content.text == (
        "Überschrift\nDieser Satz beginnt korrekt.\nEin weiterer korrekter Satz."
    )


def test_keeps_inline_text_within_one_block_together() -> None:
    """Inline-Elemente erzeugen innerhalb eines Absatzes keine Zeilenumbrüche."""
    html = """
    <html>
      <body>
        <main>
          <p>Das ist <strong>ein</strong> Satz<span>:</span> korrekt.</p>
        </main>
      </body>
    </html>
    """

    content = extract_page_content(html)

    assert content.text == "Das ist ein Satz: korrekt."


def test_extracts_visible_blocks_with_inherited_html_language() -> None:
    """Sichtbare Textblöcke übernehmen das Sprachattribut eines Vorfahren."""
    html = """
    <html lang="de">
      <body>
        <main>
          <p>Deutscher Text.</p>
          <section lang="en">
            <h2>English</h2>
            <p>English text.</p>
          </section>
        </main>
      </body>
    </html>
    """

    content = extract_page_content(html)

    assert [(block.text, block.language) for block in content.blocks] == [
        ("Deutscher Text.", "de"),
        ("English", "en"),
        ("English text.", "en"),
    ]


def test_splits_inline_content_at_language_changes_for_any_element() -> None:
    """Jedes verschachtelte Element mit abweichender Sprache trennt Prüfblöcke."""
    html = """
    <html lang="de">
      <body>
        <main>
          <p>Deutscher Text mit <x-english lang="en">an englsh word</x-english>.</p>
        </main>
      </body>
    </html>
    """

    content = extract_page_content(html)

    assert [(block.text, block.language) for block in content.blocks] == [
        ("Deutscher Text mit", "de"),
        ("an englsh word", "en"),
        (".", "de"),
    ]
