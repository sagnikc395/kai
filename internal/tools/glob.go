package tools

import (
	"fmt"
	"io/fs"
	"os"
	"path"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
)

type GlobTool struct{}

func (GlobTool) Name() string {
	return "glob"
}

func (GlobTool) Description() string {
	return "Find files matching a glob pattern. Returns matching file paths sorted alphabetically. Useful for discovering files by name or extension."
}

func (GlobTool) Parameters() map[string]any {
	return objectSchema([]string{"pattern"}, map[string]any{
		"pattern": stringSchema("The glob pattern to match files against"),
		"path":    stringSchema("Directory to search in (defaults to cwd)"),
	})
}

func (GlobTool) Call(input map[string]any) Result {
	pattern, err := stringArg(input, "pattern")
	if err != nil {
		return Result{Output: "Error: " + err.Error(), IsError: true}
	}
	searchPath, ok, err := optionalStringArg(input, "path")
	if err != nil {
		return Result{Output: "Error: " + err.Error(), IsError: true}
	}
	if !ok || searchPath == "" {
		searchPath, err = os.Getwd()
		if err != nil {
			return Result{Output: "Error: " + err.Error(), IsError: true}
		}
	}

	files, err := expandGlob(pattern, searchPath)
	if err != nil {
		return Result{Output: "Error: " + err.Error(), IsError: true}
	}
	sort.Strings(files)
	if len(files) == 0 {
		return Result{Output: "No files matched the pattern."}
	}
	return Result{Output: strings.Join(files, "\n")}
}

func (GlobTool) RenderToolCall(input map[string]any) string {
	pattern, _ := stringArg(input, "pattern")
	searchPath, ok, _ := optionalStringArg(input, "path")
	description := toolName("glob") + " " + fileName(pattern)
	if ok && searchPath != "" {
		description += muted(" in " + searchPath)
	}
	return description
}

func (GlobTool) RenderResult(result Result) string {
	if result.IsError {
		return failure(result.Output)
	}
	return truncateLines(result.Output, 20, "more files")
}

func expandGlob(pattern, searchPath string) ([]string, error) {
	if !strings.Contains(pattern, "**") {
		matches, err := filepath.Glob(resolvePattern(pattern, searchPath))
		if err != nil {
			return nil, err
		}
		return onlyFiles(matches), nil
	}

	root, absolutePattern, err := globRoot(pattern, searchPath)
	if err != nil {
		return nil, err
	}

	patternSlash := filepath.ToSlash(absolutePattern)
	if runtime.GOOS == "windows" {
		patternSlash = strings.ToLower(patternSlash)
	}

	var matches []string
	err = filepath.WalkDir(root, func(current string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return nil
		}
		if entry.IsDir() {
			return nil
		}
		candidate := filepath.ToSlash(current)
		compare := candidate
		if runtime.GOOS == "windows" {
			compare = strings.ToLower(compare)
		}
		if matchGlobSegments(patternSlash, compare) {
			abs, err := filepath.Abs(current)
			if err != nil {
				return nil
			}
			matches = append(matches, abs)
		}
		return nil
	})
	if err != nil {
		return nil, err
	}
	return matches, nil
}

func resolvePattern(pattern, searchPath string) string {
	if filepath.IsAbs(pattern) {
		return pattern
	}
	return filepath.Join(searchPath, pattern)
}

func onlyFiles(paths []string) []string {
	files := make([]string, 0, len(paths))
	for _, item := range paths {
		info, err := os.Stat(item)
		if err != nil || info.IsDir() {
			continue
		}
		abs, err := filepath.Abs(item)
		if err != nil {
			continue
		}
		files = append(files, abs)
	}
	return files
}

func globRoot(pattern, searchPath string) (string, string, error) {
	absolutePattern := resolvePattern(pattern, searchPath)
	cleanPattern := filepath.Clean(absolutePattern)
	parts := strings.Split(filepath.ToSlash(cleanPattern), "/")

	rootParts := []string{}
	for _, part := range parts {
		if hasGlobMeta(part) {
			break
		}
		rootParts = append(rootParts, part)
	}

	root := strings.Join(rootParts, "/")
	if root == "" {
		root = string(filepath.Separator)
	}
	if runtime.GOOS != "windows" && strings.HasPrefix(cleanPattern, string(filepath.Separator)) && !strings.HasPrefix(root, "/") {
		root = "/" + root
	}

	info, err := os.Stat(filepath.FromSlash(root))
	if err != nil {
		return "", "", err
	}
	if !info.IsDir() {
		return "", "", fmt.Errorf("%s is not a directory", root)
	}
	return filepath.FromSlash(root), cleanPattern, nil
}

func hasGlobMeta(value string) bool {
	return strings.ContainsAny(value, "*?[")
}

func matchGlobSegments(patternValue, candidateValue string) bool {
	patternParts := splitPath(patternValue)
	candidateParts := splitPath(candidateValue)
	return matchParts(patternParts, candidateParts)
}

func splitPath(value string) []string {
	value = strings.Trim(value, "/")
	if value == "" {
		return nil
	}
	return strings.Split(value, "/")
}

func matchParts(patternParts, candidateParts []string) bool {
	if len(patternParts) == 0 {
		return len(candidateParts) == 0
	}
	if patternParts[0] == "**" {
		if matchParts(patternParts[1:], candidateParts) {
			return true
		}
		for i := range candidateParts {
			if matchParts(patternParts[1:], candidateParts[i+1:]) {
				return true
			}
		}
		return false
	}
	if len(candidateParts) == 0 {
		return false
	}
	ok, err := path.Match(patternParts[0], candidateParts[0])
	if err != nil || !ok {
		return false
	}
	return matchParts(patternParts[1:], candidateParts[1:])
}
