// sandbox/runner.ts
import { write, spawn, file } from "bun";
import { randomUUID } from "crypto";
import { rm } from "fs/promises";
import type { SandboxOptions, SandboxResult } from "./types";

export async function runInSandbox(
  code: string,
  options: SandboxOptions = {},
): Promise<SandboxResult> {
  const { timeout = 5000, allowNetwork = false, env = {} } = options;

  const tmpFile = `/tmp/sandbox-${randomUUID()}.ts`;
  await write(tmpFile, code);

  const start = Date.now();

  const proc = spawn({
    cmd: ["bun", "run", tmpFile],
    stdout: "pipe",
    stderr: "pipe",
    env: {
      ...(!allowNetwork ? { NO_PROXY: "*" } : {}),
      ...env,
      HOME: "/tmp",
      PATH: "/usr/local/bin:/usr/bin",
    },
  });

  const timeoutHandle = setTimeout(() => proc.kill(), timeout);

  const [stdout, stderr, exitCode] = await Promise.all([
    new Response(proc.stdout).text(),
    new Response(proc.stderr).text(),
    proc.exited,
  ]);

  clearTimeout(timeoutHandle);
  await rm(tmpFile, { force: true });

  return {
    stdout,
    stderr,
    exitCode,
    timedOut: exitCode === null,
    durationMs: Date.now() - start,
  };
}
