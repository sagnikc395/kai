import type { ChatCompletionMessageParam } from "openai/resources/chat/completions";

// --- Agent Events (yielded by the agent loop) ---

export type AgentEvent =
  | { type: "assistant_message"; content: string }
  | { type: "tool_call_start"; id: string; name: string; args: string }
  | { type: "tool_call_result"; id: string; name: string; result: string }
  | { type: "error"; message: string }
  | { type: "done" };

// --- Display Messages (for UI rendering) ---

export type DisplayMessage =
  | { role: "user"; content: string }
  | { role: "assistant"; content: string }
  | {
      role: "tool_call";
      id: string;
      name: string;
      args: string;
      result?: string;
    };

// --- Tool Definition ---

export interface ToolDefinition {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  execute: (args: Record<string, unknown>) => Promise<string>;
}

// --- Conversation history type alias ---

export type ConversationMessage = ChatCompletionMessageParam;
