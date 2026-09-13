"""Tests für die lokale TU-Terminologiedatenbank."""

from pathlib import Path

from tu_web_linguacheck.terminology import (
    TerminologyEntry,
    find_german_terminology_matches,
    find_missing_english_translations,
    find_terminology_matches,
    load_terminology,
)


def test_load_terminology_loads_preferred_terms_and_variants(tmp_path: Path) -> None:
    """Die lokale JSON-Datei liefert bevorzugte Begriffe und zu prüfende Varianten."""
    terminology_path = tmp_path / "tu-terminology.local.json"
    terminology_path.write_text(
        """\
{
  "schema_version": 1,
  "entries": [
    {
      "german": "Technische Universität Dortmund",
      "preferred_english": "TU Dortmund University",
      "variants_to_flag": [
        "Technical University of Dortmund"
      ]
    }
  ]
}
""",
        encoding="utf-8",
    )

    entries = load_terminology(terminology_path)

    assert len(entries) == 1
    assert entries[0].preferred_english == "TU Dortmund University"
    assert entries[0].german == "Technische Universität Dortmund"
    assert entries[0].variants_to_flag == ("Technical University of Dortmund",)


def test_find_terminology_matches_finds_variants_case_insensitively() -> None:
    """Die Suche findet unerwünschte Varianten mit Position und bevorzugter Form."""
    entries = (
        TerminologyEntry(
            preferred_english="TU Dortmund University",
            variants_to_flag=("Technical University of Dortmund",),
        ),
    )

    matches = find_terminology_matches(
        "The TECHNICAL UNIVERSITY OF DORTMUND is located in Germany.",
        entries,
    )

    assert len(matches) == 1
    assert matches[0].offset == 4
    assert matches[0].length == 32
    assert matches[0].matched_text == "TECHNICAL UNIVERSITY OF DORTMUND"
    assert matches[0].preferred_term == "TU Dortmund University"


def test_find_terminology_matches_finds_all_variant_occurrences() -> None:
    """Die Suche findet jedes Vorkommen einer unerwünschten Variante."""
    entries = (
        TerminologyEntry(
            preferred_english="TU Dortmund University",
            variants_to_flag=("Technical University of Dortmund",),
        ),
    )

    matches = find_terminology_matches(
        "Technical University of Dortmund and Technical University of Dortmund",
        entries,
    )

    assert len(matches) == 2
    assert [match.offset for match in matches] == [0, 37]


def test_load_terminology_loads_language_neutral_preferred_terms(
    tmp_path: Path,
) -> None:
    """Die lokale JSON-Datei akzeptiert sprachneutrale bevorzugte Begriffe."""
    terminology_path = tmp_path / "tu-inclusive-language.local.json"
    terminology_path.write_text(
        """\
{
  "schema_version": 1,
  "entries": [
    {
      "preferred_term": "Lehrkräfte",
      "variants_to_flag": ["Lehrer"]
    }
  ]
}
""",
        encoding="utf-8",
    )

    entries = load_terminology(terminology_path)

    assert len(entries) == 1
    assert entries[0].preferred_term == "Lehrkräfte"
    assert entries[0].variants_to_flag == ("Lehrer",)


def test_find_german_terminology_matches_finds_source_terms() -> None:
    """Die Suche findet deutsche Quellbegriffe mit gewünschter englischer Form."""
    entries = (
        TerminologyEntry(
            preferred_english="Office for Diversity and Equal Opportunities",
            variants_to_flag=(),
            german="Stabsstelle Chancengleichheit, Familie und Vielfalt",
        ),
    )

    matches = find_german_terminology_matches(
        "Die Stabsstelle Chancengleichheit, Familie und Vielfalt berät Beschäftigte.",
        entries,
    )

    assert len(matches) == 1
    assert (
        matches[0].matched_text == "Stabsstelle Chancengleichheit, Familie und Vielfalt"
    )
    assert matches[0].offset == 4
    assert matches[0].length == 51
    assert matches[0].preferred_term == "Office for Diversity and Equal Opportunities"


def test_find_missing_english_translations_reports_missing_preferred_term() -> None:
    """Ein deutscher Quellbegriff wird gemeldet, wenn sein Englischziel fehlt."""
    entries = (
        TerminologyEntry(
            german="Technische Universität Dortmund",
            preferred_english="TU Dortmund University",
            variants_to_flag=(),
        ),
    )

    matches = find_missing_english_translations(
        "Die Technische Universität Dortmund informiert Studieninteressierte.",
        "Dortmund University of Technology provides prospective students.",
        entries,
    )

    assert len(matches) == 1
    assert matches[0].matched_text == "Technische Universität Dortmund"
    assert matches[0].offset == 4
    assert matches[0].length == 31
    assert matches[0].preferred_term == "TU Dortmund University"
