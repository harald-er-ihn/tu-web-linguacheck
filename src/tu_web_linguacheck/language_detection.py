"""Lokale Erkennung englischer Textspannen im sprachlichen Kontext."""

# pylint: disable-next=no-name-in-module
from lingua import Language, LanguageDetectorBuilder

_DETECTOR = LanguageDetectorBuilder.from_languages(
    Language.GERMAN,
    Language.ENGLISH,
).build()


def find_english_text_spans(text: str) -> tuple[tuple[int, int], ...]:
    """Gibt zusammenhängende englische Textspannen als Zeichenbereiche zurück."""
    return tuple(
        (result.start_index, result.end_index)
        for result in _DETECTOR.detect_multiple_languages_of(text)
        if result.language == Language.ENGLISH
    )
