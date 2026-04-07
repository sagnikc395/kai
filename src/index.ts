import { Command } from "commander";
import { App } from "./ui/App";
import { render } from "ink";
import React from "react";

export function startKai() {
  const program = new Command();
  program
    .name("kai")
    .description("a simple coding assistant in your terminal")
    .version("1.0.0")
    .option(
      "-m --model <model>",
      "Model to use via OpenRouter",
      "anthropic/claude-sonnet-4",
    )
    .action((options) => {
      const apiKey = process.env.OPENROUTER_API_KEY;

      if (!apiKey) {
        console.error(
          "ERROR: OPENROUTER_API_KEY environment variable is required.\n" +
            "Set it with: export OPENROUTER_API_KEY=your_key_here",
        );
        process.exit(1);
      }

      render(
        React.createElement(App, {
          apiKey,
          model: options.model,
        }),
      );
    });

  return program;
}

startKai().parse();
