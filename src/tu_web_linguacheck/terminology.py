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
