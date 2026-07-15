import argparse
import os
import sys

from dotenv import load_dotenv

from kai.__version__ import VERSION
from kai.api.client import create_client
from kai.tui.tui import run_tui


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kai",
        description="A Textual-powered coding assistant in your terminal.",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="llama-3.3-70b-versatile",
        help="model to use via Groq (default: llama-3.3-70b-versatile)",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="print version",
    )
    return parser


def main() -> None:
    load_dotenv()

    parser = build_parser()
    args, _ = parser.parse_known_args()

    if args.version:
        print(VERSION)
        return

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("ERROR: GROQ_API_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)

    client = create_client(api_key)
    run_tui(client, args.model)
