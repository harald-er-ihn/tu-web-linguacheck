"""Tests für die Erkennung von Sprachumschaltern."""

from tu_web_linguacheck.language_links import find_language_switcher_links


def test_finds_english_language_switcher() -> None:
    """Ein Link mit dem Text English wird als englischer Sprachlink erkannt."""
    html = """
    <nav>
      <a href="/en/diversity/diversity-month/">English</a>
    </nav>
    """

    links = find_language_switcher_links(html)

    assert links == [("/en/diversity/diversity-month/", "en")]


def test_finds_german_language_switcher() -> None:
    """Ein Link mit dem Text Deutsch wird als deutscher Sprachlink erkannt."""
    html = """
    <nav>
      <a href="/vielfalt/diversity-monat/">Deutsch</a>
    </nav>
    """

    links = find_language_switcher_links(html)

    assert links == [("/vielfalt/diversity-monat/", "de")]


def test_ignores_unrelated_links() -> None:
    """Normale Navigationslinks sind keine Sprachumschalter."""
    html = """
    <nav>
      <a href="/ueber-uns/">Über uns</a>
      <a href="/kontakt/">Kontakt</a>
    </nav>
    """

    links = find_language_switcher_links(html)

    assert links == []
