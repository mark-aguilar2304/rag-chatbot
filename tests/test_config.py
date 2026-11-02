from __future__ import annotations

import sys
from types import SimpleNamespace

from src import config


def test_value_reads_streamlit_secrets(monkeypatch) -> None:
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.setitem(sys.modules, "streamlit", SimpleNamespace(secrets={"LLM_MODEL": "secret-model"}))
    assert config._value("LLM_MODEL", "default-model") == "secret-model"


def test_environment_overrides_streamlit_secrets(monkeypatch) -> None:
    monkeypatch.setenv("LLM_MODEL", "env-model")
    monkeypatch.setitem(sys.modules, "streamlit", SimpleNamespace(secrets={"LLM_MODEL": "secret-model"}))
    assert config._value("LLM_MODEL", "default-model") == "env-model"
