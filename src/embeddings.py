"""Replaceable embedding providers. The default runs locally through fastembed."""

from __future__ import annotations

from typing import Protocol, Sequence

import numpy as np


class Embedder(Protocol):
    model_name: str

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray: ...

    def embed_query(self, text: str) -> np.ndarray: ...


class FastEmbedder:
    """Local ONNX embeddings; the model is downloaded once and cached."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        from fastembed import TextEmbedding

        self.model_name = model_name
        self._model = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        vectors = np.asarray(list(self._model.passage_embed(list(texts))), dtype=np.float32)
        return _normalize(vectors)

    def embed_query(self, text: str) -> np.ndarray:
        vectors = np.asarray(list(self._model.query_embed(text)), dtype=np.float32)
        return _normalize(vectors)[0]


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=-1, keepdims=True)
    norms[norms == 0] = 1.0
    return (vectors / norms).astype(np.float32)
