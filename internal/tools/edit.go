package tools

import (
	"fmt"
	"os"
	"strings"
)

type EditTool struct{}

func (EditTool) Name() string {
	return "edit"
}

func (EditTool) Description() string {
	return "Edit a file by replacing an exact string match with new content. The old_string must match exactly (including whitespace and indentation). Fails if old_string is not found or matches multiple times (unless replace_all is true)."
}

func (EditTool) Parameters() map[string]any {
	return objectSchema([]string{"file_path", "old_string", "new_string"}, map[string]any{
		"file_path":   stringSchema("Absolute path to the file to edit"),
		"old_string":  stringSchema("The exact string to find and replace"),
		"new_string":  stringSchema("The replacement string"),
		"replace_all": boolSchema("Replace all occurrences (default: false)"),
	})
}

func (EditTool) Call(input map[string]any) Result {
	filePath, err := stringArg(input, "file_path")
	if err != nil {
		return Result{Output: "Error editing file: " + err.Error(), IsError: true}
	}
	oldString, err := stringArg(input, "old_string")
	if err != nil {
		return Result{Output: "Error editing file: " + err.Error(), IsError: true}
	}
	newString, err := stringArg(input, "new_string")
	if err != nil {
		return Result{Output: "Error editing file: " + err.Error(), IsError: true}
	}
	replaceAll, err := optionalBoolArg(input, "replace_all", false)
	if err != nil {
		return Result{Output: "Error editing file: " + err.Error(), IsError: true}
	}

	contentBytes, err := os.ReadFile(filePath)
	if err != nil {
		return Result{Output: "Error editing file: " + err.Error(), IsError: true}
	}
	content := string(contentBytes)

	if oldString == newString {
		return Result{Output: "Error: old_string and new_string are identical", IsError: true}
	}
	if !strings.Contains(content, oldString) {
		return Result{Output: fmt.Sprintf("Error: old_string not found in %s", filePath), IsError: true}
	}
	if !replaceAll && strings.Count(content, oldString) > 1 {
		return Result{Output: fmt.Sprintf("Error: old_string matches multiple locations in %s. Use replace_all or provide more context to make the match unique.", filePath), IsError: true}
	}

	newContent := strings.Replace(content, oldString, newString, 1)
	if replaceAll {
		newContent = strings.ReplaceAll(content, oldString, newString)
	}
	if err := os.WriteFile(filePath, []byte(newContent), 0o644); err != nil {
		return Result{Output: "Error editing file: " + err.Error(), IsError: true}
	}

	return Result{Output: "Successfully edited " + filePath}
}

func (EditTool) RenderToolCall(input map[string]any) string {
	filePath, _ := stringArg(input, "file_path")
	oldString, _ := stringArg(input, "old_string")
	newString, _ := stringArg(input, "new_string")
	return fmt.Sprintf("%s %s\n  %s\n  %s", toolName("edit"), fileName(filePath), failure("- "+truncate(oldString, 40)), success("+ "+truncate(newString, 40)))
}

func (EditTool) RenderResult(result Result) string {
	if result.IsError {
		return failure(result.Output)
	}
	return success(result.Output)
}
