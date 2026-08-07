from __future__ import annotations

from typing import Any

from kai.api.base import Backend
from kai.api.ollama_backend import DEFAULT_HOST, DEFAULT_MODEL


def create_backend(
    model: str | None = None,
    host: str = DEFAULT_HOST,
    options: dict[str, Any] | None = None,
) -> Backend:
    from kai.api.ollama_backend import OllamaBackend

    return OllamaBackend(model=model or DEFAULT_MODEL, host=host, options=options)
