"""Lokale LanguageTool-Prüfung von Seiteninhalten."""

from collections.abc import Sequence

from tu_web_linguacheck.findings import (
    filter_ignored_terms,
    finding_from_languagetool_match,
)
from tu_web_linguacheck.html_content import TextBlock
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

    return findings, len(blocks)
