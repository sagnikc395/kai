package tools

import (
	"encoding/json"

	groqtools "github.com/conneroisu/groq-go/pkg/tools"
)

var registry = map[string]Tool{}

func init() {
	Register(BashTool{})
	Register(ReadTool{})
	Register(WriteTool{})
	Register(EditTool{})
	Register(GlobTool{})
	Register(GrepTool{})
}

func Register(tool Tool) {
	registry[tool.Name()] = tool
}

func Get(name string) (Tool, bool) {
	tool, ok := registry[name]
	return tool, ok
}

func All() []Tool {
	return []Tool{
		registry["bash"],
		registry["read"],
		registry["write"],
		registry["edit"],
		registry["glob"],
		registry["grep"],
	}
}

func Definitions() []groqtools.Tool {
	defs := make([]groqtools.Tool, 0, len(All()))
	for _, tool := range All() {
		defs = append(defs, groqtools.Tool{
			Type: groqtools.ToolTypeFunction,
			Function: groqtools.FunctionDefinition{
				Name:        tool.Name(),
				Description: tool.Description(),
				Parameters:  schemaToParams(tool.Parameters()),
			},
		})
	}
	return defs
}

func schemaToParams(schema map[string]any) groqtools.FunctionParameters {
	data, _ := json.Marshal(schema)
	var params groqtools.FunctionParameters
	_ = json.Unmarshal(data, &params)
	return params
}
