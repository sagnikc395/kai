from __future__ import annotations

import json
import uuid
from typing import Any, Iterator

from kai.api.base import StreamEvent

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5-coder:7b"


class OllamaUnavailableError(RuntimeError):
    """Raised when the local Ollama server can't be reached or lacks the model."""


def _tool_call_id() -> str:
    return f"call_{uuid.uuid4().hex[:16]}"


def _to_ollama_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert kai's OpenAI-shaped history into what Ollama's chat API accepts.

    Two shapes differ: Ollama wants tool-call arguments as an object rather
    than a JSON string, and it matches tool results by name/position instead
    of by `tool_call_id`.
    """
    converted: list[dict[str, Any]] = []
    # Ollama drops the id, so remember which tool each id belonged to in order
    # to label the corresponding result message.
    id_to_name: dict[str, str] = {}

    for message in messages:
        role = message.get("role")

        if role == "assistant" and message.get("tool_calls"):
            calls: list[dict[str, Any]] = []
            for call in message["tool_calls"]:
                function = call.get("function", {})
                raw_args = function.get("arguments", "{}")
                if isinstance(raw_args, str):
                    try:
                        args = json.loads(raw_args or "{}")
                    except json.JSONDecodeError:
                        args = {}
                else:
                    args = raw_args
                name = function.get("name", "")
                id_to_name[call.get("id", "")] = name
                calls.append({"function": {"name": name, "arguments": args}})
            converted.append(
                {
                    "role": "assistant",
                    "content": message.get("content") or "",
                    "tool_calls": calls,
                }
            )
            continue

        if role == "tool":
            entry: dict[str, Any] = {
                "role": "tool",
                "content": message.get("content", ""),
            }
            name = id_to_name.get(message.get("tool_call_id", ""))
            if name:
                entry["tool_name"] = name
            converted.append(entry)
            continue

        converted.append(
            {"role": role, "content": message.get("content") or ""},
        )

    return converted


class OllamaBackend:
    """Local inference through an Ollama server on this machine."""

    name = "ollama"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        host: str = DEFAULT_HOST,
        options: dict[str, Any] | None = None,
    ) -> None:
        try:
            from ollama import Client
        except ImportError as err:  # pragma: no cover - depends on install extras
            raise OllamaUnavailableError(
                "The 'ollama' package is required for local inference. "
                "Install it with: uv pip install 'ollama>=0.4,<1'"
            ) from err

        self.model = model
        self.host = host
        self.options = options or {}
        self._client = Client(host=host)

    def stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> Iterator[StreamEvent]:
        tool_calls: list[dict[str, Any]] = []
        finish_reason: str | None = None

        try:
            stream = self._client.chat(
                model=self.model,
                messages=_to_ollama_messages(messages),
                tools=tools,
                stream=True,
                options=self.options or None,
            )

            for chunk in stream:
                message = getattr(chunk, "message", None)
                if message is None:
                    continue

                if message.content:
                    yield StreamEvent(text=message.content)

                for call in message.tool_calls or []:
                    arguments = call.function.arguments
                    if not isinstance(arguments, str):
                        arguments = json.dumps(arguments)
                    tool_calls.append(
                        {
                            "id": _tool_call_id(),
                            "type": "function",
                            "function": {
                                "name": call.function.name,
                                "arguments": arguments,
                            },
                        }
                    )

                if getattr(chunk, "done", False):
                    finish_reason = getattr(chunk, "done_reason", None) or "stop"
        except Exception as err:
            raise self._explain(err) from err

        # Ollama reports "stop" even when it emitted tool calls; the message
        # loop keys off "tool_calls" to decide whether to keep going.
        if tool_calls:
            finish_reason = "tool_calls"

        yield StreamEvent(tool_calls=tool_calls, finish_reason=finish_reason or "stop")

    def _explain(self, err: Exception) -> Exception:
        status = getattr(err, "status_code", None)
        text = str(err).lower()

        if status == 404 or "not found" in text:
            return OllamaUnavailableError(
                f"Model '{self.model}' is not available in Ollama. "
                f"Pull it first: ollama pull {self.model}"
            )
        if isinstance(err, ConnectionError) or "connect" in text or "refused" in text:
            return OllamaUnavailableError(
                f"Could not reach the Ollama server at {self.host}. "
                "Start it with: ollama serve"
            )
        return err

    def is_retryable(self, err: Exception) -> bool:
        # A missing server or missing model won't fix itself between attempts.
        if isinstance(err, OllamaUnavailableError):
            return False
        status = getattr(err, "status_code", None)
        if isinstance(status, int) and status >= 500:
            return True
        return "timeout" in str(err).lower()
