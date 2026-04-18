export interface SandboxOptions {
  timeout?: number;
  memoryLimitMb?: number;
  allowNetwork?: boolean;
  env?: Record<string, string>;
}

export interface SandboxResult {
  stdout: string;
  stderr: string;
  exitCode: number;
  timedOut: boolean;
  durationMs: number;
}
