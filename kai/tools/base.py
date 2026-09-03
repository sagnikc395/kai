from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class Result:
    output: str
    is_error: bool = False


class Tool(ABC):
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def parameters(self) -> dict[str, Any]: ...

    @abstractmethod
    def call(self, input: dict[str, Any]) -> Result: ...

    @abstractmethod
    def render_tool_call(self, input: dict[str, Any]) -> str: ...

    @abstractmethod
    def render_result(self, result: Result) -> str: ...


def optional_string_arg(input: dict[str, Any], name: str) -> tuple[str | None, bool]:
    value = input.get(name)
    if value is None:
        return None, False
    if not isinstance(value, str):
        raise ValueError(f"argument {name!r} must be a string")
    return value, True


def optional_number_arg(input: dict[str, Any], name: str, fallback: int) -> int:
    value = input.get(name)
    if value is None:
        return fallback
    return int(value)


def optional_bool_arg(input: dict[str, Any], name: str, fallback: bool) -> bool:
    value = input.get(name)
    if value is None:
        return fallback
    if not isinstance(value, bool):
        raise ValueError(f"argument {name!r} must be a boolean")
    return value


def object_schema(required: list[str], properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def string_schema(description: str) -> dict[str, Any]:
    return {"type": "string", "description": description}


def number_schema(description: str) -> dict[str, Any]:
    return {"type": "number", "description": description}


def bool_schema(description: str) -> dict[str, Any]:
    return {"type": "boolean", "description": description}
