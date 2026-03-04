import type { ToolDefinition } from "../types.ts";

const MAX_SIZE = 100 * 1024; // 100KB

export const readFileTool: ToolDefinition = {
  name: "read_file",
  description: "Read the contents of a file at the given path.",
  parameters: {
    type: "object",
    properties: {
      path: { type: "string", description: "Absolute or relative file path" },
    },
    required: ["path"],
  },
  async execute(args) {
    const path = args.path as string;
    try {
      const file = Bun.file(path);
      const size = file.size;
      if (size > MAX_SIZE) {
        const text = await file.text();
        return text.slice(0, MAX_SIZE) + `\n\n[truncated — file is ${size} bytes]`;
      }
      return await file.text();
    } catch (e) {
      return `Error reading file: ${(e as Error).message}`;
    }
  },
};
