"""Tests für den lokalen LanguageTool-Client."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import URLError
from urllib.parse import parse_qs

import pytest

from tu_web_linguacheck.languagetool import (
    LanguageToolClient,
    LanguageToolUnavailableError,
)


class FakeResponse:
    """Minimale HTTP-Antwort für einen lokalen Unit-Test."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        """Liefert die JSON-Antwort als UTF-8-kodierte Bytes."""
        return json.dumps(self._payload).encode("utf-8")


def test_check_sends_text_and_language_to_local_server(
    monkeypatch: Any,
) -> None:
    """Der Client sendet Formulardaten und bildet LanguageTool-Funde ab."""
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, *, timeout: float) -> FakeResponse:
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["content_type"] = request.get_header("Content-type")
        captured["body"] = parse_qs(request.data.decode("utf-8"))
        captured["timeout"] = timeout

        return FakeResponse(
            {
                "matches": [
                    {
                        "message": "Möglicher Rechtschreibfehler gefunden.",
                        "offset": 4,
                        "length": 5,
                        "replacements": [
                            {"value": "ist"},
                        ],
                        "rule": {
                            "id": "GERMAN_SPELLER_RULE",
                            "issueType": "misspelling",
                            "category": {"id": "TYPOS"},
                        },
                    }
                ]
            }
        )

    monkeypatch.setattr(
        "tu_web_linguacheck.languagetool.urlopen",
        fake_urlopen,
    )

    client = LanguageToolClient()
    matches = client.check(
        text="Das istf ein Test.",
        language="de-DE",
    )

    assert captured == {
        "url": "http://127.0.0.1:8081/v2/check",
        "method": "POST",
        "content_type": "application/x-www-form-urlencoded",
        "body": {
            "text": ["Das istf ein Test."],
            "language": ["de-DE"],
        },
        "timeout": 10.0,
    }
    assert len(matches) == 1

    match = matches[0]
    assert match.message == "Möglicher Rechtschreibfehler gefunden."
    assert match.offset == 4
    assert match.length == 5
    assert match.rule_id == "GERMAN_SPELLER_RULE"
    assert match.category == "TYPOS"
    assert match.issue_type == "misspelling"
    assert match.replacements == ("ist",)


def test_check_maps_empty_replacements_to_empty_tuple(
    monkeypatch: Any,
) -> None:
    """Der Client bildet fehlende Ersetzungsvorschläge als leeres Tupel ab."""

    def fake_urlopen(*_args: Any, **_kwargs: Any) -> FakeResponse:
        return FakeResponse(
            {
                "matches": [
                    {
                        "message": "Stilhinweis.",
                        "offset": 0,
                        "length": 3,
                        "replacements": [],
                        "rule": {
                            "id": "STYLE_HINT",
                            "issueType": "style",
                            "category": {"id": "STYLE"},
                        },
                    }
                ]
            }
        )

    monkeypatch.setattr(
        "tu_web_linguacheck.languagetool.urlopen",
        fake_urlopen,
    )

    matches = LanguageToolClient().check(
        text="Foo.",
        language="de-DE",
    )

    assert len(matches) == 1
    assert matches[0].replacements == ()


def test_check_raises_clear_error_when_local_server_is_unavailable(
    monkeypatch: Any,
) -> None:
    """Der Client meldet einen nicht erreichbaren lokalen Dienst verständlich."""

    def fake_urlopen(*_args: Any, **_kwargs: Any) -> FakeResponse:
        raise URLError(ConnectionRefusedError("Connection refused"))

    monkeypatch.setattr(
        "tu_web_linguacheck.languagetool.urlopen",
        fake_urlopen,
    )

    with pytest.raises(
        LanguageToolUnavailableError,
        match=r"127\.0\.0\.1:8081",
    ):
        LanguageToolClient().check(
            text="Ein selbst erzeugter Test.",
            language="de-DE",
        )


def test_check_sends_disabled_rule_ids_to_local_server(monkeypatch: Any) -> None:
    """Der Client übergibt gezielt deaktivierte Regeln an LanguageTool."""
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, *, timeout: float) -> FakeResponse:
        captured["body"] = parse_qs(request.data.decode("utf-8"))
        captured["timeout"] = timeout

        return FakeResponse({"matches": []})

    monkeypatch.setattr(
        "tu_web_linguacheck.languagetool.urlopen",
        fake_urlopen,
    )

    matches = LanguageToolClient().check(
        text="Qi Gong für Alle",
        language="de-DE",
        disabled_rule_ids=[
            "DE_SIMPLE_REPLACE_QI_GONG",
            "ANOTHER_RULE",
        ],
    )

    assert matches == []
    assert captured == {
        "body": {
            "text": ["Qi Gong für Alle"],
            "language": ["de-DE"],
            "disabledRules": [
                "DE_SIMPLE_REPLACE_QI_GONG,ANOTHER_RULE",
            ],
        },
        "timeout": 10.0,
    }


def test_check_raises_clear_error_when_local_server_times_out(
    monkeypatch: Any,
) -> None:
    """Der Client meldet eine Zeitüberschreitung des lokalen Dienstes klar."""

    def fake_urlopen(*_args: Any, **_kwargs: Any) -> FakeResponse:
        raise TimeoutError("timed out")

    monkeypatch.setattr(
        "tu_web_linguacheck.languagetool.urlopen",
        fake_urlopen,
    )

    with pytest.raises(
        LanguageToolUnavailableError,
        match=r"127\.0\.0\.1:8081",
    ):
        LanguageToolClient().check(
            text="Ein selbst erzeugter Test.",
            language="de-DE",
        )
