"""Tests für die Umwandlung von LanguageTool-Funden."""

# pylint: disable=duplicate-code
from tu_web_linguacheck.findings import (
    filter_ignored_terms,
    finding_from_languagetool_match,
)
from tu_web_linguacheck.languagetool import LanguageToolMatch
from tu_web_linguacheck.models import Finding


def test_creates_finding_from_languagetool_match() -> None:
    """Ein LanguageTool-Fund wird in das interne Ergebnisformat überführt."""
    match = LanguageToolMatch(
        message="Möglicher Rechtschreibfehler gefunden.",
        offset=4,
        length=4,
        rule_id="GERMAN_SPELLER_RULE",
        category="TYPOS",
        issue_type="misspelling",
        replacements=("ist",),
    )

    finding = finding_from_languagetool_match(
        match,
        url="https://example.org/startseite/",
        context="Das isst ein Test.",
        profile="generic-de",
    )

    assert finding.url == "https://example.org/startseite/"
    assert finding.category == "misspelling"
    assert finding.severity == "warning"
    assert finding.message == "Möglicher Rechtschreibfehler gefunden."
    assert finding.offset == 4
    assert finding.length == 4
    assert finding.suggestions == ("ist",)
    assert finding.context == "Das isst ein Test."
    assert finding.profile == "generic-de"
    assert finding.source_rule_id == "GERMAN_SPELLER_RULE"


def test_creates_finding_without_suggestions() -> None:
    """Ein LanguageTool-Hinweis ohne Vorschlag bleibt vorschlagslos."""
    match = LanguageToolMatch(
        message="Stilhinweis.",
        offset=0,
        length=3,
        rule_id="STYLE_HINT",
        category="STYLE",
        issue_type="style",
        replacements=(),
    )

    finding = finding_from_languagetool_match(
        match,
        url="https://example.org/startseite/",
        context="Foo.",
        profile="generic-de",
    )

    assert finding.category == "style"
    assert finding.suggestions == ()


def test_filters_findings_with_configured_ignored_terms() -> None:
    """Nur Funde mit exakt passenden ignorierten Begriffen werden gefiltert."""
    findings = [
        Finding(
            url="https://example.org/",
            category="misspelling",
            severity="warning",
            message="Möglicher Tippfehler gefunden.",
            offset=0,
            length=6,
            suggestions=(),
            context="TiMana ist ein Studio.",
            profile="generic-de",
            source_rule_id="GERMAN_SPELLER_RULE",
        ),
        Finding(
            url="https://example.org/",
            category="misspelling",
            severity="warning",
            message="Möglicher Tippfehler gefunden.",
            offset=0,
            length=7,
            suggestions=(),
            context="TiManaX ist kein ignorierter Begriff.",
            profile="generic-de",
            source_rule_id="GERMAN_SPELLER_RULE",
        ),
        Finding(
            url="https://example.org/",
            category="misspelling",
            severity="warning",
            message="Möglicher Tippfehler gefunden.",
            offset=0,
            length=8,
            suggestions=(),
            context="Samtosha ist ein Studio.",
            profile="generic-de",
            source_rule_id="GERMAN_SPELLER_RULE",
        ),
    ]

    filtered_findings = filter_ignored_terms(
        findings,
        ignored_terms=["timana", "Samtosha"],
    )

    assert len(filtered_findings) == 1
    assert filtered_findings[0].context == "TiManaX ist kein ignorierter Begriff."
