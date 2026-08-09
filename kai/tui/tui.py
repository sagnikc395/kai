from __future__ import annotations

import threading
from typing import Any

from rich.markup import escape
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.events import Key
from textual.widgets import Header, Input, Static

from kai.api.base import Backend
from kai.core.conversation import Conversation
from kai.core.message_loop import MessageLoopCallbacks
from kai.core.tool_executor import ToolExecutionResult


class KaiApp(App[None]):
    TITLE = "kai (海)"
    SUB_TITLE = "a coding assistant in your terminal"
    CSS = """
    Screen {
        layout: vertical;
    }
    #transcript {
        height: 1fr;
        overflow-y: scroll;
        overflow-x: auto;
        margin: 0 1;
    }
    #transcript > Static {
        width: 100%;
    }
    #input-container {
        dock: bottom;
        height: 3;
        padding: 0 1;
    }
    #status-bar {
        dock: bottom;
        height: 1;
        padding: 0 1;
    }
    """

    BINDINGS = [
        ("escape", "quit", ""),
        ("ctrl+c", "quit", ""),
    ]

    def __init__(self, backend: Backend) -> None:
        super().__init__()
        self.backend = backend
        self.model_name = backend.model
        self.conversation = Conversation(backend)
        self.busy = False
        self.current_assistant: Static | None = None
        self.current_assistant_text = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield VerticalScroll(id="transcript")
        yield Static(
            f"[dim]Ready — {self.backend.name}:{self.model_name}[/]", id="status-bar"
        )
        yield Static(
            "[bold cyan]kai (海)[/] — coding assistant ready\n"
            "[dim]Model: qwen2.5-coder:7b · type a message and press Enter[/]",
            id="welcome",
        )
        yield Input(id="input", placeholder="Type a message...")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self.busy:
            return
        message = event.value.strip()
        if not message:
            return
        if message.lower() in ("exit", "quit", "/exit", "/quit"):
            self.exit()
            return

        self.query_one(Input).value = ""
        self.add_entry("user", message)
        self.busy = True
        self._update_status("Thinking")

        thread = threading.Thread(
            target=self._run_assistant, args=(message,), daemon=True
        )
        thread.start()

    def _run_assistant(self, message: str) -> None:
        callbacks = MessageLoopCallbacks(
            on_token=lambda token: self.call_from_thread(self._on_token, token),
            on_tool_start=lambda tc: self.call_from_thread(self._on_tool_start, tc),
            on_tool_result=lambda r: self.call_from_thread(self._on_tool_result, r),
            on_complete=lambda t: self.call_from_thread(self._on_complete, t),
            on_error=lambda e: self.call_from_thread(self._on_error, e),
            on_retry=lambda e, n, total: self.call_from_thread(
                self._on_retry, e, n, total
            ),
        )
        self.conversation.send(message, callbacks)

    def _on_token(self, token: str) -> None:
        self._update_status("Streaming")
        if self.current_assistant is None:
            transcript = self.query_one("#transcript")
            self.current_assistant = Static("", markup=True)
            self.current_assistant_text = ""
            transcript.mount(self.current_assistant)
            transcript.scroll_end(animate=False)
        self.current_assistant_text += token
        self.current_assistant.update(self.current_assistant_text)

    def _on_tool_start(self, tool_calls: list[dict[str, Any]]) -> None:
        self.current_assistant = None
        self.add_entry("tool", f"Executing {len(tool_calls)} tool call(s)...")
        self._update_status("Running tools")

    def _on_tool_result(self, results: list[ToolExecutionResult]) -> None:
        text = _render_tool_results(results)
        self.add_entry("tool", text)
        self._update_status("Tools complete")

    def _on_complete(self, text: str) -> None:
        self.busy = False
        self.current_assistant = None
        self._update_status("Ready")

    def _on_retry(self, err: Exception, attempt: int, total: int) -> None:
        # The failed attempt's partial output is discarded upstream, so drop the
        # widget holding it instead of letting the retry append to it.
        if self.current_assistant is not None:
            self.current_assistant.remove()
            self.current_assistant = None
            self.current_assistant_text = ""
        self._update_status(f"Retrying ({attempt}/{total - 1})")

    def _on_error(self, err: Exception) -> None:
        self.busy = False
        self.current_assistant = None
        self.add_entry("error", str(err))
        self._update_status("Error")

    def add_entry(self, role: str, content: str) -> None:
        transcript = self.query_one("#transcript")
        prefix_map = {
            "user": "[bold blue]you[/]",
            "assistant": "[bold magenta]kai (海)[/]",
            "tool": "[bold orange3]tool[/]",
            "error": "[bold red]error[/]",
        }
        prefix = prefix_map.get(role, "")
        if role in ("user", "assistant"):
            content = escape(content)
        entry = Static(f"{prefix} {content}", markup=True)
        transcript.mount(entry)
        transcript.scroll_end(animate=False)

    def _update_status(self, status: str) -> None:
        try:
            self.query_one("#status-bar").update(
                f"[dim]{status} — {self.backend.name}:{self.model_name}[/]"
            )
        except Exception:
            pass

    def action_quit(self) -> None:
        self.exit()


def _render_tool_results(results: list[ToolExecutionResult]) -> str:
    blocks: list[str] = []
    for r in results:
        status = "done"
        if r.result.is_error:
            status = "error"
        lines = [f"+ {r.call_summary}"]
        for line in r.result_summary.split("\n"):
            lines.append(f"| {line}")
        lines.append(f"+ {status}")
        blocks.append("\n".join(lines))
    return "\n".join(blocks)


def run_tui(backend: Backend) -> None:
    app = KaiApp(backend)
    app.run()
