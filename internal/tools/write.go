package tools

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

type WriteTool struct{}

func (WriteTool) Name() string {
	return "write"
}

func (WriteTool) Description() string {
	return "Write content to a file. Creates the file and any parent directories if they don't exist. Overwrites existing files."
}

func (WriteTool) Parameters() map[string]any {
	return objectSchema([]string{"file_path", "content"}, map[string]any{
		"file_path": stringSchema("Absolute path to the file to write"),
		"content":   stringSchema("The content to write to the file"),
	})
}

func (WriteTool) Call(input map[string]any) Result {
	filePath, err := stringArg(input, "file_path")
	if err != nil {
		return Result{Output: "Error writing file: " + err.Error(), IsError: true}
	}
	content, err := stringArg(input, "content")
	if err != nil {
		return Result{Output: "Error writing file: " + err.Error(), IsError: true}
	}

	if err := os.MkdirAll(filepath.Dir(filePath), 0o755); err != nil {
		return Result{Output: "Error writing file: " + err.Error(), IsError: true}
	}
	if err := os.WriteFile(filePath, []byte(content), 0o644); err != nil {
		return Result{Output: "Error writing file: " + err.Error(), IsError: true}
	}

	lines := len(strings.Split(content, "\n"))
	return Result{Output: fmt.Sprintf("Successfully wrote %d lines to %s", lines, filePath)}
}

func (WriteTool) RenderToolCall(input map[string]any) string {
	filePath, _ := stringArg(input, "file_path")
	content, _ := stringArg(input, "content")
	lines := len(strings.Split(content, "\n"))
	return fmt.Sprintf("%s %s %s", toolName("write"), fileName(filePath), muted(fmt.Sprintf("(%d lines)", lines)))
}

func (WriteTool) RenderResult(result Result) string {
	if result.IsError {
		return failure(result.Output)
	}
	return success(result.Output)
}
