"""Umwandlung externer Prüfergebnisse in interne Sprachfunde."""

from tu_web_linguacheck.languagetool import LanguageToolMatch
from tu_web_linguacheck.models import Finding
from tu_web_linguacheck.terminology import TerminologyMatch


def finding_from_languagetool_match(
    match: LanguageToolMatch,
    *,
    url: str,
    context: str,
    profile: str,
) -> Finding:
    """Überführt einen LanguageTool-Fund in das interne Ergebnisformat."""
    return Finding(
        url=url,
        category=match.issue_type,
        severity="warning",
        message=match.message,
        offset=match.offset,
        length=match.length,
        suggestions=match.replacements,
        context=context,
        profile=profile,
        source_rule_id=match.rule_id,
    )


def filter_ignored_terms(
    findings: list[Finding],
    *,
    ignored_terms: list[str],
) -> list[Finding]:
    """Entfernt Funde mit exakt passenden lokal ignorierten Begriffen."""
    normalized_ignored_terms = {term.casefold() for term in ignored_terms}

    return [
        finding
        for finding in findings
        if finding.context[finding.offset : finding.offset + finding.length].casefold()
        not in normalized_ignored_terms
    ]


def finding_from_terminology_match(
    match: TerminologyMatch,
    *,
    url: str,
    context: str,
    profile: str,
) -> Finding:
    """Überführt einen Terminologietreffer in das interne Ergebnisformat."""
    preferred_english = match.preferred_english

    return Finding(
        url=url,
        category="terminology",
        severity="hint",
        message=f"Nicht bevorzugte TU-Terminologie. Bevorzugt: {preferred_english}.",
        offset=match.offset,
        length=match.length,
        suggestions=(preferred_english,),
        context=context,
        profile=profile,
        source_rule_id="TU_EN_TERMINOLOGY",
    )
