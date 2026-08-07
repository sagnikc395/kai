# kai

![kai](./docs/assets/Screenshot%202026-08-06%20at%206.56.45 PM.png)

A simple coding assistant in your terminal. Kai is a minimal, hackable CLI agent - a tiny Claude Code-style tool - that runs an LLM in a tool-use loop against your local filesystem and shell. Inference is fully local: everything runs through an Ollama server on your machine, with no API key and nothing leaving the box.

## Features

- Textual terminal UI with streaming responses, tool status, and transcript scrolling
- Fully local inference through [Ollama](https://ollama.com), defaulting to `qwen2.5-coder:7b`
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
- [Ollama](https://ollama.com) running locally, plus a tool-capable model

## Quick Start

```bash
git clone https://github.com/sagnikc395/kai
cd kai

uv sync                 # or: pip install ollama python-dotenv textual

ollama serve            # if it isn't already running
ollama pull qwen2.5-coder:7b
python main.py
```

Kai needs a model with tool support - `ollama show <model>` must list `tools`
under Capabilities. `qwen2.5-coder:7b` (the default), `qwen2:7b`, and
`llama3.1:8b` all qualify; plain `gemma` models do not.

`main.py` lives at the repo root and needs no install step - it puts the repo on
`sys.path` and hands off to `kai.app.main`.

## Usage

Run from source - no installation required:

```bash
python main.py
# or pick a different model
python main.py --model llama3.1:8b
# or point at an Ollama server elsewhere
python main.py --host http://192.168.1.10:11434
```

If you installed the package, `kai` and `python -m kai` do the same thing.

CLI options:

- `-m, --model <model>` - Ollama model id (default: `qwen2.5-coder:7b`)
- `--host <url>` - Ollama server URL (default: `http://localhost:11434`)
- `--num-ctx <n>` - context window in tokens
- `--temperature <f>` - sampling temperature
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
  app.py              # CLI flag parsing, .env loading, backend construction, TUI launch
  api/
    base.py           # Backend protocol + StreamEvent, the backend-neutral contract
    client.py         # Backend factory and defaults
    ollama_backend.py # Local Ollama streaming + message-shape translation
  core/
    conversation.py   # Conversation state management
    message_loop.py   # Agent loop with streaming and tool-call accumulation
    system_prompt.py  # Dynamic system prompt builder
    tool_executor.py  # Tool dispatch and result collection
  tools/
    base.py           # Tool ABC, Result type, argument helpers, JSON schema builders
    registry.py       # Tool registration, lookup, definitions() in OpenAI tool schema
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

1. `kai/app.py` loads `.env`, parses flags, builds the Ollama backend, and starts the TUI.
2. `kai/tui/tui.py` owns the Textual event loop, transcript rendering, keyboard handling, and status updates.
3. User messages are appended to `core.Conversation`, then `core.run_message_loop` asks the backend to stream a completion. The loop only sees `StreamEvent`s, so swapping in another backend touches nothing above `api/`.
4. The model receives the generated system prompt plus the tool definitions from `tools.definitions()`.
5. Text events are forwarded to the TUI as tokens; the backend assembles tool calls and emits them on the terminal event.
6. `core.execute_tool_calls` resolves each requested tool by name, unmarshals JSON arguments, executes the local tool, and appends `tool` messages back into the conversation.
7. The loop continues until the model returns a normal assistant response with no pending tool calls.

## API Surface

### CLI API

```text
kai [options]
```

Options:

- `-m, --model <model>` selects the Ollama model id.
- `--host`, `--num-ctx`, `--temperature` tune the Ollama backend.
- `-V, --version` prints the application version.
- `-h, --help` prints usage.

Environment:

- `KAI_MODEL` sets the default model; `OLLAMA_HOST` sets the default server URL.
- `.env` is loaded automatically when present.
- `NO_COLOR=1` disables Rich markup in tool result rendering.

### Model API

`api.base.Backend` is the only thing the agent loop knows about, so a different
provider is a new module under `api/` and nothing else:

```python
class Backend(Protocol):
    name: str
    model: str
    def stream(self, messages, tools) -> Iterator[StreamEvent]: ...
    def is_retryable(self, err: Exception) -> bool: ...
```

A backend emits `StreamEvent(text=...)` while generating, then one terminal
event carrying `finish_reason` and any fully assembled `tool_calls` in OpenAI
wire shape. Retry policy is per backend, since what is worth re-sending differs.

- `OllamaBackend` uses the `ollama` SDK's `chat(stream=True)`. Ollama returns
  structured tool calls rather than raw text, so no parsing is required, but the
  message history is translated on the way out: argument strings become objects,
  `content: None` becomes `""`, and `tool` results are labelled with `tool_name`
  because Ollama has no `tool_call_id`. A missing server or unpulled model
  raises `OllamaUnavailableError` with the command that fixes it, and is not
  retried.

Conversation history is stored in OpenAI shape and translated on the way out, so
a transcript stays portable across backends.

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

`tools.registry.definitions()` converts each tool's JSON-schema-like `parameters()` dict into OpenAI-style function definitions, which Ollama accepts directly. New tools should be registered in `tools/registry.py` and added to `all()` to control the order presented to the model.

## License

See [LICENSE](./LICENSE).
