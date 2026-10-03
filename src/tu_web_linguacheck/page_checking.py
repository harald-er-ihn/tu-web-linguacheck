"""Lokale LanguageTool-Prüfung von Seiteninhalten."""

from collections.abc import Sequence
from unicodedata import combining

from tu_web_linguacheck.findings import (
    filter_ignored_terms,
    finding_from_languagetool_match,
)
from tu_web_linguacheck.html_content import TextBlock
from tu_web_linguacheck.language_detection import find_english_text_spans
from tu_web_linguacheck.languagetool import LanguageToolClient
from tu_web_linguacheck.models import Finding
from tu_web_linguacheck.text_batches import batch_page_blocks


def _check_text_findings(
    text: str,
    *,
    language: str,
    url: str,
    profile: str,
    disabled_rule_ids: Sequence[str] = (),
    ignored_terms: Sequence[str] = (),
) -> list[Finding]:
    """Prüft Text lokal und überführt Ergebnisse in interne Funde."""
    client = LanguageToolClient()

    if disabled_rule_ids:
        matches = client.check(
            text=text,
            language=language,
            disabled_rule_ids=disabled_rule_ids,
        )
    else:
        matches = client.check(text=text, language=language)

    findings = [
        finding_from_languagetool_match(
            match,
            url=url,
            context=text,
            profile=profile,
        )
        for match in matches
    ]

    return filter_ignored_terms(
        findings,
        ignored_terms=list(ignored_terms),
    )


def _check_page_text(
    text: str,
    *,
    language: str,
    url: str,
    profile: str,
    disabled_rule_ids: Sequence[str] = (),
    ignored_terms: Sequence[str] = (),
) -> tuple[list[Finding], int]:
    """Prüft nichtleere Textblöcke mit globalen Offsets und Seitenkontext."""
    findings: list[Finding] = []
    checked_blocks = 0
    block_offset = 0

    for line in text.splitlines(keepends=True):
        block = line.rstrip("\r\n")

        if block:
            checked_blocks += 1
            block_findings = _check_text_findings(
                block,
                language=language,
                url=url,
                profile=profile,
                disabled_rule_ids=disabled_rule_ids,
                ignored_terms=ignored_terms,
            )
            findings.extend(
                finding.model_copy(
                    update={
                        "context": text,
                        "offset": finding.offset + block_offset,
                    }
                )
                for finding in block_findings
            )

        block_offset += len(line)

    return findings, checked_blocks


def _is_german_or_unspecified_block(
    block: TextBlock,
    *,
    configured_language: str,
) -> bool:
    """Prüft, ob ein Block deutsch ist oder keine HTML-Sprache angibt."""
    configured_primary_language = configured_language.split("-", maxsplit=1)[0]
    return configured_primary_language.casefold() == "de" and (
        block.language is None
        or block.language.split("-", maxsplit=1)[0].casefold()
        == configured_primary_language.casefold()
    )


def _is_word_character(character: str) -> bool:
    """Prüft, ob ein Zeichen zu einem Wort gehört."""
    return bool(character) and (
        character.isalnum() or character == "_" or combining(character) != 0
    )


def _finding_is_misspelling_in_block(
    finding: Finding,
    *,
    block_offset: int,
    block_end: int,
) -> bool:
    """Prüft, ob ein Rechtschreibfund vollständig innerhalb eines Blocks liegt."""
    return (
        finding.category == "misspelling"
        and block_offset <= finding.offset
        and finding.offset + finding.length <= block_end
    )


def _has_word_boundaries(text: str, *, start: int, end: int) -> bool:
    """Prüft, ob vor und nach einem Bereich keine Wortzeichen stehen."""
    character_before = text[start - 1] if start > 0 else ""
    character_after = text[end] if end < len(text) else ""
    return not _is_word_character(character_before) and not _is_word_character(
        character_after
    )


def _is_within_english_text_span(
    *,
    start: int,
    end: int,
    english_text_spans: Sequence[tuple[int, int]],
) -> bool:
    """Prüft, ob ein Bereich vollständig in einer englischen Textspanne liegt."""
    return any(
        span_start <= start and end <= span_end
        for span_start, span_end in english_text_spans
    )


def _is_accepted_english_word_candidate(
    block: TextBlock,
    finding: Finding,
    *,
    block_offset: int,
    block_end: int,
    english_text_spans: Sequence[tuple[int, int]],
) -> bool:
    """Prüft, ob ein vollständiger Rechtschreibfund in einer englischen Spanne liegt."""
    if not _finding_is_misspelling_in_block(
        finding,
        block_offset=block_offset,
        block_end=block_end,
    ):
        return False

    candidate_start = finding.offset - block_offset
    candidate_end = candidate_start + finding.length
    candidate = block.text[candidate_start:candidate_end]
    return (
        len(candidate) >= 3
        and candidate.isalpha()
        and _has_word_boundaries(
            block.text,
            start=candidate_start,
            end=candidate_end,
        )
        and _is_within_english_text_span(
            start=candidate_start,
            end=candidate_end,
            english_text_spans=english_text_spans,
        )
    )


