from __future__ import annotations

from typing import Any

from kai.tools.base import (
    Result,
    Tool,
    bool_schema,
    object_schema,
    optional_bool_arg,
    string_schema,
)
from kai.tools.colors import failure, file_name, success, tool_name, truncate


class EditTool(Tool):
    def name(self) -> str:
        return "edit"

    def description(self) -> str:
        return "Edit a file by replacing an exact string match with new content. The old_string must match exactly (including whitespace and indentation). Fails if old_string is not found or matches multiple times (unless replace_all is true)."

    def parameters(self) -> dict[str, Any]:
        return object_schema(
            ["file_path", "old_string", "new_string"],
            {
                "file_path": string_schema("Absolute path to the file to edit"),
                "old_string": string_schema("The exact string to find and replace"),
                "new_string": string_schema("The replacement string"),
                "replace_all": bool_schema("Replace all occurrences (default: false)"),
            },
        )

    def call(self, input: dict[str, Any]) -> Result:
        file_path = input.get("file_path")
        if not isinstance(file_path, str) or not file_path:
            return Result(
                output="Error editing file: missing required argument 'file_path'",
                is_error=True,
            )

        old_string = input.get("old_string")
        if not isinstance(old_string, str):
            return Result(
                output="Error editing file: missing required argument 'old_string'",
                is_error=True,
            )

        new_string = input.get("new_string")
        if not isinstance(new_string, str):
            return Result(
                output="Error editing file: missing required argument 'new_string'",
                is_error=True,
            )

        try:
            replace_all = optional_bool_arg(input, "replace_all", False)
        except ValueError as e:
            return Result(output=f"Error editing file: {e}", is_error=True)

        try:
            with open(file_path) as f:
                content = f.read()
        except Exception as e:
            return Result(output=f"Error editing file: {e}", is_error=True)

        if old_string == new_string:
            return Result(
                output="Error: old_string and new_string are identical", is_error=True
            )

        if old_string not in content:
            return Result(
                output=f"Error: old_string not found in {file_path}", is_error=True
            )

        count = content.count(old_string)
        if not replace_all and count > 1:
            return Result(
                output=f"Error: old_string matches multiple locations in {file_path}. "
                "Use replace_all or provide more context to make the match unique.",
                is_error=True,
            )

        new_content = content.replace(
            old_string, new_string, 1 if not replace_all else count
        )

        try:
            with open(file_path, "w") as f:
                f.write(new_content)
        except Exception as e:
            return Result(output=f"Error editing file: {e}", is_error=True)

        return Result(output=f"Successfully edited {file_path}")

    def render_tool_call(self, input: dict[str, Any]) -> str:
        file_path = input.get("file_path", "")
        old_string = input.get("old_string", "")
        new_string = input.get("new_string", "")
        return (
            f"{tool_name('edit')} {file_name(file_path)}\n"
            f"  {failure('- ' + truncate(old_string, 40))}\n"
            f"  {success('+ ' + truncate(new_string, 40))}"
        )

    def render_result(self, result: Result) -> str:
        if result.is_error:
            return failure(result.output)
        return success(result.output)
