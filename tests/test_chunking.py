from __future__ import annotations

import pytest

from src.chunking import chunk_blocks
from src.ingestion import Block


def test_chunks_keep_metadata_and_respect_size() -> None:
    text = " ".join(f"Sentence {number} explains the policy in a little detail." for number in range(30))
    chunk_size = 300
    chunks = chunk_blocks(
        [Block(text, page=3, section="2. Eligibility")],
        source_name="policy.pdf",
        chunk_size=chunk_size,
        chunk_overlap=60,
    )
    assert len(chunks) > 1
    assert all(len(chunk.text) <= chunk_size for chunk in chunks)
    assert all(chunk.page == 3 for chunk in chunks)
    assert all(chunk.section == "2. Eligibility" for chunk in chunks)
    assert all(chunk.source == "policy.pdf" for chunk in chunks)
    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))
    assert len({chunk.id for chunk in chunks}) == len(chunks)


def test_consecutive_chunks_overlap() -> None:
    text = " ".join(f"Rule {number} is short and clear." for number in range(40))
    chunks = chunk_blocks([Block(text)], "rules.md", chunk_size=240, chunk_overlap=80)
    assert len(chunks) > 2
    first_words = set(chunks[0].text.split())
    second_words = set(chunks[1].text.split())
    assert len(first_words & second_words) >= 4


def test_chunks_do_not_cross_pages_or_sections() -> None:
    chunks = chunk_blocks(
        [
            Block("First page. " * 20, page=1, section="One"),
            Block("Second page. " * 20, page=2, section="Two"),
        ],
        source_name="doc.pdf",
        chunk_size=200,
        chunk_overlap=40,
    )
    assert {chunk.page for chunk in chunks} == {1, 2}
    assert all(
        (chunk.page == 1 and chunk.section == "One")
        or (chunk.page == 2 and chunk.section == "Two")
        for chunk in chunks
    )
    assert not any("First page." in chunk.text and "Second page." in chunk.text for chunk in chunks)


def test_very_long_sentence_is_split() -> None:
    text = " ".join(f"word{number}" for number in range(400))
    chunks = chunk_blocks([Block(text)], "long.txt", chunk_size=200, chunk_overlap=20)
    assert len(chunks) > 1
    assert all(len(chunk.text) <= 200 for chunk in chunks)


def test_short_chunks_are_not_duplicated() -> None:
    chunks = chunk_blocks(
        [Block("Tiny policy.", section="A"), Block("Tiny policy.", section="A")],
        source_name="doc.md",
        chunk_size=200,
        chunk_overlap=50,
    )
    assert len(chunks) == 1


def test_invalid_chunk_settings_raise() -> None:
    with pytest.raises(ValueError):
        chunk_blocks([Block("text")], "doc.txt", chunk_size=50)
    with pytest.raises(ValueError):
        chunk_blocks([Block("text")], "doc.txt", chunk_size=200, chunk_overlap=200)
    assert chunk_blocks([], "doc.txt") == []
