from __future__ import annotations

from typing import Any

from kai.api.base import Backend
from kai.core.message_loop import MessageLoopCallbacks, run_message_loop


class Conversation:
    def __init__(self, backend: Backend) -> None:
        self.backend = backend
        self.messages: list[dict[str, Any]] = []

    @property
    def model(self) -> str:
        return self.backend.model

    def send(self, user_message: str, callbacks: MessageLoopCallbacks) -> None:
        self.messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )
        self.messages = run_message_loop(self.backend, self.messages, callbacks)

    def copy_messages(self) -> list[dict[str, Any]]:
        return list(self.messages)
