# kai

A simple coding assistant in your terminal. Kai is a minimal, hackable CLI agent - a tiny Claude Code-style tool - that runs an LLM in a tool-use loop against your local filesystem and shell.

## Features

- Interactive terminal REPL
- Talks to any model available through [OpenRouter](https://openrouter.ai) (defaults to `anthropic/claude-sonnet-4`)
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
- An OpenRouter API key

## Setup

```bash
export OPENROUTER_API_KEY=your_key_here
```

## Usage

Run from source:

```bash
go run .
# or pick a different model
go run . --model anthropic/claude-opus-4
```

CLI options:

- `-m, --model <model>` - OpenRouter model id (default: `anthropic/claude-sonnet-4`)
- `-V, --version` - print version
- `-h, --help` - show help

## Building a binary

```bash
go build -o dist/kai .
```

The compiled binary is self-contained. Drop it on your `PATH` and run `kai`.

## Project layout

```
main.go             # CLI entry
internal/
  api/              # OpenRouter client + types
  core/             # message loop, query, system prompt, tool executor
  tools/            # bash, read, write, edit, glob, grep
  ui/               # terminal REPL
```

The agent loop lives in `internal/core/message_loop.go` and dispatches tool calls through `internal/core/tool_executor.go`. Tools expose JSON schemas from `internal/tools/registry.go`.

## License

See [LICENSE](./LICENSE).
