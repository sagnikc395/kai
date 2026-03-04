import type { ToolDefinition } from "../types.ts";
import type { ChatCompletionTool } from "openai/resources/chat/completions";
import { readFileTool } from "./read-file.ts";
import { writeFileTool } from "./write-file.ts";
import { bashTool } from "./bash.ts";
import { globTool } from "./glob.ts";

const tools: ToolDefinition[] = [readFileTool, writeFileTool, bashTool, globTool];

const toolMap = new Map<string, ToolDefinition>(
  tools.map((t) => [t.name, t])
);

export const toolDefinitions: ChatCompletionTool[] = tools.map((t) => ({
  type: "function" as const,
  function: {
    name: t.name,
    description: t.description,
    parameters: t.parameters,
  },
}));

export async function executeTool(
  name: string,
  args: Record<string, unknown>
): Promise<string> {
  const tool = toolMap.get(name);
  if (!tool) return `Unknown tool: ${name}`;
  return tool.execute(args);
}
