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
- Optional: [Task](https://taskfile.dev/) for the `Taskfile.yml` workflows

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

Or with Task:

```bash
task run
task run -- --model llama-3.1-8b-instant
```

CLI options:

- `-m, --model <model>` - Groq model id (default: `llama-3.3-70b-versatile`)
- `-V, --version` - print version
- `-h, --help` - show help

## Development Tasks

The Taskfile uses a repo-local Go build cache at `.cache/go-build`, which keeps checks working in sandboxed or locked-down environments.

```bash
task          # run the default check task
task run      # run the TUI from source
task build    # build dist/kai for the current platform
task test     # run go test ./...
task vet      # run go vet ./...
task fmt      # gofmt cmd/ and internal/
task tidy     # go mod tidy
task release  # build release binaries for Linux, macOS, and Windows
task clean    # remove dist/ and local build cache
```

## Building

```bash
go build -o dist/kai ./cmd/kai
```

The compiled binary is self-contained. Drop it on your `PATH` and run `kai`.

## Architecture

Kai is organized as a small layered Go application:

```text
cmd/kai/            # binary entrypoint
internal/
  app/              # CLI flag parsing, .env loading, Groq client creation
  api/              # API client wrapper package
  core/             # conversation state, message loop, system prompt, tool executor
  tui/              # Bubble Tea v2 terminal UI and streaming event bridge
  tools/            # bash, read, write, edit, glob, grep tool implementations
```

Runtime flow:

1. `cmd/kai/main.go` calls `app.Run` with process IO and CLI args.
2. `internal/app` loads `.env`, parses flags, validates `GROQ_API_KEY`, creates the Groq client, and starts the TUI.
3. `internal/tui` owns the Bubble Tea event loop, transcript rendering, keyboard handling, and status updates.
4. User messages are appended to `core.Conversation`, then `core.RunMessageLoop` sends a streamed Groq chat completion request.
5. The model receives the generated system prompt plus the tool definitions from `tools.Definitions()`.
6. Streaming deltas are forwarded to the TUI as tokens. Tool-call deltas are accumulated until the model requests tool execution.
7. `core.ExecuteToolCalls` resolves each requested tool by name, unmarshals JSON arguments, executes the local tool, and appends Groq `tool` messages back into the conversation.
8. The loop continues until the model returns a normal assistant response with no pending tool calls.

## API Surface

Kai currently exposes a CLI API and an internal tool API.

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
- `NO_COLOR=1` disables ANSI color in tool result rendering.

### Model API

The model integration uses `github.com/conneroisu/groq-go`:

- `ChatCompletionStream` is used for streamed assistant output.
- Requests include a system message, accumulated conversation history, and function tool definitions.
- Tool calls are returned as streamed deltas and reconstructed by index before execution.
- Tool results are sent back as Groq `tool` role messages using the original `ToolCallID`.

### Tool API

Tools implement `internal/tools.Tool`:

```go
type Tool interface {
    Name() string
    Description() string
    Parameters() map[string]any
    Call(input map[string]any) Result
    RenderToolCall(input map[string]any) string
    RenderResult(result Result) string
}
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

`tools.Definitions()` converts each tool's JSON-schema-like `Parameters()` map into Groq function definitions. New tools should be registered in `internal/tools/registry.go` and added to `All()` to control the order presented to the model.

## License

See [LICENSE](./LICENSE).
