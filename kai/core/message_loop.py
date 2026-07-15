from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from groq import Groq

from kai.core.system_prompt import build_system_prompt
from kai.core.tool_executor import ToolExecutionResult, execute_tool_calls
from kai.tools.registry import definitions


@dataclass
class MessageLoopCallbacks:
    on_token: Callable[[str], None] | None = None
    on_tool_start: Callable[[list[dict[str, Any]]], None] | None = None
    on_tool_result: Callable[[list[ToolExecutionResult]], None] | None = None
    on_complete: Callable[[str], None] | None = None
    on_error: Callable[[Exception], None] | None = None


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
        assistant_text = ""
        accumulated: dict[int, _ToolCallAccumulator] = {}
        finish_reason: str | None = None

        request_messages = [system_message] + messages

        try:
            stream = client.chat.completions.create(
                model=model,
                messages=request_messages,
                tools=tool_defs,
                stream=True,
                stream_options={"include_usage": False},
            )
        except Exception as err:
            if callbacks.on_error:
                callbacks.on_error(err)
            return messages

        try:
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
        except Exception as err:
            if callbacks.on_error:
                callbacks.on_error(err)
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
