"""Split blocks into overlapping, sentence-aware chunks with source metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .ingestion import Block

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    source: str
    page: int | None
    section: str | None
    index: int


def chunk_blocks(
    blocks: list[Block],
    source_name: str,
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
) -> list[Chunk]:
    """Pack sentences into chunks without crossing page or section boundaries."""
    if chunk_size < 100:
        raise ValueError("chunk_size must be at least 100 characters.")
    if not 0 <= chunk_overlap < chunk_size:
        raise ValueError("chunk_overlap must be >= 0 and smaller than chunk_size.")

    chunks: list[Chunk] = []
    seen: set[tuple[str, int | None, str | None]] = set()
    for block in blocks:
        units = _split_units(block.text, chunk_size)
        for text in _pack_units(units, chunk_size, chunk_overlap):
            identity = (text, block.page, block.section)
            if not text or identity in seen:
                continue
            seen.add(identity)
            chunks.append(
                Chunk(
                    id=f"chunk-{len(chunks):04d}",
                    text=text,
                    source=source_name,
                    page=block.page,
                    section=block.section,
                    index=len(chunks),
                )
            )
    return chunks


def _split_units(text: str, chunk_size: int) -> list[str]:
    units: list[str] = []
    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = " ".join(paragraph.split())
        if not paragraph:
            continue
        for sentence in _SENTENCE_RE.split(paragraph):
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(sentence) <= chunk_size:
                units.append(sentence)
            else:
                units.extend(_split_long_sentence(sentence, chunk_size))
    return units


def _split_long_sentence(sentence: str, chunk_size: int) -> list[str]:
    pieces: list[str] = []
    words: list[str] = []
    length = 0
    for word in sentence.split():
        extra = len(word) + (1 if words else 0)
        if words and length + extra > chunk_size:
            pieces.append(" ".join(words))
            words = []
            length = 0
        words.append(word)
        length += len(word) + (1 if len(words) > 1 else 0)
    if words:
        pieces.append(" ".join(words))
    return pieces


def _pack_units(units: list[str], chunk_size: int, chunk_overlap: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    length = 0

    for unit in units:
        if current and length + 1 + len(unit) > chunk_size:
            text = " ".join(current)
            chunks.append(text)

            # Carry a sentence or two forward for context, but never duplicate a
            # short chunk wholesale or overflow the next chunk.
            carry: list[str] = []
            carry_length = 0
            if chunk_overlap and len(text) > chunk_overlap * 2:
                for previous in reversed(current):
                    added = len(previous) + (1 if carry else 0)
                    if carry_length + added > chunk_overlap:
                        break
                    carry.insert(0, previous)
                    carry_length += added
            if carry and carry_length + 1 + len(unit) > chunk_size:
                carry = []
                carry_length = 0
            current = carry
            length = carry_length

        length += len(unit) + (1 if current else 0)
        current.append(unit)

    if current:
        chunks.append(" ".join(current))
    return [chunk.strip() for chunk in chunks if chunk.strip()]
