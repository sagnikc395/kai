# kai

A simple coding assistant in your terminal. Kai is a minimal, hackable CLI agent — a tiny Claude Code-style tool — that runs an LLM in a tool-use loop against your local filesystem and shell, with an Ink-based REPL UI.

## Features

- Interactive terminal UI built with [Ink](https://github.com/vadimdemedes/ink) + React
- Talks to any model available through [OpenRouter](https://openrouter.ai) (defaults to `anthropic/claude-sonnet-4`)
- Tool-use agent loop with a small but practical tool set:
  - `bash` — run shell commands
  - `read` — read files
  - `write` — create/overwrite files
  - `edit` — string-replace edits
  - `glob` — find files by pattern
  - `grep` — search file contents
- Single-binary builds for Linux, macOS, and Windows via `bun build --compile`

## Requirements

- [Bun](https://bun.sh) (runtime + bundler)
- An OpenRouter API key

## Setup

```bash
bun install
export OPENROUTER_API_KEY=your_key_here
```

## Usage

Run from source:

```bash
bun run start
# or pick a different model
bun run src/index.ts --model anthropic/claude-opus-4
```

CLI options:

- `-m, --model <model>` — OpenRouter model id (default: `anthropic/claude-sonnet-4`)
- `-V, --version` — print version
- `-h, --help` — show help

## Building a binary

```bash
bun run build         # local build into ./dist
bun run build:all     # cross-compile for linux/macos/windows (x64 + arm64)
```

The compiled binary is self-contained — drop it on your `PATH` and run `kai`.

## Project layout

```
src/
  index.ts          # CLI entry (commander)
  api/              # OpenRouter client + types
  core/             # message loop, query, system prompt, tool executor
  tools/            # bash, read, write, edit, glob, grep
  ui/               # Ink App + REPL + components
  utils/
build.ts            # bun --compile cross-target builds
```

The agent loop lives in `src/core/message_loop.ts` and dispatches tool calls through `src/core/tool_executor.ts`. Tools are defined with [zod](https://zod.dev) schemas in `src/tools/` and exposed to the model via `zod-to-json-schema`.

## License

See [LICENSE](./LICENSE).