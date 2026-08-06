#!/usr/bin/env python3
"""Entry point for running kai straight from a checkout: `python main.py`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kai.app import main  # noqa: E402

if __name__ == "__main__":
    main()