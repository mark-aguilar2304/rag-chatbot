"""Question embedding and top-k retrieval with source metadata."""

from __future__ import annotations

from .embeddings import Embedder
from .vector_store import IndexStore, SearchResult

MAX_QUESTION_CHARS = 2000


def validate_question(question: str) -> str:
    question = question.strip()
    if not question:
        raise ValueError("Enter a question about the document.")
    if len(question) > MAX_QUESTION_CHARS:
        raise ValueError(f"Questions are limited to {MAX_QUESTION_CHARS} characters.")
    return question


def retrieve(
    question: str,
    embedder: Embedder,
    store: IndexStore,
    top_k: int = 4,
    min_score: float = 0.0,
) -> list[SearchResult]:
    """Return the most similar chunks, each carrying its citation metadata."""
    question = validate_question(question)
    vector = embedder.embed_query(question)
    return store.search(vector, top_k=top_k, min_score=min_score)
