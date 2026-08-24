"""Tests für die Erkennung von Sprachvarianten in HTML-Dokumenten."""

from tu_web_linguacheck.language_links import (
    LanguageLink,
    find_hreflang_links,
    find_language_switcher_links,
    merge_language_links,
)


def test_finds_english_language_switcher() -> None:
    """Ein Link mit dem Text English wird als englischer Sprachlink erkannt."""
    html = """
    <nav>
      <a href="/en/diversity/diversity-month/">English</a>
    </nav>
    """

    links = find_language_switcher_links(html)

    assert links == [
        LanguageLink(
            href="/en/diversity/diversity-month/",
            language="en",
            detection_method="language_switcher",
        )
    ]


def test_finds_german_language_switcher() -> None:
    """Ein Link mit dem Text Deutsch wird als deutscher Sprachlink erkannt."""
    html = """
    <nav>
      <a href="/vielfalt/diversity-monat/">Deutsch</a>
    </nav>
    """

    links = find_language_switcher_links(html)

    assert links == [
        LanguageLink(
            href="/vielfalt/diversity-monat/",
            language="de",
            detection_method="language_switcher",
        )
    ]


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


def test_finds_hreflang_alternatives() -> None:
    """Hreflang-Alternativen werden mit URL und Sprachcode erkannt."""
    html = """
    <head>
      <link rel="alternate" hreflang="de" href="/vielfalt/diversity-monat/" />
      <link
        rel="alternate"
        hreflang="en"
        href="/en/diversity/diversity-month/"
      />
    </head>
    """

    links = find_hreflang_links(html)

    assert links == [
        LanguageLink(
            href="/vielfalt/diversity-monat/",
            language="de",
            detection_method="hreflang",
        ),
        LanguageLink(
            href="/en/diversity/diversity-month/",
            language="en",
            detection_method="hreflang",
        ),
    ]


def test_ignores_non_language_hreflang_links() -> None:
    """x-default und Links ohne alternate-Relation werden ignoriert."""
    html = """
    <head>
      <link rel="alternate" hreflang="x-default" href="/" />
      <link rel="canonical" hreflang="en" href="/en/" />
    </head>
    """

    links = find_hreflang_links(html)

    assert links == []


def test_normalizes_regional_hreflang_codes() -> None:
    """Regionale deutsche und englische hreflang-Codes werden normalisiert."""
    html = """
    <head>
      <link rel="alternate" hreflang="de-DE" href="/de/" />
      <link rel="alternate" hreflang="en-US" href="/en-us/" />
      <link rel="alternate" hreflang="en-GB" href="/en-gb/" />
    </head>
    """

    links = find_hreflang_links(html)

    assert links == [
        LanguageLink(
            href="/de/",
            language="de",
            detection_method="hreflang",
        ),
        LanguageLink(
            href="/en-us/",
            language="en",
            detection_method="hreflang",
        ),
        LanguageLink(
            href="/en-gb/",
            language="en",
            detection_method="hreflang",
        ),
    ]


def test_prefers_hreflang_over_visible_language_switcher() -> None:
    """Hreflang hat Vorrang vor einem identischen sichtbaren Sprachumschalter."""
    links = [
        LanguageLink(
            href="/en/page/",
            language="en",
            detection_method="language_switcher",
        ),
        LanguageLink(
            href="/en/page/",
            language="en",
            detection_method="hreflang",
        ),
    ]

    merged_links = merge_language_links(links)

    assert merged_links == [
        LanguageLink(
            href="/en/page/",
            language="en",
            detection_method="hreflang",
        )
    ]


def test_keeps_language_links_with_different_targets() -> None:
    """Unterschiedliche Sprachziele bleiben als eigene Einträge erhalten."""
    links = [
        LanguageLink(
            href="/de/page/",
            language="de",
            detection_method="hreflang",
        ),
        LanguageLink(
            href="/en/page/",
            language="en",
            detection_method="language_switcher",
        ),
    ]

    merged_links = merge_language_links(links)

    assert merged_links == links
