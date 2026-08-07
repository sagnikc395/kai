from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator, Protocol, runtime_checkable


@dataclass
class StreamEvent:
    """One normalized step of a completion, regardless of backend.

    Backends emit any number of `text`-only events while generating, then a
    single terminal event carrying `finish_reason` and, when the model called
    tools, the fully assembled `tool_calls` in OpenAI wire shape.
    """

    text: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    finish_reason: str | None = None


@runtime_checkable
class Backend(Protocol):
    """A source of streamed chat completions.

    The message loop only knows about this; whether tokens come from Groq's
    API or a locally loaded Unsloth model is the backend's business.
    """

    name: str
    model: str

    def stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> Iterator[StreamEvent]: ...

    def is_retryable(self, err: Exception) -> bool:
        """Whether re-issuing the identical request could plausibly succeed."""
        ...
