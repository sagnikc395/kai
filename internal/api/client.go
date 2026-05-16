package api

import groq "github.com/conneroisu/groq-go"

func NewClient(apiKey string) (*groq.Client, error) {
	return groq.NewClient(apiKey)
}
