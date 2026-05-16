package core

import (
	"encoding/json"
	"fmt"

	groq "github.com/conneroisu/groq-go"
	groqtools "github.com/conneroisu/groq-go/pkg/tools"
	"github.com/sagnikc395/kai/internal/tools"
)

type ToolExecutionResult struct {
	ToolCall      groqtools.ToolCall
	Result        tools.Result
	CallSummary   string
	ResultSummary string
}

func ExecuteToolCalls(toolCalls []groqtools.ToolCall) ([]groq.ChatCompletionMessage, []ToolExecutionResult) {
	messages := make([]groq.ChatCompletionMessage, 0, len(toolCalls))
	results := make([]ToolExecutionResult, 0, len(toolCalls))

	for _, toolCall := range toolCalls {
		tool, ok := tools.Get(toolCall.Function.Name)

		var result tools.Result
		var callSummary string
		var resultSummary string

		if !ok {
			result = tools.Result{
				Output:  fmt.Sprintf("Unknown tool: %s", toolCall.Function.Name),
				IsError: true,
			}
			callSummary = fmt.Sprintf("Unknown tool: %s", toolCall.Function.Name)
			resultSummary = result.Output
		} else {
			var parsedArgs map[string]any
			if err := json.Unmarshal([]byte(toolCall.Function.Arguments), &parsedArgs); err != nil {
				result = tools.Result{
					Output:  fmt.Sprintf("Invalid JSON arguments: %s", toolCall.Function.Arguments),
					IsError: true,
				}
				callSummary = tool.Name() + " (invalid args)"
				resultSummary = result.Output
			} else {
				callSummary = tool.RenderToolCall(parsedArgs)
				result = tool.Call(parsedArgs)
				resultSummary = tool.RenderResult(result)
			}
		}

		messages = append(messages, groq.ChatCompletionMessage{
			Role:       groq.RoleTool,
			ToolCallID: toolCall.ID,
			Content:    result.Output,
		})
		results = append(results, ToolExecutionResult{
			ToolCall:      toolCall,
			Result:        result,
			CallSummary:   callSummary,
			ResultSummary: resultSummary,
		})
	}

	return messages, results
}
