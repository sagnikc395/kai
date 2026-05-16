package tools

import (
	"os"
	"strings"
)

const (
	colorReset   = "\033[0m"
	colorMuted   = "\033[38;5;245m"
	colorSuccess = "\033[38;5;40m"
	colorError   = "\033[38;5;203m"
	colorTool    = "\033[38;5;214m\033[1m"
	colorFile    = "\033[38;5;75m"
)

func colorize(code, text string) string {
	if os.Getenv("NO_COLOR") != "" {
		return text
	}
	return code + text + colorReset
}

func muted(text string) string {
	return colorize(colorMuted, text)
}

func success(text string) string {
	return colorize(colorSuccess, text)
}

func failure(text string) string {
	return colorize(colorError, text)
}

func toolName(text string) string {
	return colorize(colorTool, text)
}

func fileName(text string) string {
	return colorize(colorFile, text)
}

func truncate(text string, max int) string {
	if len(text) <= max {
		return text
	}
	return strings.TrimSpace(text[:max]) + "..."
}
