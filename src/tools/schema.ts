import { z } from "zod";

// read input schema
export const ReadInputSchema = z.object({
  file_path: z.string().describe("Absolute path to the file to read"),
  offset: z
    .number()
    .optional()
    .describe("Line number to start reading from (1-based)"),
  limit: z.number().optional().describe("Maximum number of lines to read"),
});

//write input schema
export const WriteInputSchema = z.object({
  file_path: z.string().describe("Absolute path to the file to write"),
  content: z.string().describe("The content to write to the file"),
});

//grepping input from source code

export const GrepInputSchema = z.object({
  pattern: z.string().describe("The regex pattern to search for"),
  path: z
    .string()
    .optional()
    .describe("File or directory to search in (defaults to cwd)"),
  include: z
    .string()
    .optional()
    .describe("Glob pattern to filter files (e.g. '*.ts')"),
});

// searching in a directory

export const GlobInputSchema = z.object({
  pattern: z.string().describe("The glob pattern to match files against"),
  path: z
    .string()
    .optional()
    .describe("Directory to search in (defaults to cwd)"),
});

//edit to the file path

export const EditInputSchema = z.object({
  file_path: z.string().describe("Absolute path to the file to edit"),
  old_string: z.string().describe("The exact string to find and replace"),
  new_string: z.string().describe("The replacement string"),
  replace_all: z
    .boolean()
    .optional()
    .default(false)
    .describe("Replace all occurrences (default: false)"),
});

// bash service

export const BashInputSchema = z.object({
  command: z.string().describe("The bash command to execute"),
  timeout: z
    .number()
    .optional()
    .default(30000)
    .describe("Timeout in milliseconds (default 30s)"),
});
