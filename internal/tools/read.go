package tools

import (
	"fmt"
	"os"
	"strings"
)

type ReadTool struct{}

func (ReadTool) Name() string {
	return "read"
}

func (ReadTool) Description() string {
	return "Read a file from the filesystem. Returns the file content with line numbers. Supports optional offset and limit for reading specific portions of large files."
}

func (ReadTool) Parameters() map[string]any {
	return objectSchema([]string{"file_path"}, map[string]any{
		"file_path": stringSchema("Absolute path to the file to read"),
		"offset":    numberSchema("Line number to start reading from (1-based)"),
		"limit":     numberSchema("Maximum number of lines to read"),
	})
}

func (ReadTool) Call(input map[string]any) Result {
	filePath, err := stringArg(input, "file_path")
	if err != nil {
		return Result{Output: "Error reading file: " + err.Error(), IsError: true}
	}
	offset, err := optionalNumberArg(input, "offset", 0)
	if err != nil {
		return Result{Output: "Error reading file: " + err.Error(), IsError: true}
	}
	limit, err := optionalNumberArg(input, "limit", 0)
	if err != nil {
		return Result{Output: "Error reading file: " + err.Error(), IsError: true}
	}

	content, err := os.ReadFile(filePath)
	if err != nil {
		return Result{Output: "Error reading file: " + err.Error(), IsError: true}
	}

	lines := strings.Split(string(content), "\n")
	startLine := 0
	if offset > 0 {
		startLine = offset - 1
	}
	if startLine > len(lines) {
		startLine = len(lines)
	}
	endLine := len(lines)
	if limit > 0 && startLine+limit < endLine {
		endLine = startLine + limit
	}

	var builder strings.Builder
	for i, line := range lines[startLine:endLine] {
		if i > 0 {
			builder.WriteByte('\n')
		}
		fmt.Fprintf(&builder, "%6d\t%s", startLine+i+1, line)
	}

	return Result{Output: builder.String()}
}

func (ReadTool) RenderToolCall(input map[string]any) string {
	filePath, _ := stringArg(input, "file_path")
	offset, _ := optionalNumberArg(input, "offset", 0)
	limit, _ := optionalNumberArg(input, "limit", 0)

	description := toolName("read") + " " + fileName(filePath)
	if offset > 0 || limit > 0 {
		parts := []string{}
		if offset > 0 {
			parts = append(parts, fmt.Sprintf("from line %d", offset))
		}
		if limit > 0 {
			parts = append(parts, fmt.Sprintf("limit %d", limit))
		}
		description += muted(" (" + strings.Join(parts, ", ") + ")")
	}
	return description
}

func (ReadTool) RenderResult(result Result) string {
	if result.IsError {
		return failure(result.Output)
	}
	return truncateLines(result.Output, 20, "more lines")
}
