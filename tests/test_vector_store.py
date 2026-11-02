from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from src.indexer import build_index
from src.ingestion import DocumentError
from src.vector_store import (
    IndexFormatError,
    IndexNotFoundError,
    IndexStore,
    StaleIndexError,
)


def test_build_save_load_and_search(tmp_path: Path, fake_embedder, sample_markdown: Path) -> None:
    index_dir = tmp_path / "index"
    built = build_index(
        sample_markdown, index_dir, fake_embedder, chunk_size=300, chunk_overlap=50
    )
    assert built.vectors.shape[0] == len(built.chunks)
    assert (index_dir / "manifest.json").is_file()
    assert (index_dir / "vectors.npy").is_file()
    assert (index_dir / "chunks.json").is_file()

    store = IndexStore.load(index_dir)
    store.ensure_compatible(fake_embedder.model_name, 300, 50)
    store.validate_source(sample_markdown)

    results = store.search(fake_embedder.embed_query("equipment stipend"), top_k=3)
    assert results
    assert results[0].section == "Equipment"
    assert "$600" in results[0].text
    assert results[0].source == "handbook.md"
    assert results[0].page is None
    assert 0.0 <= results[0].score <= 1.0

    assert store.manifest["source"]["sha256"]
    assert store.manifest["chunk_count"] == len(store.chunks)


def test_missing_and_corrupt_indexes_raise(tmp_path: Path, fake_embedder, sample_markdown: Path) -> None:
    with pytest.raises(IndexNotFoundError):
        IndexStore.load(tmp_path / "missing")

    index_dir = tmp_path / "index"
    build_index(sample_markdown, index_dir, fake_embedder, chunk_size=300, chunk_overlap=50)
    (index_dir / "chunks.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(IndexFormatError):
        IndexStore.load(index_dir)


def test_vector_chunk_mismatch_is_rejected(tmp_path: Path, fake_embedder, sample_markdown: Path) -> None:
    index_dir = tmp_path / "index"
    build_index(sample_markdown, index_dir, fake_embedder, chunk_size=300, chunk_overlap=50)
    bad = np.zeros((2, 4), dtype=np.float32)
    np.save(index_dir / "vectors.npy", bad)
    with pytest.raises(IndexFormatError):
        IndexStore.load(index_dir)


def test_changed_document_is_detected(tmp_path: Path, fake_embedder, sample_markdown: Path) -> None:
    index_dir = tmp_path / "index"
    build_index(sample_markdown, index_dir, fake_embedder, chunk_size=300, chunk_overlap=50)
    store = IndexStore.load(index_dir)
    sample_markdown.write_text("# Changed\n\nNew content.", encoding="utf-8")
    with pytest.raises(StaleIndexError, match="changed"):
        store.validate_source(sample_markdown)

    sample_markdown.unlink()
    with pytest.raises(StaleIndexError, match="missing"):
        store.validate_source(sample_markdown)


def test_model_and_chunking_mismatch_are_detected(
    tmp_path: Path, fake_embedder, sample_markdown: Path
) -> None:
    index_dir = tmp_path / "index"
    build_index(sample_markdown, index_dir, fake_embedder, chunk_size=300, chunk_overlap=50)
    store = IndexStore.load(index_dir)

    with pytest.raises(StaleIndexError, match="embedding model"):
        store.ensure_compatible("different-model", 300, 50)
    with pytest.raises(StaleIndexError, match="chunk settings"):
        store.ensure_compatible(fake_embedder.model_name, 400, 50)


def test_empty_document_does_not_build(tmp_path: Path, fake_embedder) -> None:
    document = tmp_path / "empty.md"
    document.write_text("", encoding="utf-8")
    with pytest.raises(DocumentError):
        build_index(document, tmp_path / "index", fake_embedder)


def test_search_filters_by_score_and_validates_input(
    tmp_path: Path, fake_embedder, sample_markdown: Path
) -> None:
    store = build_index(
        sample_markdown, tmp_path / "index", fake_embedder, chunk_size=300, chunk_overlap=50
    )
    query = fake_embedder.embed_query("travel hotel")
    assert store.search(query, top_k=3, min_score=2.0) == []
    with pytest.raises(ValueError, match="top_k"):
        store.search(query, top_k=0)
    with pytest.raises(ValueError, match="dimension"):
        store.search(np.ones(3, dtype=np.float32))
