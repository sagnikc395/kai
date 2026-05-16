package tools

import (
	"fmt"
	"strings"
)

func truncateLines(output string, maxLines int, label string) string {
	lines := strings.Split(output, "\n")
	if len(lines) <= maxLines {
		return output
	}
	return strings.Join(lines[:maxLines], "\n") + "\n" + muted(fmt.Sprintf("... (%d %s)", len(lines)-maxLines, label))
}
