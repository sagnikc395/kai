from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

from kai.api.base import Backend
from kai.core.system_prompt import build_system_prompt
from kai.core.tool_executor import ToolExecutionResult, execute_tool_calls
from kai.tools.registry import definitions
from kai.config import MessageConfig


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


def _run_completion(
    backend: Backend,
    request_messages: list[dict[str, Any]],
    tool_defs: list[dict[str, Any]],
    callbacks: MessageLoopCallbacks,
) -> tuple[str, list[dict[str, Any]], str | None]:
    assistant_text = ""
    tool_calls: list[dict[str, Any]] = []
    finish_reason: str | None = None

    for event in backend.stream(request_messages, tool_defs):
        if event.text:
            assistant_text += event.text
            if callbacks.on_token:
                callbacks.on_token(event.text)
        if event.tool_calls:
            tool_calls.extend(event.tool_calls)
        if event.finish_reason:
            finish_reason = event.finish_reason

    return assistant_text, tool_calls, finish_reason


def run_message_loop(
    backend: Backend,
    messages: list[dict[str, Any]],
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
        tool_calls: list[dict[str, Any]] = []
        finish_reason = None
        last_error: Exception | None = None

        for attempt in range(1, MessageConfig.MAX_ATTEMPTS + 1):
            assistant_text = ""
            tool_calls = []
            finish_reason = None
            try:
                assistant_text, tool_calls, finish_reason = _run_completion(
                    backend, request_messages, tool_defs, callbacks
                )
                last_error = None
                break
            except Exception as err:
                last_error = err
                if attempt == MessageConfig.MAX_ATTEMPTS or not backend.is_retryable(err):
                    break
                if callbacks.on_retry:
                    callbacks.on_retry(err, attempt, MessageConfig.MAX_ATTEMPTS)
                time.sleep(MessageConfig.RETRY_BASE_DELAY * (2 ** (attempt - 1)))

        if last_error is not None:
            if callbacks.on_error:
                callbacks.on_error(last_error)
            return messages

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
