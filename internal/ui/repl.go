package ui

import (
	"bufio"
	"context"
	"fmt"
	"io"
	"strings"

	"github.com/sagnikc395/kai/internal/api"
	"github.com/sagnikc395/kai/internal/core"
)

func RunREPL(ctx context.Context, client *api.OpenRouterClient, model string, input io.Reader, output io.Writer) error {
	conversation := core.NewConversation(client, model)
	reader := bufio.NewReader(input)

	fmt.Fprintf(output, "%skai%s %s(%s)%s\n", primary(), reset(), muted(), model, reset())
	fmt.Fprintf(output, "%sType a message to chat. \"exit\" to quit.%s\n\n", muted(), reset())

	for {
		fmt.Fprintf(output, "%s> %s", primary(), reset())
		line, err := reader.ReadString('\n')
		if err != nil {
			if err == io.EOF {
				return nil
			}
			return err
		}

		message := strings.TrimSpace(line)
		if message == "" {
			continue
		}
		switch strings.ToLower(message) {
		case "exit", "quit":
			return nil
		}

		toolTextPrinted := false
		callbacks := core.MessageLoopCallbacks{
			OnToken: func(token string) {
				fmt.Fprint(output, token)
			},
			OnToolStart: func(toolCalls []api.ToolCall) {
				if !strings.HasSuffix(message, "\n") {
					fmt.Fprintln(output)
				}
				fmt.Fprintf(output, "%sExecuting tools...%s\n", muted(), reset())
				toolTextPrinted = true
			},
			OnToolResult: func(results []core.ToolExecutionResult) {
				for _, result := range results {
					fmt.Fprintf(output, "  %s %s\n", mutedLine("┌"), result.CallSummary)
					for _, line := range strings.Split(result.ResultSummary, "\n") {
						fmt.Fprintf(output, "  %s %s\n", mutedLine("│"), line)
					}
					status := success("done")
					if result.Result.IsError {
						status = failure("error")
					}
					fmt.Fprintf(output, "  %s %s\n", mutedLine("└"), status)
				}
			},
			OnComplete: func(text string) {
				if text != "" {
					fmt.Fprintln(output)
				} else if toolTextPrinted {
					fmt.Fprintln(output)
				}
			},
			OnError: func(err error) {
				fmt.Fprintf(output, "\n%sError:%s %s\n", failureColor(), reset(), err.Error())
			},
		}

		conversation.Send(ctx, message, callbacks)
	}
}

func primary() string {
	return "\033[38;5;99m\033[1m"
}

func muted() string {
	return "\033[38;5;245m"
}

func reset() string {
	return "\033[0m"
}

func failureColor() string {
	return "\033[38;5;203m"
}

func successColor() string {
	return "\033[38;5;40m"
}

func success(text string) string {
	return successColor() + text + reset()
}

func failure(text string) string {
	return failureColor() + text + reset()
}

func mutedLine(text string) string {
	return muted() + text + reset()
}
