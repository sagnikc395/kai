# kai

A simple coding assistant in your terminal. Kai is a minimal, hackable CLI agent - a tiny Claude Code-style tool - that runs an LLM in a tool-use loop against your local filesystem and shell.

## Features

- Bubble Tea v2 terminal UI with streaming responses, tool status, and transcript scrolling
- Talks to models available through Groq (defaults to `llama-3.3-70b-versatile`)
- Tool-use agent loop with a small but practical tool set:
  - `bash` - run shell commands
  - `read` - read files
  - `write` - create/overwrite files
  - `edit` - string-replace edits
  - `glob` - find files by pattern
  - `grep` - search file contents
- Single-binary builds for Linux, macOS, and Windows via `go build`

## Requirements

- Go 1.26.3 or newer
- A Groq API key

## Setup

```bash
export GROQ_API_KEY=your_key_here
```

## Usage

Run from source:

```bash
go run ./cmd/kai
# or pick a different model
go run ./cmd/kai --model llama-3.1-8b-instant
```

CLI options:

- `-m, --model <model>` - Groq model id (default: `llama-3.3-70b-versatile`)
- `-V, --version` - print version
- `-h, --help` - show help

## Building a binary

```bash
go build -o dist/kai ./cmd/kai
```

The compiled binary is self-contained. Drop it on your `PATH` and run `kai`.

## Project layout

```
cmd/kai/            # binary entrypoint
internal/
  app/              # CLI flag parsing and app startup
  api/              # API client + types
  core/             # message loop, query, system prompt, tool executor
  tui/              # Bubble Tea v2 terminal UI
  tools/            # bash, read, write, edit, glob, grep
```

The agent loop lives in `internal/core/message_loop.go` and dispatches tool calls through `internal/core/tool_executor.go`. Tools expose JSON schemas from `internal/tools/registry.go`.

## License

See [LICENSE](./LICENSE).
