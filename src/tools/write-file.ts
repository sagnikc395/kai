import type { ToolDefinition } from "../types.ts";

export const writeFileTool: ToolDefinition = {
  name: "write_file",
  description:
    "Write content to a file at the given path. Creates parent directories if needed.",
  parameters: {
    type: "object",
    properties: {
      path: { type: "string", description: "Absolute or relative file path" },
      content: { type: "string", description: "Content to write" },
    },
    required: ["path", "content"],
  },
  async execute(args) {
    const path = args.path as string;
    const content = args.content as string;
    try {
      await Bun.write(path, content);
      const bytes = Buffer.byteLength(content, "utf-8");
      return `Wrote ${bytes} bytes to ${path}`;
    } catch (e) {
      return `Error writing file: ${(e as Error).message}`;
    }
  },
};
