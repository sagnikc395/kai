import { BashInputSchema } from "./schema";
import { exec } from "child_process";
import type { Tool, ToolResult } from "./types";
import { colors } from "../utils/colors";

export const bashTool: Tool = {
  name: "bash",
  description:
    "Execute a bash command and return its output. Use for running shell commands, installing packages, running scripts, etc.",
  BashInputSchema,

  async call(input): Promise<ToolResult> {
    const { command, timeout } = BashInputSchema.parse(input);

    return new Promise((resolve) => {
      exec(
        command,
        { timeout, maxBuffer: 1024 * 1024 * 10 },
        (error, stdout, stderr) => {
          if (error && !stdout && !stderr) {
            resolve({
              output: `Error: ${error.message}`,
              isError: true,
            });
            return;
          }

          let output = "";
          if (stdout) output += stdout;
          if (stderr) output += (output ? "\n" : "") + stderr;
          if (!output) output = "(no output)";

          resolve({
            output: output.trim(),
            isError: !!error,
          });
        },
      );
    });
  },

  renderToolCall(input) {
    const { command } = BashInputSchema.parse(input);
    return `${colors.toolName("bash")} ${colors.muted("$")} ${command}`;
  },

  renderResult(result) {
    if (result.isError) {
      return colors.error(result.output);
    }
    return result.output;
  },
};
