from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from groq import (
    APIConnectionError,
    APITimeoutError,
    Groq,
    RateLimitError,
)

from kai.core.system_prompt import build_system_prompt
from kai.core.tool_executor import ToolExecutionResult, execute_tool_calls
from kai.tools.registry import definitions


MAX_ATTEMPTS = 4
RETRY_BASE_DELAY = 0.5

# Groq rejects a generation when the model emits a malformed tool call (a name
# that isn't in request.tools, or unparseable call syntax). Smaller models do
# this intermittently, so the same request usually succeeds on a retry.
_RETRYABLE_MESSAGES = (
    "failed to call a function",
    "failed_generation",
    "tool call validation failed",
    "tool_use_failed",
)


@dataclass
class MessageLoopCallbacks:
    on_token: Callable[[str], None] | None = None
    on_tool_start: Callable[[list[dict[str, Any]]], None] | None = None
    on_tool_result: Callable[[list[ToolExecutionResult]], None] | None = None
    on_complete: Callable[[str], None] | None = None
    on_error: Callable[[Exception], None] | None = None
    # (error, attempt_number, max_attempts) — partial output from the failed
    # attempt is discarded, so the UI should drop anything already streamed.
    on_retry: Callable[[Exception, int, int], None] | None = None


def _is_retryable(err: Exception) -> bool:
    if isinstance(err, (APIConnectionError, APITimeoutError, RateLimitError)):
        return True
    status = getattr(err, "status_code", None)
    if isinstance(status, int) and status >= 500:
        return True
    text = str(err).lower()
    return any(marker in text for marker in _RETRYABLE_MESSAGES)


@dataclass
class _ToolCallAccumulator:
    id: str = ""
    name: str = ""
    arguments: str = ""


def _accumulate_tool_call_delta(
    acc: dict[int, _ToolCallAccumulator],
    delta: Any,
) -> None:
    idx = delta.index
    if idx is None:
        return
    existing = acc.get(idx)
    if existing is None:
        existing = _ToolCallAccumulator()
        acc[idx] = existing
    if delta.id:
        existing.id = delta.id
    if delta.function and delta.function.name:
        existing.name = delta.function.name
    if delta.function and delta.function.arguments:
        existing.arguments += delta.function.arguments


def _build_tool_calls(
    acc: dict[int, _ToolCallAccumulator],
) -> list[dict[str, Any]]:
    tool_calls: list[dict[str, Any]] = []
    for index in sorted(acc.keys()):
        a = acc[index]
        tool_calls.append(
            {
                "id": a.id,
                "type": "function",
                "function": {
                    "name": a.name,
                    "arguments": a.arguments,
                },
            }
        )
    return tool_calls


def _stream_completion(
    client: Groq,
    request_messages: list[dict[str, Any]],
    model: str,
    tool_defs: list[dict[str, Any]],
    callbacks: MessageLoopCallbacks,
) -> tuple[str, dict[int, _ToolCallAccumulator], str | None]:
    assistant_text = ""
    accumulated: dict[int, _ToolCallAccumulator] = {}
    finish_reason: str | None = None

    stream = client.chat.completions.create(
        model=model,
        messages=request_messages,
        tools=tool_defs,
        stream=True,
    )

    for chunk in stream:
        if chunk.choices is None or len(chunk.choices) == 0:
            continue
        choice = chunk.choices[0]
        delta = choice.delta

        if delta and delta.content:
            assistant_text += delta.content
            if callbacks.on_token:
                callbacks.on_token(delta.content)

        if delta and delta.tool_calls:
            for tool_call_delta in delta.tool_calls:
                _accumulate_tool_call_delta(accumulated, tool_call_delta)

        if choice.finish_reason:
            finish_reason = choice.finish_reason

    return assistant_text, accumulated, finish_reason


def run_message_loop(
    client: Groq,
    messages: list[dict[str, Any]],
    model: str,
    callbacks: MessageLoopCallbacks,
) -> list[dict[str, Any]]:
    system_message: dict[str, Any] = {
        "role": "system",
        "content": build_system_prompt(),
    }
    tool_defs = definitions()
    continue_loop = True

    while continue_loop:
        request_messages = [system_message] + messages

        assistant_text = ""
        accumulated: dict[int, _ToolCallAccumulator] = {}
        finish_reason = None
        last_error: Exception | None = None

        for attempt in range(1, MAX_ATTEMPTS + 1):
            assistant_text = ""
            accumulated = {}
            finish_reason = None
            try:
                assistant_text, accumulated, finish_reason = _stream_completion(
                    client, request_messages, model, tool_defs, callbacks
                )
                last_error = None
                break
            except Exception as err:
                last_error = err
                if attempt == MAX_ATTEMPTS or not _is_retryable(err):
                    break
                if callbacks.on_retry:
                    callbacks.on_retry(err, attempt, MAX_ATTEMPTS)
                time.sleep(RETRY_BASE_DELAY * (2 ** (attempt - 1)))

        if last_error is not None:
            if callbacks.on_error:
                callbacks.on_error(last_error)
            return messages

        tool_calls = _build_tool_calls(accumulated)

        if finish_reason == "tool_calls" or (
            tool_calls and finish_reason and finish_reason != "stop"
        ):
            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": assistant_text or None,
                "tool_calls": tool_calls,
            }
            messages.append(assistant_msg)

            if callbacks.on_tool_start:
                callbacks.on_tool_start(tool_calls)

            tool_messages, results = execute_tool_calls(tool_calls)
            messages.extend(tool_messages)

            if callbacks.on_tool_result:
                callbacks.on_tool_result(results)

            continue

        if assistant_text:
            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_text,
                }
            )

        if callbacks.on_complete:
            callbacks.on_complete(assistant_text)

        continue_loop = False

    return messages
