"""Document -> chunks -> embeddings -> persistent index."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .chunking import chunk_blocks
from .embeddings import Embedder
from .ingestion import DocumentError, load_document, sha256_file
from .vector_store import SCHEMA_VERSION, IndexStore


def build_index(
    document_path: str | Path,
    index_dir: str | Path,
    embedder: Embedder,
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
) -> IndexStore:
    document_path = Path(document_path)
    blocks = load_document(document_path)
    chunks = chunk_blocks(
        blocks,
        source_name=document_path.name,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    if not chunks:
        raise DocumentError(f"No usable text chunks were produced from {document_path.name}.")

    vectors = np.asarray(embedder.embed_documents([chunk.text for chunk in chunks]), dtype=np.float32)
    if vectors.ndim != 2 or vectors.shape[0] != len(chunks) or vectors.shape[1] == 0:
        raise RuntimeError("The embedding provider returned an unexpected vector shape.")
    if not np.isfinite(vectors).all():
        raise RuntimeError("The embedding provider returned invalid values.")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": {
            "path": str(document_path),
            "name": document_path.name,
            "sha256": sha256_file(document_path),
            "size": document_path.stat().st_size,
        },
        "embedding_model": embedder.model_name,
        "chunking": {"size": chunk_size, "overlap": chunk_overlap},
        "chunk_count": len(chunks),
        "dimension": int(vectors.shape[1]),
    }
    store = IndexStore(chunks=chunks, vectors=vectors, manifest=manifest)
    store.save(index_dir)
    return store
