"""Command line interface for kai."""

from __future__ import annotations

import argparse
import os
import sys
from importlib.metadata import PackageNotFoundError, version

from dotenv import load_dotenv

from kai.api.client import create_backend
from kai.config import OllamaConfig
from kai.tui.tui import run_tui


def _version() -> str:
    try:
        return version("kai")
    except PackageNotFoundError:
        return "unknown"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kai",
        description=(
            "a coding assistant in your terminal, "
            "powered by open source models and ollama."
        ),
    )
    parser.add_argument(
        "-m",
        "--model",
        default=os.environ.get("KAI_MODEL", OllamaConfig.DEFAULT_MODEL),
        help=f"Ollama model to use (default: {OllamaConfig.DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("OLLAMA_HOST", OllamaConfig.DEFAULT_HOST),
        help=f"Ollama server URL (default: {OllamaConfig.DEFAULT_HOST})",
    )
    parser.add_argument(
        "--num-ctx",
        type=int,
        default=None,
        help="context window in tokens",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="sampling temperature",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {_version()}",
    )
    return parser


def main() -> None:
    load_dotenv()

    args = build_parser().parse_args()

    options: dict[str, object] = {}
    if args.num_ctx is not None:
        options["num_ctx"] = args.num_ctx
    if args.temperature is not None:
        options["temperature"] = args.temperature

    try:
        backend = create_backend(
            model=args.model,
            host=args.host,
            options=options,
        )
    except Exception as err:
        print(f"ERROR: {err}", file=sys.stderr)
        raise SystemExit(1) from err

    try:
        run_tui(backend)
    except KeyboardInterrupt:
        raise SystemExit(130) from None
