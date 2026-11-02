"""Build the persistent index: python -m scripts.build_index"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.config import load_settings
from src.embeddings import FastEmbedder
from src.indexer import build_index
from src.ingestion import DocumentError

# Windows consoles often default to cp1252; avoid crashing on non-ASCII paths/content.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the RAG index for one document.")
    parser.add_argument("--document", type=Path, help="Override DOCUMENT_PATH.")
    parser.add_argument("--index-dir", type=Path, help="Override INDEX_DIR.")
    args = parser.parse_args()

    settings = load_settings()
    document = (args.document or settings.document_path).resolve()
    index_dir = (args.index_dir or settings.index_dir).resolve()

    print(f"Document: {document}")
    print(f"Embedding model: {settings.embedding_model}")
    print("Building index (the first run downloads the embedding model)...")
    try:
        embedder = FastEmbedder(settings.embedding_model)
        store = build_index(
            document,
            index_dir,
            embedder,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
    except (DocumentError, ValueError, OSError) as exc:
        raise SystemExit(f"Error: {exc}") from exc

    print(f"Indexed {len(store.chunks)} chunks into {index_dir}")


if __name__ == "__main__":
    main()
