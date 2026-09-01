"""Tests für die Extraktion allgemeiner Seitenlinks."""

from tu_web_linguacheck.page_links import extract_page_links


def test_extract_page_links_resolves_regular_main_links() -> None:
    """Normale Links aus dem Hauptinhalt werden aufgelöst und gefiltert."""
    html = """
    <html>
      <body>
        <nav>
          <a href="/navigation/">Navigation</a>
        </nav>
        <main>
          <a href="team/">Team</a>
          <a href="https://cs.tu-dortmund.de/studium/">Studium</a>
          <a href="#kontakt">Kontakt</a>
          <a href="mailto:info@example.org">E-Mail</a>
          <a href="tel:+492317550">Telefon</a>
          <a href="javascript:void(0)">Menü</a>
        </main>
      </body>
    </html>
    """

    links = extract_page_links(
        "https://cs.tu-dortmund.de/fakultaet/",
        html,
    )

    assert links == [
        "https://cs.tu-dortmund.de/fakultaet/team/",
        "https://cs.tu-dortmund.de/studium/",
    ]
