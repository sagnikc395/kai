from __future__ import annotations

import fnmatch
import os
import pathlib
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


class GlobTool(Tool):
    def name(self) -> str:
        return "glob"

    def description(self) -> str:
        return "Find files matching a glob pattern. Returns matching file paths sorted alphabetically. Useful for discovering files by name or extension."

    def parameters(self) -> dict[str, Any]:
        return object_schema(
            ["pattern"],
            {
                "pattern": string_schema("The glob pattern to match files against"),
                "path": string_schema("Directory to search in (defaults to cwd)"),
            },
        )

    def call(self, input: dict[str, Any]) -> Result:
        pattern = input.get("pattern")
        if not isinstance(pattern, str) or not pattern:
            return Result(
                output="Error: missing required argument 'pattern'", is_error=True
            )

        search_path, path_specified = optional_string_arg(input, "path")
        if not path_specified or not search_path:
            try:
                search_path = os.getcwd()
            except OSError as e:
                return Result(output=f"Error: {e}", is_error=True)

        try:
            files = expand_glob(pattern, search_path)
        except Exception as e:
            return Result(output=f"Error: {e}", is_error=True)

        files.sort()
        if not files:
            return Result(output="No files matched the pattern.")
        return Result(output="\n".join(files))

    def render_tool_call(self, input: dict[str, Any]) -> str:
        pattern = input.get("pattern", "")
        search_path, path_specified = optional_string_arg(input, "path")
        description = f"{tool_name('glob')} {file_name(pattern)}"
        if path_specified and search_path:
            description += muted(f" in {search_path}")
        return description

    def render_result(self, result: Result) -> str:
        if result.is_error:
            return failure(result.output)
        return truncate_lines(result.output, 20, "more files")


def expand_glob(pattern: str, search_path: str) -> list[str]:
    if "**" not in pattern:
        matched = fnmatch.filter(
            _walk_files(search_path),
            os.path.join(search_path, pattern)
            if not os.path.isabs(pattern)
            else pattern,
        )
        return _only_files(matched)

    root, abs_pattern = _glob_root(pattern, search_path)
    abs_root = os.path.abspath(root) if not os.path.isabs(root) else root

    matches: list[str] = []
    pattern_parts = _split_path(abs_pattern)
    for dirpath, _dirnames, filenames in os.walk(abs_root):
        for filename in filenames:
            candidate = os.path.join(dirpath, filename)
            candidate_parts = _split_path(candidate)
            if _match_parts(pattern_parts, candidate_parts):
                matches.append(os.path.abspath(candidate))
    return matches


def _walk_files(search_path: str) -> list[str]:
    files: list[str] = []
    for dirpath, _dirnames, filenames in os.walk(search_path):
        for filename in filenames:
            files.append(os.path.join(dirpath, filename))
    return files


def _only_files(paths: list[str]) -> list[str]:
    result: list[str] = []
    for item in paths:
        try:
            if os.path.isfile(item):
                result.append(os.path.abspath(item))
        except OSError:
            continue
    return result


def _glob_root(pattern: str, search_path: str) -> tuple[str, str]:
    if os.path.isabs(pattern):
        abs_pattern = pattern
    else:
        abs_pattern = os.path.join(search_path, pattern)
    abs_pattern = os.path.normpath(abs_pattern)
    parts = _split_path(abs_pattern)
    root_parts: list[str] = []
    for part in parts:
        if _has_glob_meta(part):
            break
        root_parts.append(part)
    if os.name == "nt" and len(root_parts) >= 1 and root_parts[0].endswith(":"):
        root = root_parts[0] + os.sep
        if len(root_parts) > 1:
            root = os.path.join(root, *root_parts[1:])
    else:
        root = (
            os.sep + os.path.join(*root_parts)
            if abs_pattern.startswith(os.sep)
            else os.path.join(*root_parts)
        )
        if not root:
            root = os.sep

    if not os.path.isdir(root):
        root = os.path.dirname(root)

    return root, abs_pattern


def _has_glob_meta(value: str) -> bool:
    return any(c in value for c in "*?[")


def _split_path(value: str) -> list[str]:
    parts = pathlib.PurePosixPath(value).parts
    if os.sep == "\\":
        parts = pathlib.PureWindowsPath(value).parts
    result = [p for p in parts if p not in ("/", "\\", "")]
    return result


def _match_parts(pattern_parts: list[str], candidate_parts: list[str]) -> bool:
    if not pattern_parts:
        return not candidate_parts
    if pattern_parts[0] == "**":
        if _match_parts(pattern_parts[1:], candidate_parts):
            return True
        for i in range(len(candidate_parts)):
            if _match_parts(pattern_parts[1:], candidate_parts[i + 1 :]):
                return True
        return False
    if not candidate_parts:
        return False
    if not fnmatch.fnmatch(candidate_parts[0], pattern_parts[0]):
        return False
    return _match_parts(pattern_parts[1:], candidate_parts[1:])
