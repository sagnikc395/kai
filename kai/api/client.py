from __future__ import annotations

from typing import Any

from kai.api.base import Backend
from kai.config import OllamaConfig


def create_backend(
    model: str | None = None,
    host: str = OllamaConfig.DEFAULT_HOST,
    options: dict[str, Any] | None = None,
) -> Backend:
    from kai.api.ollama_backend import OllamaBackend

    return OllamaBackend(
        model=model or OllamaConfig.DEFAULT_MODEL,
        host=host,
        options=options,
    )
