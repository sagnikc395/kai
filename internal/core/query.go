package core

import (
	"context"

	"github.com/sagnikc395/kai/internal/api"
)

type Conversation struct {
	messages []api.ChatMessage
	client   *api.OpenRouterClient
	model    string
}

func NewConversation(client *api.OpenRouterClient, model string) *Conversation {
	return &Conversation{
		client: client,
		model:  model,
	}
}

func (c *Conversation) Send(ctx context.Context, userMessage string, callbacks MessageLoopCallbacks) {
	c.messages = append(c.messages, api.ChatMessage{
		Role:    "user",
		Content: api.StringPtr(userMessage),
	})
	c.messages = RunMessageLoop(ctx, c.client, c.messages, c.model, callbacks)
}

func (c *Conversation) Messages() []api.ChatMessage {
	messages := make([]api.ChatMessage, len(c.messages))
	copy(messages, c.messages)
	return messages
}
