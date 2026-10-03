"""Tests für die lokale kontextbezogene Sprachidentifikation."""

from tu_web_linguacheck.language_detection import find_english_text_spans


def test_find_english_text_spans_uses_surrounding_context() -> None:
    """Erkennt englische Spannen, aber keinen Eigennamen im deutschen Satz."""
    texts = (
        "Die Pflegelotsin Sonja Wentzel der FH Dortmund informiert.",
        "Dieses Modell bietet Orientierung für active Bystanding und zeigt "
        "konkrete Möglichkeiten.",
        "Language makes racism and supports respectful communication.",
    )

    assert not find_english_text_spans(texts[0])
    assert find_english_text_spans(texts[1]) == ((38, 56),)
    assert find_english_text_spans(texts[2]) == ((0, len(texts[2])),)
