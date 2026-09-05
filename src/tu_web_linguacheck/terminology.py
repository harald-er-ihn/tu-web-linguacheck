"""Laden der lokalen TU-Terminologiedatenbank."""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TerminologyEntry:
    """Ein bevorzugter englischer Begriff mit unerwünschten Varianten."""

    preferred_english: str
    variants_to_flag: tuple[str, ...]


def load_terminology(path: Path) -> tuple[TerminologyEntry, ...]:
    """Lädt bevorzugte Begriffe und zu prüfende Varianten aus einer JSON-Datei."""
    payload = json.loads(path.read_text(encoding="utf-8"))

    return tuple(
        TerminologyEntry(
            preferred_english=entry["preferred_english"],
            variants_to_flag=tuple(entry["variants_to_flag"]),
        )
        for entry in payload["entries"]
    )


@dataclass(frozen=True)
class TerminologyMatch:
    """Eine im Text gefundene unerwünschte Terminologievariante."""

    matched_text: str
    offset: int
    length: int
    preferred_english: str


def find_terminology_matches(
    text: str,
    entries: tuple[TerminologyEntry, ...],
) -> list[TerminologyMatch]:
    """Findet unerwünschte Terminologievarianten unabhängig von Großschreibung."""
    matches: list[TerminologyMatch] = []
    normalized_text = text.casefold()

    for entry in entries:
        for variant in entry.variants_to_flag:
            normalized_variant = variant.casefold()
            offset = normalized_text.find(normalized_variant)

            while offset >= 0:
                matches.append(
                    TerminologyMatch(
                        matched_text=text[offset : offset + len(variant)],
                        offset=offset,
                        length=len(variant),
                        preferred_english=entry.preferred_english,
                    )
                )
                offset = normalized_text.find(
                    normalized_variant,
                    offset + len(normalized_variant),
                )

    return matches
