from kai.tools.colors import muted


def truncate_lines(output: str, max_lines: int, label: str) -> str:
    lines = output.split("\n")
    if len(lines) <= max_lines:
        return output
    return (
        "\n".join(lines[:max_lines])
        + "\n"
        + muted(f"... ({len(lines) - max_lines} {label})")
    )
