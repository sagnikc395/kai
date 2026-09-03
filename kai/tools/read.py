from __future__ import annotations

from typing import Any

from kai.tools.base import (
    Result,
    Tool,
    number_schema,
    object_schema,
    optional_number_arg,
    string_schema,
)
from kai.tools.colors import failure, file_name, muted, tool_name
from kai.tools.format import truncate_lines


class ReadTool(Tool):
    def name(self) -> str:
        return "read"

    def description(self) -> str:
        return "Read a file from the filesystem. Returns the file content with line numbers. Supports optional offset and limit for reading specific portions of large files."

    def parameters(self) -> dict[str, Any]:
        return object_schema(
            ["file_path"],
            {
                "file_path": string_schema("Absolute path to the file to read"),
                "offset": number_schema("Line number to start reading from (1-based)"),
                "limit": number_schema("Maximum number of lines to read"),
            },
        )

    def call(self, input: dict[str, Any]) -> Result:
        file_path = input.get("file_path")
        if not isinstance(file_path, str) or not file_path:
            return Result(
                output="Error reading file: missing required argument 'file_path'",
                is_error=True,
            )

        offset = optional_number_arg(input, "offset", 0)
        limit = optional_number_arg(input, "limit", 0)

        try:
            with open(file_path) as f:
                content = f.read()
        except Exception as e:
            return Result(output=f"Error reading file: {e}", is_error=True)

        lines = content.split("\n")
        start = min(offset - 1, len(lines)) if offset > 0 else 0
        end = start + limit if limit > 0 else None
        return Result(
            output="\n".join(
                f"{line_no:>6}\t{line}"
                for line_no, line in enumerate(lines[start:end], start + 1)
            )
        )

    def render_tool_call(self, input: dict[str, Any]) -> str:
        file_path = input.get("file_path", "")
        offset = optional_number_arg(input, "offset", 0)
        limit = optional_number_arg(input, "limit", 0)

        description = f"{tool_name('read')} {file_name(file_path)}"
        if offset > 0 or limit > 0:
            parts = []
            if offset > 0:
                parts.append(f"from line {offset}")
            if limit > 0:
                parts.append(f"limit {limit}")
            description += muted(f" ({', '.join(parts)})")
        return description

    def render_result(self, result: Result) -> str:
        if result.is_error:
            return failure(result.output)
        return truncate_lines(result.output, 20, "more lines")
