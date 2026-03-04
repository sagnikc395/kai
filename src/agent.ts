import OpenAI from "openai";
import type {
  ChatCompletionMessageParam,
  ChatCompletionAssistantMessageParam,
} from "openai/resources/chat/completions";
import { toolDefinitions, executeTool } from "./tools/index.ts";
import type { AgentEvent } from "./types.ts";

let _client: OpenAI | null = null;
function getClient() {
  if (!_client) _client = new OpenAI();
  return _client;
}

const model = process.env["KAI_MODEL"] || "gpt-4o";

const SYSTEM_PROMPT = `You are kai, a helpful coding assistant running in the user's terminal.
Working directory: ${process.cwd()}

You have access to tools for reading/writing files, running bash commands, and finding files.
Use tools when needed to answer the user's questions or complete tasks.
Be concise and direct in your responses.`;

export async function* runAgentLoop(
  history: ChatCompletionMessageParam[]
): AsyncGenerator<AgentEvent> {
  const messages: ChatCompletionMessageParam[] = [
    { role: "system", content: SYSTEM_PROMPT },
    ...history,
  ];

  const MAX_ITERATIONS = 20;

  for (let i = 0; i < MAX_ITERATIONS; i++) {
    let response;
    try {
      response = await getClient().chat.completions.create({
        model,
        messages,
        tools: toolDefinitions,
      });
    } catch (e) {
      yield { type: "error", message: (e as Error).message };
      yield { type: "done" };
      return;
    }

    const choice = response.choices[0];
    if (!choice) {
      yield { type: "error", message: "No response from model" };
      yield { type: "done" };
      return;
    }

    const assistantMessage = choice.message;

    // Emit text content if present
    if (assistantMessage.content) {
      yield { type: "assistant_message", content: assistantMessage.content };
    }

    // If no tool calls, we're done
    if (
      !assistantMessage.tool_calls ||
      assistantMessage.tool_calls.length === 0
    ) {
      yield { type: "done" };
      return;
    }

    // Add assistant message to history
    messages.push(assistantMessage as ChatCompletionAssistantMessageParam);

    // Execute tool calls
    for (const toolCall of assistantMessage.tool_calls) {
      const { id, function: fn } = toolCall;

      let args: Record<string, unknown>;
      try {
        args = JSON.parse(fn.arguments);
      } catch {
        args = {};
      }

      yield {
        type: "tool_call_start",
        id,
        name: fn.name,
        args: fn.arguments,
      };

      const result = await executeTool(fn.name, args);

      yield { type: "tool_call_result", id, name: fn.name, result };

      messages.push({
        role: "tool",
        tool_call_id: id,
        content: result,
      });
    }

    // Loop continues — model will process tool results
  }

  yield {
    type: "error",
    message: "Agent loop exceeded maximum iterations",
  };
  yield { type: "done" };
}
