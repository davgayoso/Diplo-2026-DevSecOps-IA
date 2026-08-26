from pathlib import Path

import pytest

from app.rag.chunking import _split_words, chunks_from_pdf


def test_split_words_applies_overlap() -> None:
    pieces = _split_words("one two three four five six", size=4, overlap=2)

    assert pieces == ["one two three four", "three four five six"]


def test_split_words_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError, match="overlap"):
        _split_words("one two", size=2, overlap=2)


def test_owasp_pdf_is_chunked_with_page_metadata() -> None:
    pdf_path = Path("data/documents/OWASP-GenAI-LLM-Top-10-2026-v1.0.pdf")
    chunks = chunks_from_pdf(pdf_path, size=220, overlap=40, start_page=5, end_page=107)

    assert len(chunks) == 175
    assert min(chunk.page for chunk in chunks) == 5
    assert max(chunk.page for chunk in chunks) == 107
    assert len({chunk.id for chunk in chunks}) == len(chunks)
    assert all(chunk.section != "References" for chunk in chunks)
    assert next(chunk for chunk in chunks if chunk.page == 10).section == (
        "LLM01:2026 Prompt Injection"
    )
