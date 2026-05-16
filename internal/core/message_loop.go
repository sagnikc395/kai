package core

import (
	"context"

	"github.com/sagnikc395/kai/internal/api"
	"github.com/sagnikc395/kai/internal/tools"
)

type MessageLoopCallbacks struct {
	OnToken      func(token string)
	OnToolStart  func(toolCalls []api.ToolCall)
	OnToolResult func(results []ToolExecutionResult)
	OnComplete   func(text string)
	OnError      func(err error)
}

type toolCallAccumulator struct {
	id        string
	name      string
	arguments string
}

func RunMessageLoop(ctx context.Context, client *api.OpenRouterClient, messages []api.ChatMessage, model string, callbacks MessageLoopCallbacks) []api.ChatMessage {
	systemMessage := api.ChatMessage{
		Role:    "system",
		Content: api.StringPtr(BuildSystemPrompt()),
	}

	toolDefinitions := tools.Definitions()
	continueLoop := true

	for continueLoop {
		assistantText := ""
		toolCallDeltas := map[int]*toolCallAccumulator{}
		finishReason := ""

		requestMessages := make([]api.ChatMessage, 0, len(messages)+1)
		requestMessages = append(requestMessages, systemMessage)
		requestMessages = append(requestMessages, messages...)

		err := client.StreamChatCompletion(ctx, api.ChatCompletionRequest{
			Model:    model,
			Messages: requestMessages,
			Tools:    toolDefinitions,
		}, func(chunk api.ChatCompletionChunk) error {
			if len(chunk.Choices) == 0 {
				return nil
			}

			choice := chunk.Choices[0]
			if choice.Delta.Content != nil && *choice.Delta.Content != "" {
				assistantText += *choice.Delta.Content
				if callbacks.OnToken != nil {
					callbacks.OnToken(*choice.Delta.Content)
				}
			}

			for _, delta := range choice.Delta.ToolCalls {
				accumulateToolCallDelta(toolCallDeltas, delta)
			}

			if choice.FinishReason != "" {
				finishReason = choice.FinishReason
			}
			return nil
		})

		if err != nil {
			if callbacks.OnError != nil {
				callbacks.OnError(err)
			}
			return messages
		}

		toolCalls := buildToolCalls(toolCallDeltas)
		if finishReason == "tool_calls" || (len(toolCalls) > 0 && finishReason != "stop") {
			messages = append(messages, api.ChatMessage{
				Role:      "assistant",
				Content:   nullableContent(assistantText),
				ToolCalls: toolCalls,
			})

			if callbacks.OnToolStart != nil {
				callbacks.OnToolStart(toolCalls)
			}

			toolMessages, results := ExecuteToolCalls(toolCalls)
			messages = append(messages, toolMessages...)

			if callbacks.OnToolResult != nil {
				callbacks.OnToolResult(results)
			}
			continue
		}

		if assistantText != "" {
			messages = append(messages, api.ChatMessage{
				Role:    "assistant",
				Content: api.StringPtr(assistantText),
			})
		}
		if callbacks.OnComplete != nil {
			callbacks.OnComplete(assistantText)
		}
		continueLoop = false
	}

	return messages
}

func accumulateToolCallDelta(accumulator map[int]*toolCallAccumulator, delta api.ToolCallDelta) {
	existing, ok := accumulator[delta.Index]
	if !ok {
		existing = &toolCallAccumulator{}
		accumulator[delta.Index] = existing
	}
	if delta.ID != "" {
		existing.id = delta.ID
	}
	if delta.Function != nil {
		if delta.Function.Name != "" {
			existing.name = delta.Function.Name
		}
		if delta.Function.Arguments != "" {
			existing.arguments += delta.Function.Arguments
		}
	}
}

func buildToolCalls(accumulator map[int]*toolCallAccumulator) []api.ToolCall {
	toolCalls := make([]api.ToolCall, 0, len(accumulator))
	for index := 0; index < len(accumulator); index++ {
		accumulated, ok := accumulator[index]
		if !ok {
			continue
		}
		toolCalls = append(toolCalls, api.ToolCall{
			ID:   accumulated.id,
			Type: "function",
			Function: api.FunctionCall{
				Name:      accumulated.name,
				Arguments: accumulated.arguments,
			},
		})
	}
	return toolCalls
}

func nullableContent(text string) *string {
	if text == "" {
		return nil
	}
	return api.StringPtr(text)
}
