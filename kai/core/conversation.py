from __future__ import annotations

from typing import Any

from groq import Groq

from kai.core.message_loop import MessageLoopCallbacks, run_message_loop


class Conversation:
    def __init__(self, client: Groq, model: str) -> None:
        self.client = client
        self.model = model
        self.messages: list[dict[str, Any]] = []

    def send(self, user_message: str, callbacks: MessageLoopCallbacks) -> None:
        self.messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )
        self.messages = run_message_loop(
            self.client, self.messages, self.model, callbacks
        )

    def copy_messages(self) -> list[dict[str, Any]]:
        return list(self.messages)
