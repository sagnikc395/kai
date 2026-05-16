package core

import (
	"context"

	groq "github.com/conneroisu/groq-go"
)

type Conversation struct {
	messages []groq.ChatCompletionMessage
	client   *groq.Client
	model    groq.ChatModel
}

func NewConversation(client *groq.Client, model groq.ChatModel) *Conversation {
	return &Conversation{
		client: client,
		model:  model,
	}
}

func (c *Conversation) Send(ctx context.Context, userMessage string, callbacks MessageLoopCallbacks) {
	c.messages = append(c.messages, groq.ChatCompletionMessage{
		Role:    groq.RoleUser,
		Content: userMessage,
	})
	c.messages = RunMessageLoop(ctx, c.client, c.messages, c.model, callbacks)
}

func (c *Conversation) Messages() []groq.ChatCompletionMessage {
	messages := make([]groq.ChatCompletionMessage, len(c.messages))
	copy(messages, c.messages)
	return messages
}
