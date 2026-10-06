"""Lokale Markierung möglicher Personennamen mit spaCy."""

from functools import cache
from typing import Sequence

import de_core_news_lg

from tu_web_linguacheck.models import Finding


@cache
def get_person_ner_model():
    """Lädt das lokale Personenmodell erst bei tatsächlichem Bedarf."""
    return de_core_news_lg.load()


def find_person_entity_spans(text: str) -> tuple[tuple[int, int, str], ...]:
    """Gibt vollständige als PER erkannte Spannen zurück."""
    document = get_person_ner_model()(text)
    return tuple(
        (entity.start_char, entity.end_char, entity.text)
        for entity in document.ents
        if entity.label_ == "PER"
    )


def mark_html_language_findings_with_person_hints(
    findings: Sequence[Finding],
) -> list[Finding]:
    """Ergänzt passende Sprach- und Rechtschreibfunde innerhalb von Personen."""
    marked_findings: list[Finding] = []
    entity_spans_by_context: dict[str, tuple[tuple[int, int, str], ...]] = {}

    for finding in findings:
        if finding.category not in {"HTML_LANGUAGE", "misspelling"}:
            marked_findings.append(finding)
            continue

        entity_spans = entity_spans_by_context.get(finding.context)
        if entity_spans is None:
            entity_spans = find_person_entity_spans(finding.context)
            entity_spans_by_context[finding.context] = entity_spans

        finding_end = finding.offset + finding.length
        person_name = next(
            (
                entity_text
                for entity_start, entity_end, entity_text in entity_spans
                if entity_start <= finding.offset and finding_end <= entity_end
            ),
            None,
        )
        marked_findings.append(
            finding.model_copy(update={"ner_person_name": person_name})
        )

    return marked_findings
