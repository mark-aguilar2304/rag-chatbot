from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class FakeEmbedder:
    """Deterministic hashed bag-of-words vectors for offline tests."""

    model_name = "fake-embedding-v1"

    def __init__(self, dimension: int = 128) -> None:
        self.dimension = dimension

    def _vector(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimension, dtype=np.float32)
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            digest = hashlib.blake2s(token.encode("utf-8"), digest_size=4).digest()
            vector[int.from_bytes(digest, "big") % self.dimension] += 1.0
        norm = float(np.linalg.norm(vector))
        return vector / norm if norm else vector

    def embed_documents(self, texts) -> np.ndarray:
        return np.stack([self._vector(text) for text in texts])

    def embed_query(self, text: str) -> np.ndarray:
        return self._vector(text)


@pytest.fixture
def fake_embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
def sample_markdown(tmp_path: Path) -> Path:
    path = tmp_path / "handbook.md"
    path.write_text(
        "# Handbook\n\n"
        "## Eligibility\n\n"
        "Full-time employees become eligible after 90 calendar days. Contractors are not eligible.\n\n"
        "## Equipment\n\n"
        "The equipment stipend is $600 per calendar year. Submit receipts within 30 days.\n\n"
        "## Travel\n\n"
        "The hotel limit is $180 per night in Tier 1 cities.\n",
        encoding="utf-8",
    )
    return path
