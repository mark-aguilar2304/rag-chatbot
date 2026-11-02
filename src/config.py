"""Application settings loaded from environment variables and .env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# .env values never override variables already set in the environment.
load_dotenv(PROJECT_ROOT / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    document_path: Path
    index_dir: Path
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    min_score: float
    llm_base_url: str
    llm_model: str
    llm_api_key: str
    llm_timeout: int


def _value(name: str, default: str) -> str:
    # Environment variables win. Streamlit Community Cloud exposes its secrets
    # through st.secrets rather than the process environment.
    raw = os.environ.get(name)
    if raw is None:
        try:
            import streamlit as st

            raw = st.secrets.get(name)
        except Exception:
            raw = None
    return (str(raw) if raw is not None else default).strip()


def _path(name: str, default: str) -> Path:
    path = Path(_value(name, default)).expanduser()
    return (path if path.is_absolute() else PROJECT_ROOT / path).resolve()


def load_settings() -> Settings:
    """Read settings and fail early with a readable message on bad values."""
    try:
        chunk_size = int(_value("CHUNK_SIZE", "1200"))
        chunk_overlap = int(_value("CHUNK_OVERLAP", "200"))
        top_k = int(_value("TOP_K", "4"))
        min_score = float(_value("MIN_SCORE", "0.0"))
        llm_timeout = int(_value("LLM_TIMEOUT", "120"))
    except ValueError as exc:
        raise ValueError(f"A numeric setting is invalid: {exc}") from exc

    if chunk_size < 100:
        raise ValueError("CHUNK_SIZE must be at least 100 characters.")
    if not 0 <= chunk_overlap < chunk_size:
        raise ValueError("CHUNK_OVERLAP must be >= 0 and smaller than CHUNK_SIZE.")
    if not 1 <= top_k <= 20:
        raise ValueError("TOP_K must be between 1 and 20.")
    if not -1.0 <= min_score <= 1.0:
        raise ValueError("MIN_SCORE must be between -1.0 and 1.0.")
    if llm_timeout < 1:
        raise ValueError("LLM_TIMEOUT must be at least 1 second.")

    llm_base_url = _value("LLM_BASE_URL", "http://localhost:11434/v1").rstrip("/")
    if not llm_base_url.startswith(("http://", "https://")):
        raise ValueError("LLM_BASE_URL must start with http:// or https://.")
    llm_model = _value("LLM_MODEL", "llama3.2")
    if not llm_model:
        raise ValueError("LLM_MODEL must not be empty.")
    embedding_model = _value("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    if not embedding_model:
        raise ValueError("EMBEDDING_MODEL must not be empty.")

    return Settings(
        document_path=_path("DOCUMENT_PATH", "data/student-handbook.pdf"),
        index_dir=_path("INDEX_DIR", "index"),
        embedding_model=embedding_model,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        top_k=top_k,
        min_score=min_score,
        llm_base_url=llm_base_url,
        llm_model=llm_model,
        llm_api_key=_value("LLM_API_KEY", ""),
        llm_timeout=llm_timeout,
    )
