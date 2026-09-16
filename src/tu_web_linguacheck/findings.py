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
    preferred_term = match.preferred_term

    return Finding(
        url=url,
        category="terminology",
        severity="hint",
        message=f"Nicht bevorzugte TU-Terminologie. Bevorzugt: {preferred_term}.",
        offset=match.offset,
        length=match.length,
        suggestions=(preferred_term,),
        context=context,
        profile=profile,
        source_rule_id="TU_DE_INCLUSIVE_LANGUAGE"
        if profile == "tu-de"
        else "TU_EN_TERMINOLOGY",
    )


# pylint: disable=too-many-arguments
def finding_from_missing_english_translation(
    match: TerminologyMatch,
    *,
    occurrence_count: int,
    source_url: str,
    target_url: str,
    source_context: str,
    target_context: str | None,
    profile: str,
) -> Finding:
    """Überführt einen fehlenden englischen Zielbegriff in einen Übersetzungsfund."""
    return Finding(
        url=target_url,
        category="terminology",
        severity="hint",
        message=(
            "Die bevorzugte englische Übersetzung fehlt auf der englischen Zielseite."
        ),
        offset=match.offset,
        length=match.length,
        suggestions=(match.preferred_term,),
        context=source_context,
        profile=profile,
        source_rule_id="TU_EN_MISSING_TRANSLATION",
        source_url=source_url,
        source_term=match.matched_text,
        occurrence_count=occurrence_count,
        target_context=target_context,
    )
