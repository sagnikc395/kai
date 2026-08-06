# kai

A simple coding assistant in your terminal. Kai is a minimal, hackable CLI agent - a tiny Claude Code-style tool - that runs an LLM in a tool-use loop against your local filesystem and shell.

## Features

- Textual terminal UI with streaming responses, tool status, and transcript scrolling
- Talks to models available through Groq (defaults to `llama-3.3-70b-versatile`)
- Tool-use agent loop with a small but practical tool set:
  - `bash` - run shell commands
  - `read` - read files
  - `write` - create/overwrite files
  - `edit` - string-replace edits
  - `glob` - find files by pattern
  - `grep` - search file contents
- Python package installable via pip, or runnable straight from a checkout with `python main.py`

## Requirements

- Python 3.10 or newer
- A Groq API key

## Quick Start

```bash
git clone https://github.com/sagnikc395/kai
cd kai

uv sync                 # or: pip install groq python-dotenv textual

echo "GROQ_API_KEY=your_key_here" > .env
python main.py
```

`main.py` lives at the repo root and needs no install step - it puts the repo on
`sys.path` and hands off to `kai.app.main`. The key can also come from the
environment instead of `.env` (`export GROQ_API_KEY=...`).

## Usage

Run from source - no installation required:

```bash
python main.py
# or pick a different model
python main.py --model llama-3.1-8b-instant
```

If you installed the package, `kai` and `python -m kai` do the same thing.

CLI options:

- `-m, --model <model>` - Groq model id (default: `llama-3.3-70b-versatile`)
- `-V, --version` - print version
- `-h, --help` - show help

Inside the TUI:

- Type a message and press <kbd>Enter</kbd> to send.
- `exit`, `quit`, `/exit`, or `/quit` leaves the session.
- <kbd>Esc</kbd> or <kbd>Ctrl</kbd>+<kbd>C</kbd> quits.

## Development

```bash
uv sync                  # install dependencies
pip install -e .         # editable install (adds the `kai` command)
python -m pytest         # run the test suite
ruff check               # lint
ruff format              # format
```

## Building

```bash
pip install build
python -m build --outdir dist
pip install dist/kai-*.whl
```

The installed package adds the `kai` command to your PATH.

## Architecture

Kai is organized as a small layered Python application:

```text
main.py               # run-from-checkout entry point (python main.py)
kai/                  # Python package
  __main__.py         # python -m kai entry point
  __version__.py      # package version string (-V / --version)
  app.py              # CLI flag parsing, .env loading, Groq client creation, TUI launch
  api/
    client.py         # Groq API client wrapper
  core/
    conversation.py   # Conversation state management
    message_loop.py   # Agent loop with streaming and tool-call accumulation
    system_prompt.py  # Dynamic system prompt builder
    tool_executor.py  # Tool dispatch and result collection
  tools/
    base.py           # Tool ABC, Result type, argument helpers, JSON schema builders
    registry.py       # Tool registration, lookup, Definitions() for Groq API
    colors.py         # Rich markup color helpers (with NO_COLOR support)
    format.py         # truncateLines helper
    bash.py           # bash tool: runs shell commands
    read.py           # read tool: reads files with line numbers
    write.py          # write tool: creates/overwrites files
    edit.py           # edit tool: string-replace in files
    glob_.py          # glob tool: finds files by pattern (supports **)
    grep_.py          # grep tool: regex search in file contents
  tui/
    tui.py            # Textual TUI: streaming, transcript, keyboard handling
tests/                # pytest suite for the tools
docs/                 # design notes (V3.md)
```

Runtime flow:

1. `kai/app.py` loads `.env`, parses flags, validates `GROQ_API_KEY`, creates the Groq client, and starts the TUI.
2. `kai/tui/tui.py` owns the Textual event loop, transcript rendering, keyboard handling, and status updates.
3. User messages are appended to `core.Conversation`, then `core.run_message_loop` sends a streamed Groq chat completion request.
4. The model receives the generated system prompt plus the tool definitions from `tools.definitions()`.
5. Streaming deltas are forwarded to the TUI as tokens. Tool-call deltas are accumulated until the model requests tool execution.
6. `core.execute_tool_calls` resolves each requested tool by name, unmarshals JSON arguments, executes the local tool, and appends Groq `tool` messages back into the conversation.
7. The loop continues until the model returns a normal assistant response with no pending tool calls.

## API Surface

### CLI API

```text
kai [options]
```

Options:

- `-m, --model <model>` selects the Groq model id.
- `-V, --version` prints the application version.
- `-h, --help` prints usage.

Environment:

- `GROQ_API_KEY` is required.
- `.env` is loaded automatically when present.
- `NO_COLOR=1` disables Rich markup in tool result rendering.

### Model API

The model integration uses the `groq` Python SDK:

- `client.chat.completions.create(stream=True)` is used for streamed assistant output.
- Requests include a system message, accumulated conversation history, and function tool definitions.
- Tool calls are returned as streamed deltas and reconstructed by index before execution.
- Tool results are sent back as Groq `tool` role messages using the original `tool_call_id`.

### Tool API

Tools implement `tools.base.Tool`:

```python
class Tool(ABC):
    def name(self) -> str: ...
    def description(self) -> str: ...
    def parameters(self) -> dict: ...
    def call(self, input: dict) -> Result: ...
    def render_tool_call(self, input: dict) -> str: ...
    def render_result(self, result: Result) -> str: ...
```

Available tools:

| Tool | Required args | Optional args | Purpose |
| --- | --- | --- | --- |
| `bash` | `command` | `timeout` | Run a shell command with a millisecond timeout. |
| `read` | `file_path` | `offset`, `limit` | Read a file with line numbers. |
| `write` | `file_path`, `content` | | Create or overwrite a file, including parent directories. |
| `edit` | `file_path`, `old_string`, `new_string` | `replace_all` | Replace exact text in a file. |
| `glob` | `pattern` | `path` | Find files by glob pattern, including `**`. |
| `grep` | `pattern` | `path`, `include` | Search file contents with a regex. |

`tools.registry.definitions()` converts each tool's JSON-schema-like `parameters()` dict into Groq function definitions. New tools should be registered in `tools/registry.py` and added to `all()` to control the order presented to the model.

## License

See [LICENSE](./LICENSE).
