package tools

import "github.com/sagnikc395/kai/internal/api"

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

func Definitions() []api.ToolDefinition {
	definitions := make([]api.ToolDefinition, 0, len(All()))
	for _, tool := range All() {
		definitions = append(definitions, api.ToolDefinition{
			Type: "function",
			Function: api.ToolDefinitionFunction{
				Name:        tool.Name(),
				Description: tool.Description(),
				Parameters:  tool.Parameters(),
			},
		})
	}
	return definitions
}
