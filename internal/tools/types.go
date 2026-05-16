package tools

import "fmt"

type Result struct {
	Output  string
	IsError bool
}

type Tool interface {
	Name() string
	Description() string
	Parameters() map[string]any
	Call(input map[string]any) Result
	RenderToolCall(input map[string]any) string
	RenderResult(result Result) string
}

func stringArg(input map[string]any, name string) (string, error) {
	value, ok := input[name]
	if !ok {
		return "", fmt.Errorf("missing required argument %q", name)
	}
	text, ok := value.(string)
	if !ok {
		return "", fmt.Errorf("argument %q must be a string", name)
	}
	return text, nil
}

func optionalStringArg(input map[string]any, name string) (string, bool, error) {
	value, ok := input[name]
	if !ok || value == nil {
		return "", false, nil
	}
	text, ok := value.(string)
	if !ok {
		return "", false, fmt.Errorf("argument %q must be a string", name)
	}
	return text, true, nil
}

func optionalNumberArg(input map[string]any, name string, fallback int) (int, error) {
	value, ok := input[name]
	if !ok || value == nil {
		return fallback, nil
	}
	switch v := value.(type) {
	case float64:
		return int(v), nil
	case int:
		return v, nil
	default:
		return 0, fmt.Errorf("argument %q must be a number", name)
	}
}

func optionalBoolArg(input map[string]any, name string, fallback bool) (bool, error) {
	value, ok := input[name]
	if !ok || value == nil {
		return fallback, nil
	}
	boolean, ok := value.(bool)
	if !ok {
		return false, fmt.Errorf("argument %q must be a boolean", name)
	}
	return boolean, nil
}

func objectSchema(required []string, properties map[string]any) map[string]any {
	return map[string]any{
		"type":                 "object",
		"properties":           properties,
		"required":             required,
		"additionalProperties": false,
	}
}

func stringSchema(description string) map[string]any {
	return map[string]any{"type": "string", "description": description}
}

func numberSchema(description string) map[string]any {
	return map[string]any{"type": "number", "description": description}
}

func boolSchema(description string) map[string]any {
	return map[string]any{"type": "boolean", "description": description}
}
