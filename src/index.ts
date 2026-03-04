import * as readline from "node:readline";
import chalk from "chalk";
import { runAgentLoop } from "./agent.ts";
import type { ChatCompletionMessageParam } from "openai/resources/chat/completions";

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

const history: ChatCompletionMessageParam[] = [];

function prompt(): Promise<string> {
  return new Promise((resolve) => {
    rl.question(chalk.green("\nkai> "), (answer) => resolve(answer));
  });
}

console.log(chalk.bold("kai") + " — coding agent");
console.log(chalk.dim(`model: ${process.env["KAI_MODEL"] || "gpt-4o"} | cwd: ${process.cwd()}`));
console.log(chalk.dim('Type "exit" or Ctrl+C to quit.\n'));

async function main() {
  while (true) {
    const input = await prompt();
    const trimmed = input.trim();

    if (!trimmed) continue;
    if (trimmed === "exit" || trimmed === "quit") {
      console.log(chalk.dim("Bye!"));
      rl.close();
      process.exit(0);
    }

    history.push({ role: "user", content: trimmed });

    for await (const event of runAgentLoop(history)) {
      switch (event.type) {
        case "assistant_message":
          console.log("\n" + event.content);
          history.push({ role: "assistant", content: event.content });
          break;

        case "tool_call_start":
          console.log(
            chalk.dim(`\n[tool] ${event.name}`) +
              chalk.dim(`(${truncate(event.args, 120)})`)
          );
          break;

        case "tool_call_result":
          console.log(chalk.dim(truncate(event.result, 500)));
          break;

        case "error":
          console.error(chalk.red(`Error: ${event.message}`));
          break;

        case "done":
          break;
      }
    }
  }
}

function truncate(s: string, max: number): string {
  if (s.length <= max) return s;
  return s.slice(0, max) + "…";
}

main();