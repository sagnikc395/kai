package tools

import (
	"bytes"
	"context"
	"errors"
	"os/exec"
	"runtime"
	"strings"
	"time"
)

type BashTool struct{}

func (BashTool) Name() string {
	return "bash"
}

func (BashTool) Description() string {
	return "Execute a bash command and return its output. Use for running shell commands, installing packages, running scripts, etc."
}

func (BashTool) Parameters() map[string]any {
	return objectSchema([]string{"command"}, map[string]any{
		"command": stringSchema("The bash command to execute"),
		"timeout": numberSchema("Timeout in milliseconds (default 30s)"),
	})
}

func (BashTool) Call(input map[string]any) Result {
	command, err := stringArg(input, "command")
	if err != nil {
		return Result{Output: "Error: " + err.Error(), IsError: true}
	}
	timeout, err := optionalNumberArg(input, "timeout", 30000)
	if err != nil {
		return Result{Output: "Error: " + err.Error(), IsError: true}
	}

	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(timeout)*time.Millisecond)
	defer cancel()

	cmd := shellCommand(ctx, command)
	var stdout bytes.Buffer
	var stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err = cmd.Run()
	output := strings.TrimSpace(stdout.String())
	if stderr.Len() > 0 {
		if output != "" {
			output += "\n"
		}
		output += strings.TrimSpace(stderr.String())
	}
	if output == "" {
		output = "(no output)"
	}

	isError := err != nil
	if errors.Is(ctx.Err(), context.DeadlineExceeded) {
		isError = true
		if output == "(no output)" {
			output = "Error: command timed out"
		} else {
			output += "\nError: command timed out"
		}
	} else if err != nil && output == "(no output)" {
		output = "Error: " + err.Error()
	}

	return Result{Output: output, IsError: isError}
}

func (BashTool) RenderToolCall(input map[string]any) string {
	command, _ := stringArg(input, "command")
	return toolName("bash") + " " + muted("$") + " " + command
}

func (BashTool) RenderResult(result Result) string {
	if result.IsError {
		return failure(result.Output)
	}
	return result.Output
}

func shellCommand(ctx context.Context, command string) *exec.Cmd {
	if runtime.GOOS == "windows" {
		return exec.CommandContext(ctx, "cmd", "/C", command)
	}
	return exec.CommandContext(ctx, "bash", "-lc", command)
}
