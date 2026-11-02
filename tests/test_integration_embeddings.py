from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.config import PROJECT_ROOT, load_settings
from src.embeddings import FastEmbedder
from src.indexer import build_index
from src.retrieval import retrieve
from src.vector_store import IndexStore

pytestmark = pytest.mark.skipif(
    os.environ.get("RAG_RUN_INTEGRATION") != "1",
    reason="Set RAG_RUN_INTEGRATION=1 to run tests that download/use the real embedding model.",
)


def test_real_embeddings_retrieve_expected_sections(tmp_path: Path) -> None:
    settings = load_settings()
    eval_data = json.loads(
        (PROJECT_ROOT / "eval" / "questions.json").read_text(encoding="utf-8")
    )
    document = PROJECT_ROOT / eval_data["document"]
    embedder = FastEmbedder(settings.embedding_model)
    store = build_index(
        document,
        tmp_path / "index",
        embedder,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    loaded = IndexStore.load(tmp_path / "index")
    loaded.validate_source(document)

    hits = 0
    answerable = [item for item in eval_data["questions"] if item["answerable"]]
    for item in answerable:
        results = retrieve(item["question"], embedder, loaded, top_k=4)
        sections = {result.section for result in results}
        hits += int(bool(sections & set(item["expected_sections"])))

    assert hits / len(answerable) >= 0.75
    assert len(store.chunks) > 1
