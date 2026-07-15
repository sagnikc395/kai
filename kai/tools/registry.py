from __future__ import annotations

from typing import Any

from kai.tools.base import Tool
from kai.tools.bash import BashTool
from kai.tools.edit import EditTool
from kai.tools.glob_ import GlobTool
from kai.tools.grep_ import GrepTool
from kai.tools.read import ReadTool
from kai.tools.write import WriteTool

_registry: dict[str, Tool] = {}


def _init() -> None:
    _register(BashTool())
    _register(ReadTool())
    _register(WriteTool())
    _register(EditTool())
    _register(GlobTool())
    _register(GrepTool())


def _register(tool: Tool) -> None:
    _registry[tool.name()] = tool


def get(name: str) -> Tool | None:
    return _registry.get(name)


def all_tools() -> list[Tool]:
    return [
        _registry["bash"],
        _registry["read"],
        _registry["write"],
        _registry["edit"],
        _registry["glob"],
        _registry["grep"],
    ]


def definitions() -> list[dict[str, Any]]:
    defs: list[dict[str, Any]] = []
    for tool in all_tools():
        defs.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name(),
                    "description": tool.description(),
                    "parameters": tool.parameters(),
                },
            }
        )
    return defs


_init()
