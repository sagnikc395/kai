# kai

Building a small agent from scratch using tool calling, with a production-ready CLI.

## Setup

- This project uses the Gemini Flash model by default (override with `--model`).
- Create your API key in Google GenAI Studio.
- Copy `.env.local` to `.env` and set `GEMINI_API_KEY`.

## Install (recommended)

```bash
uv pip install -e .
```

## CLI usage

```bash
# chat with the model
kai chat "summarize this repo"

# list files (relative to working dir)
kai --working-dir examples/calculator list-files .

# read a file
kai --working-dir examples/calculator read-file main.py

# write a file
kai --working-dir . write-file notes.txt --content "hello"

# run a python file with args
kai --working-dir examples/calculator run-python main.py --arg "3 + 5"
```

## Development

```bash
uv pip install -e .[dev]
pytest -q
```
