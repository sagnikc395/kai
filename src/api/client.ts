import type { ChatCompletionRequest, ChatCompletionChunk } from "./types";

const OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1";

async function* parseSSEStream(
  body: ReadableStream<Uint8Array>,
): AsyncGenerator<string> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed?.startsWith("data: ")) continue;
        const data = trimmed.slice(6);
        if (data === "[DONE]") return;
        yield data;
      }
    }
  } catch (e) {
    console.error(`MALFORMED JSON chunks !`);
  } finally {
    reader.releaseLock();
  }
}

export class OpenRouterClient {
  constructor(private apiKey: string) {}

  async *streamChatCompletion(
    request: ChatCompletionRequest,
  ): AsyncGenerator<ChatCompletionChunk> {
    const response = await fetch(`${OPENROUTER_BASE_URL}/chat/completions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/youtube-cc",
        "X-Title": "youtube-cc",
      },
      body: JSON.stringify({ ...request, stream: true }),
    });

    if (!response.ok) {
      throw new Error(
        `OpenRouter API error (${response.status}): ${await response.text()}`,
      );
    }
    if (!response.body) throw new Error("No response body received");

    for await (const data of parseSSEStream(response.body)) {
      try {
        yield JSON.parse(data) as ChatCompletionChunk;
      } catch {}
    }
  }
}
