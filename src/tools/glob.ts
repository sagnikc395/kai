import type { ToolDefinition } from "../types.ts";

const MAX_ENTRIES = 1000;

export const globTool: ToolDefinition = {
  name: "glob",
  description:
    "Find files matching a glob pattern. Returns matching file paths.",
  parameters: {
    type: "object",
    properties: {
      pattern: {
        type: "string",
        description: 'Glob pattern (e.g. "src/**/*.ts")',
      },
      cwd: {
        type: "string",
        description: "Directory to search in (defaults to working directory)",
      },
    },
    required: ["pattern"],
  },
  async execute(args) {
    const pattern = args.pattern as string;
    const cwd = (args.cwd as string) || process.cwd();
    try {
      const glob = new Bun.Glob(pattern);
      const entries: string[] = [];
      for await (const entry of glob.scan({ cwd })) {
        entries.push(entry);
        if (entries.length >= MAX_ENTRIES) break;
      }
      if (entries.length === 0) return "No files matched.";
      let result = entries.join("\n");
      if (entries.length >= MAX_ENTRIES) {
        result += `\n\n[limited to ${MAX_ENTRIES} entries]`;
      }
      return result;
    } catch (e) {
      return `Error scanning files: ${(e as Error).message}`;
    }
  },
};
