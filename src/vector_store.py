"""A small persistent vector index built on NumPy: vectors, chunks, manifest."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .chunking import Chunk
from .ingestion import sha256_file

SCHEMA_VERSION = 1
VECTORS_FILE = "vectors.npy"
CHUNKS_FILE = "chunks.json"
MANIFEST_FILE = "manifest.json"
BUILD_COMMAND = "python -m scripts.build_index"


class IndexNotFoundError(RuntimeError):
    """No usable index exists yet."""


class IndexFormatError(RuntimeError):
    """Index files exist but are incomplete or unreadable."""


class StaleIndexError(RuntimeError):
    """The index no longer matches the document or current configuration."""


@dataclass(frozen=True)
class SearchResult:
    chunk_id: str
    text: str
    source: str
    page: int | None
    section: str | None
    score: float

    def citation(self) -> str:
        location: list[str] = []
        if self.page is not None:
            location.append(f"page {self.page}")
        if self.section:
            location.append(f'section "{self.section}"')
        suffix = f" - {', '.join(location)}" if location else ""
        return f"{self.source}{suffix}"


@dataclass
class IndexStore:
    chunks: list[Chunk]
    vectors: np.ndarray
    manifest: dict[str, Any]

    @classmethod
    def load(cls, index_dir: str | Path) -> "IndexStore":
        index_dir = Path(index_dir)
        if not index_dir.is_dir():
            raise IndexNotFoundError(
                f"No index found at {index_dir}. Build it with: {BUILD_COMMAND}"
            )

        missing = [
            name
            for name in (VECTORS_FILE, CHUNKS_FILE, MANIFEST_FILE)
            if not (index_dir / name).is_file()
        ]
        if missing:
            raise IndexNotFoundError(
                f"The index at {index_dir} is incomplete (missing {', '.join(missing)}). "
                f"Rebuild it with: {BUILD_COMMAND}"
            )

        try:
            manifest = json.loads((index_dir / MANIFEST_FILE).read_text(encoding="utf-8"))
            raw_chunks = json.loads((index_dir / CHUNKS_FILE).read_text(encoding="utf-8"))
            vectors = np.load(index_dir / VECTORS_FILE, allow_pickle=False)
        except (OSError, ValueError, EOFError, json.JSONDecodeError) as exc:
            raise IndexFormatError(
                f"The index at {index_dir} is corrupted or unreadable. "
                f"Rebuild it with: {BUILD_COMMAND}"
            ) from exc

        if not isinstance(manifest, dict):
            raise IndexFormatError("The index manifest is invalid. Rebuild the index.")
        required = {"schema_version", "source", "embedding_model", "chunking", "chunk_count", "dimension"}
        if missing := required - set(manifest):
            raise IndexFormatError(
                f"The index manifest is missing {', '.join(sorted(missing))}. Rebuild the index."
            )
        if not isinstance(manifest["source"], dict) or not isinstance(manifest["chunking"], dict):
            raise IndexFormatError("The index manifest is invalid. Rebuild the index.")

        if not isinstance(raw_chunks, list) or not raw_chunks:
            raise IndexFormatError("The index contains no chunks. Rebuild the index.")
        try:
            chunks = [Chunk(**item) for item in raw_chunks]
        except (TypeError, ValueError) as exc:
            raise IndexFormatError("The stored chunks are invalid. Rebuild the index.") from exc

        if vectors.ndim != 2 or vectors.shape[0] != len(chunks) or vectors.shape[1] == 0:
            raise IndexFormatError(
                "The vectors do not match the stored chunks. Rebuild the index."
            )
        try:
            chunk_count = int(manifest["chunk_count"])
            dimension = int(manifest["dimension"])
            schema_version = int(manifest["schema_version"])
        except (TypeError, ValueError) as exc:
            raise IndexFormatError("The index manifest is invalid. Rebuild the index.") from exc
        if chunk_count != len(chunks):
            raise IndexFormatError("The index manifest does not match its chunks. Rebuild the index.")
        if dimension != vectors.shape[1]:
            raise IndexFormatError("The index manifest does not match its vectors. Rebuild the index.")
        if schema_version != SCHEMA_VERSION:
            raise StaleIndexError("The index format is outdated. Rebuild the index.")

        try:
            vectors = vectors.astype(np.float32)
        except (TypeError, ValueError) as exc:
            raise IndexFormatError("The stored vectors are invalid. Rebuild the index.") from exc
        if not np.isfinite(vectors).all():
            raise IndexFormatError("The stored vectors are invalid. Rebuild the index.")

        return cls(chunks, _normalize_rows(vectors), manifest)

    def ensure_compatible(
        self, embedding_model: str, chunk_size: int, chunk_overlap: int
    ) -> None:
        if int(self.manifest["schema_version"]) != SCHEMA_VERSION:
            raise StaleIndexError("The index format is outdated. Rebuild the index.")
        if self.manifest["embedding_model"] != embedding_model:
            raise StaleIndexError(
                "The index was built with a different embedding model "
                f"({self.manifest['embedding_model']}). Rebuild it with: {BUILD_COMMAND}"
            )
        chunking = self.manifest["chunking"]
        if not isinstance(chunking, dict):
            raise IndexFormatError("The index manifest is invalid. Rebuild the index.")
        if (
            int(chunking.get("size", -1)) != chunk_size
            or int(chunking.get("overlap", -1)) != chunk_overlap
        ):
            raise StaleIndexError(
                "The chunk settings changed since this index was built. "
                f"Rebuild it with: {BUILD_COMMAND}"
            )

    def validate_source(self, document_path: str | Path) -> None:
        document_path = Path(document_path)
        if not document_path.is_file():
            raise StaleIndexError(
                f"The reference document for this index is missing: {document_path}. "
                "Restore it or rebuild the index from another document."
            )
        expected = self.manifest["source"].get("sha256")
        if not expected:
            raise IndexFormatError("The index has no source fingerprint. Rebuild the index.")
        if sha256_file(document_path) != expected:
            raise StaleIndexError(
                "The reference document changed since the index was built. "
                f"Rebuild it with: {BUILD_COMMAND}"
            )

    def search(
        self, query_vector: np.ndarray, top_k: int = 4, min_score: float = 0.0
    ) -> list[SearchResult]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")
        query = np.asarray(query_vector, dtype=np.float32).reshape(-1)
        if query.shape[0] != self.vectors.shape[1]:
            raise ValueError(
                "Embedding dimension mismatch: the index and embedding model are incompatible. "
                "Rebuild the index."
            )
        norm = float(np.linalg.norm(query))
        if norm == 0:
            raise ValueError("The question produced an empty embedding.")
        if not np.isfinite(query).all():
            raise ValueError("The question produced an invalid embedding.")
        scores = self.vectors @ (query / norm)

        results: list[SearchResult] = []
        for position in np.argsort(-scores, kind="stable")[:top_k]:
            score = float(scores[position])
            if score < min_score:
                continue
            chunk = self.chunks[int(position)]
            results.append(
                SearchResult(
                    chunk_id=chunk.id,
                    text=chunk.text,
                    source=chunk.source,
                    page=chunk.page,
                    section=chunk.section,
                    score=score,
                )
            )
        return results

    def save(self, index_dir: str | Path) -> None:
        index_dir = Path(index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)
        vectors = _normalize_rows(np.asarray(self.vectors, dtype=np.float32))
        self.manifest["chunk_count"] = len(self.chunks)
        self.manifest["dimension"] = int(vectors.shape[1])

        vectors_tmp = index_dir / ".vectors.tmp.npy"
        chunks_tmp = index_dir / ".chunks.tmp.json"
        manifest_tmp = index_dir / ".manifest.tmp.json"
        np.save(vectors_tmp, vectors, allow_pickle=False)
        chunks_tmp.write_text(
            json.dumps([asdict(chunk) for chunk in self.chunks], ensure_ascii=False),
            encoding="utf-8",
        )
        manifest_tmp.write_text(
            json.dumps(self.manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # Manifest is written last: a half-written index is detected on load.
        os.replace(vectors_tmp, index_dir / VECTORS_FILE)
        os.replace(chunks_tmp, index_dir / CHUNKS_FILE)
        os.replace(manifest_tmp, index_dir / MANIFEST_FILE)


def _normalize_rows(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (vectors / norms).astype(np.float32)
