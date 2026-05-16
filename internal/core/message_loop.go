package core

import (
	"context"
	"io"

	groq "github.com/conneroisu/groq-go"
	groqtools "github.com/conneroisu/groq-go/pkg/tools"
	"github.com/sagnikc395/kai/internal/tools"
)

type MessageLoopCallbacks struct {
	OnToken      func(token string)
	OnToolStart  func(toolCalls []groqtools.ToolCall)
	OnToolResult func(results []ToolExecutionResult)
	OnComplete   func(text string)
	OnError      func(err error)
}

type toolCallAccumulator struct {
	id        string
	name      string
	arguments string
}

func RunMessageLoop(ctx context.Context, client *groq.Client, messages []groq.ChatCompletionMessage, model groq.ChatModel, callbacks MessageLoopCallbacks) []groq.ChatCompletionMessage {
	systemMessage := groq.ChatCompletionMessage{
		Role:    groq.RoleSystem,
		Content: BuildSystemPrompt(),
	}

	toolDefinitions := tools.Definitions()
	continueLoop := true

	for continueLoop {
		assistantText := ""
		accumulated := map[int]*toolCallAccumulator{}
		finishReason := groq.FinishReason("")

		requestMessages := make([]groq.ChatCompletionMessage, 0, len(messages)+1)
		requestMessages = append(requestMessages, systemMessage)
		requestMessages = append(requestMessages, messages...)

		stream, err := client.ChatCompletionStream(ctx, groq.ChatCompletionRequest{
			Model:    model,
			Messages: requestMessages,
			Tools:    toolDefinitions,
		})
		if err != nil {
			if callbacks.OnError != nil {
				callbacks.OnError(err)
			}
			return messages
		}

		for {
			chunk, err := stream.Recv()
			if err == io.EOF {
				break
			}
			if err != nil {
				stream.Close()
				if callbacks.OnError != nil {
					callbacks.OnError(err)
				}
				return messages
			}
			if chunk == nil || len(chunk.Choices) == 0 {
				continue
			}

			choice := chunk.Choices[0]
			if choice.Delta.Content != "" {
				assistantText += choice.Delta.Content
				if callbacks.OnToken != nil {
					callbacks.OnToken(choice.Delta.Content)
				}
			}

			for _, delta := range choice.Delta.ToolCalls {
				if delta.Index != nil {
					accumulateToolCallDelta(accumulated, delta)
				}
			}

			if choice.FinishReason != "" {
				finishReason = choice.FinishReason
			}
		}
		stream.Close()

		toolCalls := buildToolCalls(accumulated)
		if finishReason == groq.ReasonToolCalls || (len(toolCalls) > 0 && finishReason != groq.ReasonStop) {
			messages = append(messages, groq.ChatCompletionMessage{
				Role:      groq.RoleAssistant,
				Content:   assistantText,
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
			messages = append(messages, groq.ChatCompletionMessage{
				Role:    groq.RoleAssistant,
				Content: assistantText,
			})
		}
		if callbacks.OnComplete != nil {
			callbacks.OnComplete(assistantText)
		}
		continueLoop = false
	}

	return messages
}

func accumulateToolCallDelta(acc map[int]*toolCallAccumulator, delta groqtools.ToolCall) {
	idx := *delta.Index
	existing, ok := acc[idx]
	if !ok {
		existing = &toolCallAccumulator{}
		acc[idx] = existing
	}
	if delta.ID != "" {
		existing.id = delta.ID
	}
	if delta.Function.Name != "" {
		existing.name = delta.Function.Name
	}
	if delta.Function.Arguments != "" {
		existing.arguments += delta.Function.Arguments
	}
}

func buildToolCalls(acc map[int]*toolCallAccumulator) []groqtools.ToolCall {
	toolCalls := make([]groqtools.ToolCall, 0, len(acc))
	for index := 0; index < len(acc); index++ {
		a, ok := acc[index]
		if !ok {
			continue
		}
		toolCalls = append(toolCalls, groqtools.ToolCall{
			ID:   a.id,
			Type: string(groqtools.ToolTypeFunction),
			Function: groqtools.FunctionCall{
				Name:      a.name,
				Arguments: a.arguments,
			},
		})
	}
	return toolCalls
}
