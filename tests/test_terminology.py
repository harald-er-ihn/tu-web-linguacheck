"""Tests für die lokale TU-Terminologiedatenbank."""

from pathlib import Path

from tu_web_linguacheck.terminology import load_terminology


def test_load_terminology_loads_preferred_terms_and_variants(tmp_path: Path) -> None:
    """Die lokale JSON-Datei liefert bevorzugte Begriffe und zu prüfende Varianten."""
    terminology_path = tmp_path / "tu-terminology.local.json"
    terminology_path.write_text(
        """\
{
  "schema_version": 1,
  "entries": [
    {
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
    assert entries[0].variants_to_flag == ("Technical University of Dortmund",)
