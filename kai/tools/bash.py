from __future__ import annotations

import platform
import subprocess
from typing import Any

from kai.tools.base import (
    Result,
    Tool,
    number_schema,
    object_schema,
    optional_number_arg,
    string_schema,
)
from kai.tools.colors import failure, muted, tool_name


class BashTool(Tool):
    def name(self) -> str:
        return "bash"

    def description(self) -> str:
        return "Execute a bash command and return its output. Use for running shell commands, installing packages, running scripts, etc."

    def parameters(self) -> dict[str, Any]:
        return object_schema(
            ["command"],
            {
                "command": string_schema("The bash command to execute"),
                "timeout": number_schema("Timeout in milliseconds (default 30s)"),
            },
        )

    def call(self, input: dict[str, Any]) -> Result:
        command = input.get("command")
        if not isinstance(command, str) or not command:
            return Result(
                output="Error: missing required argument 'command'", is_error=True
            )

        timeout_ms = optional_number_arg(input, "timeout", 30000)
        timeout_sec = timeout_ms / 1000.0

        try:
            if platform.system().lower() == "windows":
                proc = subprocess.run(
                    ["cmd", "/C", command],
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                )
            else:
                proc = subprocess.run(
                    ["bash", "-lc", command],
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                )

            output = proc.stdout.strip()
            if proc.stderr.strip():
                if output:
                    output += "\n"
                output += proc.stderr.strip()
            if not output:
                output = "(no output)"

            is_error = proc.returncode != 0
            if is_error and output == "(no output)":
                output = f"Error: command exited with code {proc.returncode}"

            return Result(output=output, is_error=is_error)

        except subprocess.TimeoutExpired:
            return Result(output="Error: command timed out", is_error=True)
        except FileNotFoundError:
            shell = "cmd" if platform.system().lower() == "windows" else "bash"
            return Result(output=f"Error: {shell} not found in PATH", is_error=True)
        except Exception as e:
            return Result(output=f"Error: {e}", is_error=True)

    def render_tool_call(self, input: dict[str, Any]) -> str:
        command = input.get("command", "")
        return f"{tool_name('bash')} {muted('$')} {command}"

    def render_result(self, result: Result) -> str:
        if result.is_error:
            return failure(result.output)
        return result.output
