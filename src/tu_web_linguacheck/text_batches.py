"""Bündelung sichtbarer Textblöcke für lokale Sprachprüfungen."""

from tu_web_linguacheck.html_content import TextBlock


def batch_page_blocks(
    blocks: tuple[TextBlock, ...],
    language: str,
) -> list[tuple[str, str, int]]:
    """Bündelt aufeinanderfolgende Textblöcke mit derselben Prüfsprache."""
    batches: list[tuple[str, str, int]] = []
    batch_texts: list[str] = []
    batch_language = ""
    batch_offset = 0
    block_offset = 0
    configured_primary_language = language.split("-", maxsplit=1)[0]

    for block in blocks:
        block_language = (
            language
            if block.language is None
            or block.language.casefold() == configured_primary_language.casefold()
            else "en-US"
            if block.language.casefold() == "en"
            else block.language
        )
        if batch_texts and block_language != batch_language:
            batches.append(("\n".join(batch_texts), batch_language, batch_offset))
            batch_texts = []
        if not batch_texts:
            batch_language = block_language
            batch_offset = block_offset
        batch_texts.append(block.text)
        block_offset += len(block.text) + 1

    if batch_texts:
        batches.append(("\n".join(batch_texts), batch_language, batch_offset))

    return batches
