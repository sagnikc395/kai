package tools

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestReadWriteEditTools(t *testing.T) {
	t.Setenv("NO_COLOR", "1")
	tempDir := t.TempDir()
	filePath := filepath.Join(tempDir, "notes", "todo.txt")

	writeResult := (WriteTool{}).Call(map[string]any{
		"file_path": filePath,
		"content":   "alpha\nbeta\nalpha",
	})
	if writeResult.IsError {
		t.Fatalf("write failed: %s", writeResult.Output)
	}

	readResult := (ReadTool{}).Call(map[string]any{
		"file_path": filePath,
		"offset":    float64(2),
		"limit":     float64(1),
	})
	if readResult.IsError {
		t.Fatalf("read failed: %s", readResult.Output)
	}
	if !strings.Contains(readResult.Output, "2\tbeta") {
		t.Fatalf("read output missing numbered line: %q", readResult.Output)
	}

	duplicateEdit := (EditTool{}).Call(map[string]any{
		"file_path":   filePath,
		"old_string":  "alpha",
		"new_string":  "gamma",
		"replace_all": false,
	})
	if !duplicateEdit.IsError {
		t.Fatalf("expected duplicate edit to fail")
	}

	editResult := (EditTool{}).Call(map[string]any{
		"file_path":   filePath,
		"old_string":  "alpha",
		"new_string":  "gamma",
		"replace_all": true,
	})
	if editResult.IsError {
		t.Fatalf("edit failed: %s", editResult.Output)
	}

	content, err := os.ReadFile(filePath)
	if err != nil {
		t.Fatal(err)
	}
	if got := string(content); got != "gamma\nbeta\ngamma" {
		t.Fatalf("unexpected edited content: %q", got)
	}
}

func TestGlobAndGrepTools(t *testing.T) {
	t.Setenv("NO_COLOR", "1")
	tempDir := t.TempDir()
	mustWrite(t, filepath.Join(tempDir, "a.go"), "package main\n")
	mustWrite(t, filepath.Join(tempDir, "nested", "b.go"), "package nested\nfunc Target() {}\n")
	mustWrite(t, filepath.Join(tempDir, "nested", "b.txt"), "Target in text\n")

	globResult := (GlobTool{}).Call(map[string]any{
		"pattern": "**/*.go",
		"path":    tempDir,
	})
	if globResult.IsError {
		t.Fatalf("glob failed: %s", globResult.Output)
	}
	if !strings.Contains(globResult.Output, filepath.Join(tempDir, "a.go")) ||
		!strings.Contains(globResult.Output, filepath.Join(tempDir, "nested", "b.go")) {
		t.Fatalf("glob output missing expected files: %q", globResult.Output)
	}

	grepResult := (GrepTool{}).Call(map[string]any{
		"pattern": "Target",
		"path":    tempDir,
		"include": "*.go",
	})
	if grepResult.IsError {
		t.Fatalf("grep failed: %s", grepResult.Output)
	}
	if !strings.Contains(grepResult.Output, "b.go:2:func Target() {}") {
		t.Fatalf("grep output missing expected match: %q", grepResult.Output)
	}
	if strings.Contains(grepResult.Output, "b.txt") {
		t.Fatalf("grep include filter did not exclude txt file: %q", grepResult.Output)
	}
}

func mustWrite(t *testing.T, path string, content string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
}
