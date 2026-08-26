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
        "Geschlechtergerechte Sprache Dieser Inhalt soll geprüft werden."
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
