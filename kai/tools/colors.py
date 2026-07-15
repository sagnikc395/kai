import os

_NO_COLOR = os.environ.get("NO_COLOR") == "1"


def _markup(tag: str, text: str) -> str:
    if _NO_COLOR:
        return text
    return f"[{tag}]{text}[/]"


def muted(text: str) -> str:
    return _markup("dim", text)


def success(text: str) -> str:
    return _markup("green", text)


def failure(text: str) -> str:
    return _markup("red", text)


def tool_name(text: str) -> str:
    return _markup("bold orange3", text)


def file_name(text: str) -> str:
    return _markup("blue", text)


def truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len].strip() + "..."
