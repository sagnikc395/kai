package api

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
)

const openRouterBaseURL = "https://openrouter.ai/api/v1"

type OpenRouterClient struct {
	apiKey     string
	httpClient *http.Client
}

func NewOpenRouterClient(apiKey string) *OpenRouterClient {
	return &OpenRouterClient{
		apiKey:     apiKey,
		httpClient: http.DefaultClient,
	}
}

func (c *OpenRouterClient) StreamChatCompletion(ctx context.Context, request ChatCompletionRequest, onChunk func(ChatCompletionChunk) error) error {
	request.Stream = true

	body, err := json.Marshal(request)
	if err != nil {
		return err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, openRouterBaseURL+"/chat/completions", bytes.NewReader(body))
	if err != nil {
		return err
	}

	req.Header.Set("Authorization", "Bearer "+c.apiKey)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("HTTP-Referer", "https://github.com/sagnikc395/kai")
	req.Header.Set("X-Title", "kai")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		errorBody, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("OpenRouter API error (%d): %s", resp.StatusCode, strings.TrimSpace(string(errorBody)))
	}

	return parseSSEStream(resp.Body, onChunk)
}

func parseSSEStream(body io.Reader, onChunk func(ChatCompletionChunk) error) error {
	scanner := bufio.NewScanner(body)
	scanner.Buffer(make([]byte, 1024), 10*1024*1024)

	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if !strings.HasPrefix(line, "data: ") {
			continue
		}

		data := strings.TrimPrefix(line, "data: ")
		if data == "[DONE]" {
			return nil
		}

		var chunk ChatCompletionChunk
		if err := json.Unmarshal([]byte(data), &chunk); err != nil {
			continue
		}
		if err := onChunk(chunk); err != nil {
			return err
		}
	}

	return scanner.Err()
}
