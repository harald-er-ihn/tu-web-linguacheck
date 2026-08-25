"""Tests für die Erkennung von Sprachvarianten in HTML-Dokumenten."""

from tu_web_linguacheck.language_links import (
    LanguageLink,
    filter_allowed_language_links,
    find_allowed_page_language_links,
    find_hreflang_links,
    find_language_links_for_language,
    find_language_switcher_links,
    find_page_language_links,
    merge_language_links,
    resolve_language_link,
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

    assert not links


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

    assert not links


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


def test_resolves_domain_relative_language_link() -> None:
    """Ein domain-relativer Sprachlink wird gegen die Basis-URL aufgelöst."""
    language_link = LanguageLink(
        href="/en/diversity/diversity-month/",
        language="en",
        detection_method="hreflang",
    )

    resolved_link = resolve_language_link(
        "https://stabsstelle-cfv.tu-dortmund.de/vielfalt/diversity-monat/",
        language_link,
    )

    assert resolved_link == LanguageLink(
        href="https://stabsstelle-cfv.tu-dortmund.de/en/diversity/diversity-month/",
        language="en",
        detection_method="hreflang",
    )


def test_resolves_path_relative_language_link() -> None:
    """Ein pfad-relativer Sprachlink wird gegen den aktuellen Pfad aufgelöst."""
    language_link = LanguageLink(
        href="en/forschung/",
        language="en",
        detection_method="language_switcher",
    )

    resolved_link = resolve_language_link(
        "https://cs.tu-dortmund.de/forschung/",
        language_link,
    )

    assert resolved_link == LanguageLink(
        href="https://cs.tu-dortmund.de/forschung/en/forschung/",
        language="en",
        detection_method="language_switcher",
    )


def test_keeps_absolute_language_link() -> None:
    """Ein absoluter Sprachlink bleibt unverändert."""
    language_link = LanguageLink(
        href="https://cs.tu-dortmund.de/en/forschung/",
        language="en",
        detection_method="hreflang",
    )

    resolved_link = resolve_language_link(
        "https://cs.tu-dortmund.de/forschung/",
        language_link,
    )

    assert resolved_link == language_link


def test_finds_resolved_and_merged_page_language_links() -> None:
    """Sprachlinks einer Seite werden aufgelöst und nach Quelle priorisiert."""
    html = """
    <head>
      <link rel="alternate" hreflang="en" href="/en/page/" />
    </head>
    <nav>
      <a href="https://example.tu-dortmund.de/en/page/">English</a>
    </nav>
    """

    links = find_page_language_links(
        "https://example.tu-dortmund.de/de/page/",
        html,
    )

    assert links == [
        LanguageLink(
            href="https://example.tu-dortmund.de/en/page/",
            language="en",
            detection_method="hreflang",
        )
    ]


def test_filters_language_links_to_allowed_domains() -> None:
    """Nur Sprachlinks zu erlaubten Domains bleiben erhalten."""
    links = [
        LanguageLink(
            href="https://stabsstelle-cfv.tu-dortmund.de/en/diversity/",
            language="en",
            detection_method="hreflang",
        ),
        LanguageLink(
            href="https://external.example/en/diversity/",
            language="en",
            detection_method="language_switcher",
        ),
    ]

    filtered_links = filter_allowed_language_links(links, ["tu-dortmund.de"])

    assert filtered_links == [
        LanguageLink(
            href="https://stabsstelle-cfv.tu-dortmund.de/en/diversity/",
            language="en",
            detection_method="hreflang",
        )
    ]


def test_filters_similar_but_foreign_domain_from_language_links() -> None:
    """Ähnlich aussehende fremde Domains bleiben ausgeschlossen."""
    links = [
        LanguageLink(
            href="https://tu-dortmund.de.example.org/en/page/",
            language="en",
            detection_method="hreflang",
        )
    ]

    filtered_links = filter_allowed_language_links(links, ["tu-dortmund.de"])

    assert not filtered_links


def test_finds_only_allowed_page_language_links() -> None:
    """Eine Seite liefert nur aufgelöste Sprachlinks zu erlaubten Domains."""
    html = """
    <head>
      <link rel="alternate" hreflang="en" href="/en/page/" />
    </head>
    <nav>
      <a href="https://external.example/en/page/">English</a>
    </nav>
    """

    links = find_allowed_page_language_links(
        "https://stabsstelle-cfv.tu-dortmund.de/de/page/",
        html,
        ["tu-dortmund.de"],
    )

    assert links == [
        LanguageLink(
            href="https://stabsstelle-cfv.tu-dortmund.de/en/page/",
            language="en",
            detection_method="hreflang",
        )
    ]


def test_finds_language_links_for_requested_language() -> None:
    """Nur Sprachlinks zur angeforderten Sprache werden zurückgegeben."""
    links = [
        LanguageLink(
            href="https://example.tu-dortmund.de/de/page/",
            language="de",
            detection_method="hreflang",
        ),
        LanguageLink(
            href="https://example.tu-dortmund.de/en/page/",
            language="en",
            detection_method="language_switcher",
        ),
    ]

    matching_links = find_language_links_for_language(links, "en")

    assert matching_links == [
        LanguageLink(
            href="https://example.tu-dortmund.de/en/page/",
            language="en",
            detection_method="language_switcher",
        )
    ]


def test_returns_no_language_links_when_language_is_not_available() -> None:
    """Ohne passenden Sprachlink wird eine leere Liste zurückgegeben."""
    links = [
        LanguageLink(
            href="https://example.tu-dortmund.de/de/page/",
            language="de",
            detection_method="hreflang",
        )
    ]

    matching_links = find_language_links_for_language(links, "en")

    assert not matching_links
