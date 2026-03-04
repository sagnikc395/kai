import type { ToolDefinition } from "../types.ts";

const TIMEOUT_MS = 30_000;

export const bashTool: ToolDefinition = {
  name: "bash",
  description: "Execute a bash command and return stdout, stderr, and exit code.",
  parameters: {
    type: "object",
    properties: {
      command: { type: "string", description: "The bash command to execute" },
    },
    required: ["command"],
  },
  async execute(args) {
    const command = args.command as string;
    try {
      const proc = Bun.spawn(["bash", "-c", command], {
        stdout: "pipe",
        stderr: "pipe",
      });

      const timer = setTimeout(() => proc.kill(), TIMEOUT_MS);

      const [stdout, stderr] = await Promise.all([
        new Response(proc.stdout).text(),
        new Response(proc.stderr).text(),
      ]);

      const exitCode = await proc.exited;
      clearTimeout(timer);

      let result = "";
      if (stdout) result += stdout;
      if (stderr) result += (result ? "\n" : "") + `stderr: ${stderr}`;
      result += (result ? "\n" : "") + `exit code: ${exitCode}`;
      return result;
    } catch (e) {
      return `Error executing command: ${(e as Error).message}`;
    }
  },
};
