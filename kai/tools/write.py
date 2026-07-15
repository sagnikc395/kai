from __future__ import annotations

import os
from typing import Any

from kai.tools.base import Result, Tool, object_schema, string_schema
from kai.tools.colors import failure, file_name, muted, success, tool_name


class WriteTool(Tool):
    def name(self) -> str:
        return "write"

    def description(self) -> str:
        return "Write content to a file. Creates the file and any parent directories if they don't exist. Overwrites existing files."

    def parameters(self) -> dict[str, Any]:
        return object_schema(
            ["file_path", "content"],
            {
                "file_path": string_schema("Absolute path to the file to write"),
                "content": string_schema("The content to write to the file"),
            },
        )

    def call(self, input: dict[str, Any]) -> Result:
        file_path = input.get("file_path")
        if not isinstance(file_path, str) or not file_path:
            return Result(
                output="Error writing file: missing required argument 'file_path'",
                is_error=True,
            )

        content = input.get("content")
        if not isinstance(content, str):
            return Result(
                output="Error writing file: missing required argument 'content'",
                is_error=True,
            )

        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as f:
                f.write(content)
        except Exception as e:
            return Result(output=f"Error writing file: {e}", is_error=True)

        lines = len(content.split("\n"))
        return Result(output=f"Successfully wrote {lines} lines to {file_path}")

    def render_tool_call(self, input: dict[str, Any]) -> str:
        file_path = input.get("file_path", "")
        content = input.get("content", "")
        lines = len(content.split("\n"))
        return (
            f"{tool_name('write')} {file_name(file_path)} {muted(f'({lines} lines)')}"
        )

    def render_result(self, result: Result) -> str:
        if result.is_error:
            return failure(result.output)
        return success(result.output)
