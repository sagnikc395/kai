import type { ChatMessage } from "../api/types";
import { OpenRouterClient } from "../api/client";
import { runMessageLoop, type MessageLoopCallbacks } from "./message_loop";

export class Conversation {
  private messages: ChatMessage[] = [];
  private client: OpenRouterClient;
  private model: string;

  constructor(client: OpenRouterClient, model: string) {
    this.client = client;
    this.model = model;
  }

  async send(
    userMessage: string,
    callbacks: MessageLoopCallbacks,
  ): Promise<void> {
    this.messages.push({
      role: "user",
      content: userMessage,
    });

    this.messages = await runMessageLoop(
      this.client,
      this.messages,
      this.model,
      callbacks,
    );
  }

  getMessages(): ChatMessage[] {
    return [...this.messages];
  }
}
