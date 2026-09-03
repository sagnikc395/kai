from __future__ import annotations

import fnmatch
import os
import re
from typing import Any

from kai.tools.base import (
    Result,
    Tool,
    object_schema,
    optional_string_arg,
    string_schema,
)
from kai.tools.colors import failure, file_name, muted, tool_name
from kai.tools.format import truncate_lines


class GrepTool(Tool):
    def name(self) -> str:
        return "grep"

    def description(self) -> str:
        return "Search file contents using regex patterns. Returns matching lines with file paths and line numbers."

    def parameters(self) -> dict[str, Any]:
        return object_schema(
            ["pattern"],
            {
                "pattern": string_schema("The regex pattern to search for"),
                "path": string_schema(
                    "File or directory to search in (defaults to cwd)"
                ),
                "include": string_schema("Glob pattern to filter files (e.g. '*.ts')"),
            },
        )

    def call(self, input: dict[str, Any]) -> Result:
        pattern = input.get("pattern")
        if not isinstance(pattern, str) or not pattern:
            return Result(
                output="Error: missing required argument 'pattern'", is_error=True
            )

        search_path, _ = optional_string_arg(input, "path")
        if not search_path:
            search_path = "."

        include, include_specified = optional_string_arg(input, "include")

        try:
            expression = re.compile(pattern)
        except re.error as e:
            return Result(output=f"Error: {e}", is_error=True)

        try:
            matches = _grep_files(
                expression, search_path, include if include_specified else None
            )
        except Exception as e:
            return Result(output=f"Error: {e}", is_error=True)

        if not matches:
            return Result(output="No matches found.")
        return Result(output="\n".join(matches))

    def render_tool_call(self, input: dict[str, Any]) -> str:
        pattern = input.get("pattern", "")
        search_path, path_specified = optional_string_arg(input, "path")
        include, include_specified = optional_string_arg(input, "include")

        description = f"{tool_name('grep')} {muted('/')}{pattern}{muted('/')}"
        if path_specified and search_path:
            description += f" {muted('in')} {file_name(search_path)}"
        if include_specified and include:
            description += f" {muted(f'({include})')}"
        return description

    def render_result(self, result: Result) -> str:
        if result.is_error:
            return failure(result.output)
        return truncate_lines(result.output, 20, "more lines")


def _grep_files(
    expression: re.Pattern[str],
    search_path: str,
    include: str | None,
) -> list[str]:
    if os.path.isfile(search_path):
        files = [search_path]
    else:
        files = []
        for dirpath, _dirnames, filenames in os.walk(search_path):
            for filename in filenames:
                files.append(os.path.join(dirpath, filename))

    matches: list[str] = []
    for file_path in files:
        if include is not None and not fnmatch.fnmatch(
            os.path.basename(file_path), include
        ):
            continue
        file_matches = _grep_file(expression, file_path, 100 - len(matches))
        matches.extend(file_matches)
        if len(matches) >= 100:
            break

    return matches


def _grep_file(
    expression: re.Pattern[str],
    file_path: str,
    remaining: int,
) -> list[str]:
    if remaining <= 0:
        return []
    try:
        with open(file_path, errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return []

    matches: list[str] = []
    for line_number, line in enumerate(lines, 1):
        if not expression.search(line):
            continue
        display_line = line.rstrip("\n\r")
        if len(display_line) > 200:
            display_line = display_line[:200]
        matches.append(f"{file_path}:{line_number}:{display_line}")
        if len(matches) >= remaining:
            break
    return matches
