package tools

import (
	"bufio"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

type GrepTool struct{}

func (GrepTool) Name() string {
	return "grep"
}

func (GrepTool) Description() string {
	return "Search file contents using regex patterns. Returns matching lines with file paths and line numbers."
}

func (GrepTool) Parameters() map[string]any {
	return objectSchema([]string{"pattern"}, map[string]any{
		"pattern": stringSchema("The regex pattern to search for"),
		"path":    stringSchema("File or directory to search in (defaults to cwd)"),
		"include": stringSchema("Glob pattern to filter files (e.g. '*.ts')"),
	})
}

func (GrepTool) Call(input map[string]any) Result {
	pattern, err := stringArg(input, "pattern")
	if err != nil {
		return Result{Output: "Error: " + err.Error(), IsError: true}
	}
	searchPath, ok, err := optionalStringArg(input, "path")
	if err != nil {
		return Result{Output: "Error: " + err.Error(), IsError: true}
	}
	if !ok || searchPath == "" {
		searchPath = "."
	}
	include, includeOK, err := optionalStringArg(input, "include")
	if err != nil {
		return Result{Output: "Error: " + err.Error(), IsError: true}
	}

	expression, err := regexp.Compile(pattern)
	if err != nil {
		return Result{Output: "Error: " + err.Error(), IsError: true}
	}

	matches, err := grepFiles(expression, searchPath, include, includeOK)
	if err != nil {
		return Result{Output: "Error: " + err.Error(), IsError: true}
	}
	if len(matches) == 0 {
		return Result{Output: "No matches found."}
	}
	return Result{Output: strings.Join(matches, "\n")}
}

func (GrepTool) RenderToolCall(input map[string]any) string {
	pattern, _ := stringArg(input, "pattern")
	searchPath, pathOK, _ := optionalStringArg(input, "path")
	include, includeOK, _ := optionalStringArg(input, "include")

	description := toolName("grep") + " " + muted("/") + pattern + muted("/")
	if pathOK && searchPath != "" {
		description += " " + muted("in") + " " + fileName(searchPath)
	}
	if includeOK && include != "" {
		description += " " + muted("("+include+")")
	}
	return description
}

func (GrepTool) RenderResult(result Result) string {
	if result.IsError {
		return failure(result.Output)
	}
	return truncateLines(result.Output, 20, "more lines")
}

func grepFiles(expression *regexp.Regexp, searchPath, include string, includeOK bool) ([]string, error) {
	info, err := os.Stat(searchPath)
	if err != nil {
		return nil, err
	}

	var files []string
	if !info.IsDir() {
		files = append(files, searchPath)
	} else {
		err := filepath.WalkDir(searchPath, func(current string, entry fs.DirEntry, walkErr error) error {
			if walkErr != nil {
				return nil
			}
			if entry.IsDir() {
				return nil
			}
			files = append(files, current)
			return nil
		})
		if err != nil {
			return nil, err
		}
	}

	var matches []string
	for _, filePath := range files {
		if includeOK && include != "" {
			ok, err := filepath.Match(include, filepath.Base(filePath))
			if err != nil {
				return nil, err
			}
			if !ok {
				continue
			}
		}
		fileMatches := grepFile(expression, filePath, 100-len(matches))
		matches = append(matches, fileMatches...)
		if len(matches) >= 100 {
			break
		}
	}
	return matches, nil
}

func grepFile(expression *regexp.Regexp, filePath string, remaining int) []string {
	if remaining <= 0 {
		return nil
	}
	file, err := os.Open(filePath)
	if err != nil {
		return nil
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	scanner.Buffer(make([]byte, 1024), 1024*1024)

	var matches []string
	lineNumber := 0
	for scanner.Scan() {
		lineNumber++
		line := scanner.Text()
		if !expression.MatchString(line) {
			continue
		}
		if len(line) > 200 {
			line = line[:200]
		}
		matches = append(matches, fmt.Sprintf("%s:%d:%s", filePath, lineNumber, line))
		if len(matches) >= remaining {
			break
		}
	}
	return matches
}