def _english_word_findings_for_block(
    block: TextBlock,
    *,
    block_offset: int,
    findings: Sequence[Finding],
) -> list[Finding]:
    """Findet vollständige Rechtschreibkandidaten in englischen Textspannen."""
    block_end = block_offset + len(block.text)
    english_text_spans = find_english_text_spans(block.text)
    return [
        finding
        for finding in findings
        if _is_accepted_english_word_candidate(
            block,
            finding,
            block_offset=block_offset,
            block_end=block_end,
            english_text_spans=english_text_spans,
        )
    ]


def _unmarked_english_findings_for_block(
    block: TextBlock,
    *,
    block_offset: int,
    findings: Sequence[Finding],
    url: str,
    profile: str,
) -> tuple[list[Finding], set[tuple[int, int]]]:
    """Ersetzt bestätigte englische Wortfolgen eines Blocks durch einen HTML-Hinweis."""
    english_word_findings = _english_word_findings_for_block(
        block,
        block_offset=block_offset,
        findings=findings,
    )
    grouped_findings: list[list[Finding]] = []

    for finding in english_word_findings:
        if not grouped_findings:
            grouped_findings.append([finding])
            continue

        previous_finding = grouped_findings[-1][-1]
        separator = block.text[
            previous_finding.offset
            + previous_finding.length
            - block_offset : finding.offset - block_offset
        ]
        if separator.isspace():
            grouped_findings[-1].append(finding)
        else:
            grouped_findings.append([finding])

    replacement_findings = [
        Finding(
            url=url,
            category="HTML_LANGUAGE",
            severity="warning",
            message=(
                'Englischer Ausdruck ist nicht mit lang="en" oder '
                'lang="en-US" ausgezeichnet.'
            ),
            offset=group[0].offset,
            length=group[-1].offset + group[-1].length - group[0].offset,
            suggestions=('lang="en-US"',),
            context=findings[0].context if findings else block.text,
            profile=profile,
            source_rule_id="MISSING_ENGLISH_LANG",
        )
        for group in grouped_findings
    ]
    replaced_finding_keys = {
        (finding.offset, finding.length) for finding in english_word_findings
    }
    return replacement_findings, replaced_finding_keys


def _replace_unmarked_english_word_findings(
    blocks: tuple[TextBlock, ...],
    findings: list[Finding],
    *,
    language: str,
    url: str,
    profile: str,
) -> list[Finding]:
    """Ersetzt englische Rechtschreibkandidaten ohne HTML-Sprache durch Hinweise."""
    replacement_findings: list[Finding] = []
    replaced_finding_keys: set[tuple[int, int]] = set()
    block_offset = 0

    for block in blocks:
        if _is_german_or_unspecified_block(
            block,
            configured_language=language,
        ):
            block_replacements, block_replaced_keys = (
                _unmarked_english_findings_for_block(
                    block,
                    block_offset=block_offset,
                    findings=findings,
                    url=url,
                    profile=profile,
                )
            )
            replacement_findings.extend(block_replacements)
            replaced_finding_keys.update(block_replaced_keys)

        block_offset += len(block.text) + 1

    remaining_findings = [
        finding
        for finding in findings
        if (finding.offset, finding.length) not in replaced_finding_keys
    ]
    return sorted(
        [*remaining_findings, *replacement_findings],
        key=lambda finding: finding.offset,
    )


def _check_page_blocks(
    blocks: tuple[TextBlock, ...],
    *,
    language: str,
    url: str,
    profile: str,
    disabled_rule_ids: Sequence[str] = (),
    ignored_terms: Sequence[str] = (),
) -> tuple[list[Finding], int]:
    """Prüft gleichsprachige Textblöcke gebündelt mit globalen Offsets."""
    findings: list[Finding] = []
    context = "\n".join(block.text for block in blocks)

    for batch_text, batch_language, batch_offset in batch_page_blocks(blocks, language):
        batch_findings = _check_text_findings(
            batch_text,
            language=batch_language,
            url=url,
            profile=profile,
            disabled_rule_ids=disabled_rule_ids,
            ignored_terms=ignored_terms,
        )
        findings.extend(
            finding.model_copy(
                update={"context": context, "offset": finding.offset + batch_offset}
            )
            for finding in batch_findings
        )

    findings = _replace_unmarked_english_word_findings(
        blocks,
        findings,
        language=language,
        url=url,
        profile=profile,
    )
    return findings, len(blocks)
