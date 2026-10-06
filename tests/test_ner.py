"""Tests für lokale NER-Markierungen möglicher Personennamen."""

# pylint: disable=duplicate-code
from tu_web_linguacheck import ner
from tu_web_linguacheck.models import Finding
from tu_web_linguacheck.ner import (
    find_person_entity_spans,
    mark_html_language_findings_with_person_hints,
)


def test_find_person_entity_spans_returns_complete_person_name() -> None:
    """Erkennt den vollständigen Namen statt nur des Sprachhinweis-Fragments."""
    text = "Saloua Mohammed ist Referentin für Rassismuskritik."

    assert find_person_entity_spans(text) == (
        (0, len("Saloua Mohammed"), "Saloua Mohammed"),
    )


def test_mark_html_language_findings_with_person_hints_keeps_finding() -> None:
    """Markiert einen Fund innerhalb eines vollständigen Personennamens additiv."""
    text = "Saloua Mohammed ist Referentin für Rassismuskritik."
    finding = Finding(
        url="https://example.org/",
        category="HTML_LANGUAGE",
        severity="warning",
        message="Englischer Ausdruck ist nicht ausgezeichnet.",
        offset=0,
        length=len("Saloua"),
        suggestions=('lang="en-US"',),
        context=text,
        profile="tu-de",
        source_rule_id="MISSING_ENGLISH_LANG",
    )

    marked_findings = mark_html_language_findings_with_person_hints([finding])

    assert len(marked_findings) == 1
    marked_finding = marked_findings[0]
    assert marked_finding.category == "HTML_LANGUAGE"
    assert marked_finding.source_rule_id == "MISSING_ENGLISH_LANG"
    assert marked_finding.offset == 0
    assert marked_finding.length == len("Saloua")
    assert marked_finding.ner_person_name == "Saloua Mohammed"


def test_mark_findings_marks_misspelling_within_person_entity(
    monkeypatch,
) -> None:
    """Markiert einen Rechtschreibfund innerhalb einer Person additiv."""
    text = "Saloua Mohammed ist Referentin."
    finding = Finding(
        url="https://example.org/",
        category="misspelling",
        severity="warning",
        message="Möglicher Rechtschreibfehler.",
        offset=0,
        length=len("Saloua"),
        suggestions=(),
        context=text,
        profile="tu-de",
        source_rule_id="GERMAN_SPELLER_RULE",
    )

    monkeypatch.setattr(
        ner,
        "find_person_entity_spans",
        lambda _text: ((0, len("Saloua Mohammed"), "Saloua Mohammed"),),
    )

    marked_findings = mark_html_language_findings_with_person_hints([finding])

    assert len(marked_findings) == 1
    marked_finding = marked_findings[0]
    assert marked_finding.category == "misspelling"
    assert marked_finding.source_rule_id == "GERMAN_SPELLER_RULE"
    assert marked_finding.offset == 0
    assert marked_finding.length == len("Saloua")
    assert marked_finding.ner_person_name == "Saloua Mohammed"


def test_mark_findings_does_not_mark_misspelling_outside_person_entity(
    monkeypatch,
) -> None:
    """Markiert keinen Rechtschreibfund außerhalb einer erkannten Person."""
    text = "Saloua Mohammed ist Referentin."
    finding = Finding(
        url="https://example.org/",
        category="misspelling",
        severity="warning",
        message="Möglicher Rechtschreibfehler.",
        offset=text.index("Referentin"),
        length=len("Referentin"),
        suggestions=(),
        context=text,
        profile="tu-de",
        source_rule_id="GERMAN_SPELLER_RULE",
    )

    monkeypatch.setattr(
        ner,
        "find_person_entity_spans",
        lambda _text: ((0, len("Saloua Mohammed"), "Saloua Mohammed"),),
    )

    marked_findings = mark_html_language_findings_with_person_hints([finding])

    assert len(marked_findings) == 1
    marked_finding = marked_findings[0]
    assert marked_finding.category == "misspelling"
    assert marked_finding.source_rule_id == "GERMAN_SPELLER_RULE"
    assert marked_finding.offset == text.index("Referentin")
    assert marked_finding.length == len("Referentin")
    assert marked_finding.ner_person_name is None


def test_mark_html_language_findings_keeps_false_person_hint_visible() -> None:
    """Behält auch einen fälschlich als Person markierten Sprachhinweis."""
    text = "Distract (Ablenken)"
    finding = Finding(
        url="https://example.org/",
        category="HTML_LANGUAGE",
        severity="warning",
        message="Englischer Ausdruck ist nicht ausgezeichnet.",
        offset=0,
        length=len("Distract"),
        suggestions=('lang="en-US"',),
        context=text,
        profile="tu-de",
        source_rule_id="MISSING_ENGLISH_LANG",
    )

    marked_findings = mark_html_language_findings_with_person_hints([finding])

    assert len(marked_findings) == 1
    marked_finding = marked_findings[0]
    assert marked_finding.category == "HTML_LANGUAGE"
    assert marked_finding.source_rule_id == "MISSING_ENGLISH_LANG"
    assert marked_finding.context == text
    assert marked_finding.offset == 0
    assert marked_finding.length == len("Distract")
    assert marked_finding.ner_person_name == "Distract"


def test_mark_html_language_findings_analyzes_shared_context_once(
    monkeypatch,
) -> None:
    """Analysiert denselben Seitenkontext nur einmal für mehrere Hinweise."""
    text = "Saloua Mohammed und Hanin Ghazalin sind Referentinnen."
    first_finding = Finding(
        url="https://example.org/",
        category="HTML_LANGUAGE",
        severity="warning",
        message="Englischer Ausdruck ist nicht ausgezeichnet.",
        offset=0,
        length=len("Saloua"),
        suggestions=('lang="en-US"',),
        context=text,
        profile="tu-de",
        source_rule_id="MISSING_ENGLISH_LANG",
    )
    second_finding = first_finding.model_copy(
        update={
            "offset": len("Saloua Mohammed und "),
            "length": len("Hanin"),
        }
    )
    analysis_calls = 0

    def fake_find_person_entity_spans(
        received_text: str,
    ) -> tuple[tuple[int, int, str], ...]:
        nonlocal analysis_calls
        analysis_calls += 1
        assert received_text == text
        return (
            (0, len("Saloua Mohammed"), "Saloua Mohammed"),
            (
                len("Saloua Mohammed und "),
                len("Saloua Mohammed und Hanin Ghazalin"),
                "Hanin Ghazalin",
            ),
        )

    monkeypatch.setattr(
        ner,
        "find_person_entity_spans",
        fake_find_person_entity_spans,
    )

    marked_findings = mark_html_language_findings_with_person_hints(
        [first_finding, second_finding]
    )

    assert analysis_calls == 1
    assert [finding.ner_person_name for finding in marked_findings] == [
        "Saloua Mohammed",
        "Hanin Ghazalin",
    ]


def test_get_person_ner_model_loads_model_only_once(monkeypatch) -> None:
    """Lädt das Modell verzögert und verwendet es danach aus dem Cache."""
    loaded_model = object()
    load_calls = 0

    def fake_load() -> object:
        nonlocal load_calls
        load_calls += 1
        return loaded_model

    monkeypatch.setattr(ner.de_core_news_lg, "load", fake_load)
    ner.get_person_ner_model.cache_clear()

    try:
        assert ner.get_person_ner_model() is loaded_model
        assert ner.get_person_ner_model() is loaded_model
        assert load_calls == 1
    finally:
        ner.get_person_ner_model.cache_clear()
