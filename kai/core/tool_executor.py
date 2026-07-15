from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from kai.tools.base import Result
from kai.tools.registry import get


@dataclass
class ToolExecutionResult:
    tool_call: dict[str, Any] = field(default_factory=dict)
    result: Result = field(default_factory=lambda: Result("", False))
    call_summary: str = ""
    result_summary: str = ""


def execute_tool_calls(
    tool_calls: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[ToolExecutionResult]]:
    messages: list[dict[str, Any]] = []
    results: list[ToolExecutionResult] = []

    for tool_call in tool_calls:
        function_info = tool_call.get("function", {})
        tool_name = function_info.get("name", "")
        tool_impl = get(tool_name)

        result: Result
        call_summary: str
        result_summary: str

        if tool_impl is None:
            result = Result(
                output=f"Unknown tool: {tool_name}",
                is_error=True,
            )
            call_summary = f"Unknown tool: {tool_name}"
            result_summary = result.output
        else:
            try:
                parsed_args: dict[str, Any] = json.loads(
                    function_info.get("arguments", "{}")
                )
            except json.JSONDecodeError:
                result = Result(
                    output=f"Invalid JSON arguments: {function_info.get('arguments', '')}",
                    is_error=True,
                )
                call_summary = tool_impl.name() + " (invalid args)"
                result_summary = result.output
            else:
                call_summary = tool_impl.render_tool_call(parsed_args)
                result = tool_impl.call(parsed_args)
                result_summary = tool_impl.render_result(result)

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.get("id", ""),
                "content": result.output,
            }
        )
        results.append(
            ToolExecutionResult(
                tool_call=tool_call,
                result=result,
                call_summary=call_summary,
                result_summary=result_summary,
            )
        )

    return messages, results
