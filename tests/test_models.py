"""Tests für das interne Modell eines Sprachfunds."""

import pytest
from pydantic import ValidationError

from tu_web_linguacheck.models import Finding


def test_finding_accepts_valid_data() -> None:
    """Ein vollständig beschriebener Sprachfund wird akzeptiert."""
    finding = Finding(
        url="https://example.org/startseite/",
        category="spelling",
        severity="error",
        message="Möglicher Rechtschreibfehler gefunden.",
        offset=4,
        length=4,
        suggestions=("ist",),
        context="Das isst ein Test.",
        profile="generic-de",
        source_rule_id="GERMAN_SPELLER_RULE",
    )

    assert finding.url == "https://example.org/startseite/"
    assert finding.severity == "error"
    assert finding.suggestions == ("ist",)
    assert finding.source_rule_id == "GERMAN_SPELLER_RULE"


def test_finding_accepts_empty_suggestions() -> None:
    """Ein Hinweis ohne Ersetzungsvorschlag wird akzeptiert."""
    finding = Finding(
        url="https://example.org/startseite/",
        category="style",
        severity="hint",
        message="Stilhinweis.",
        offset=0,
        length=3,
        suggestions=(),
        context="Foo.",
        profile="generic-de",
        source_rule_id="STYLE_HINT",
    )

    assert finding.suggestions == ()


@pytest.mark.parametrize(
    "url",
    [
        "file:///tmp/seite.html",
        "ftp://example.org/datei.txt",
        "mailto:info@example.org",
        "keine-url",
    ],
)
def test_finding_rejects_non_http_urls(url: str) -> None:
    """Ein Fund muss zu einer HTTP(S)-URL gehören."""
    with pytest.raises(ValidationError):
        Finding(
            url=url,
            category="spelling",
            severity="error",
            message="Testmeldung.",
            offset=0,
            length=1,
            suggestions=(),
            context="Text",
            profile="generic-de",
            source_rule_id="TEST_RULE",
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("offset", -1),
        ("length", 0),
    ],
)
def test_finding_rejects_invalid_text_positions(
    field_name: str,
    value: int,
) -> None:
    """Offset und Fundlänge müssen sinnvolle Textpositionen beschreiben."""
    values = {
        "url": "https://example.org/startseite/",
        "category": "grammar",
        "severity": "error",
        "message": "Testmeldung.",
        "offset": 0,
        "length": 1,
        "suggestions": (),
        "context": "Text",
        "profile": "generic-de",
        "source_rule_id": "TEST_RULE",
    }
    values[field_name] = value

    with pytest.raises(ValidationError):
        Finding(**values)


def test_finding_rejects_unknown_severity() -> None:
    """Nicht definierte Schweregrade werden abgelehnt."""
    with pytest.raises(ValidationError):
        Finding(
            url="https://example.org/startseite/",
            category="grammar",
            severity="critical",
            message="Testmeldung.",
            offset=0,
            length=1,
            suggestions=(),
            context="Text",
            profile="generic-de",
            source_rule_id="TEST_RULE",
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "category",
        "message",
        "context",
        "profile",
        "source_rule_id",
    ],
)
def test_finding_rejects_empty_required_text_fields(field_name: str) -> None:
    """Fachlich erforderliche Textfelder dürfen nicht leer sein."""
    values = {
        "url": "https://example.org/startseite/",
        "category": "grammar",
        "severity": "warning",
        "message": "Testmeldung.",
        "offset": 0,
        "length": 1,
        "suggestions": (),
        "context": "Text",
        "profile": "generic-de",
        "source_rule_id": "TEST_RULE",
    }
    values[field_name] = ""

    with pytest.raises(ValidationError):
        Finding(**values)
