package main

import (
	"context"
	"flag"
	"fmt"
	"os"

	"github.com/sagnikc395/kai/internal/api"
	"github.com/sagnikc395/kai/internal/ui"
)

const (
	defaultModel = "anthropic/claude-sonnet-4"
	version      = "1.0.0"
)

func main() {
	model := defaultModel
	showVersion := false

	flags := flag.NewFlagSet("kai", flag.ExitOnError)
	flags.StringVar(&model, "m", defaultModel, "model to use via OpenRouter")
	flags.StringVar(&model, "model", defaultModel, "model to use via OpenRouter")
	flags.BoolVar(&showVersion, "V", false, "print version")
	flags.BoolVar(&showVersion, "version", false, "print version")
	flags.Usage = func() {
		fmt.Fprintf(flags.Output(), "Usage: kai [options]\n\n")
		fmt.Fprintf(flags.Output(), "A simple coding assistant in your terminal.\n\n")
		fmt.Fprintf(flags.Output(), "Options:\n")
		flags.PrintDefaults()
	}

	if err := flags.Parse(os.Args[1:]); err != nil {
		os.Exit(2)
	}

	if showVersion {
		fmt.Println(version)
		return
	}

	apiKey := os.Getenv("OPENROUTER_API_KEY")
	if apiKey == "" {
		fmt.Fprintln(os.Stderr, "ERROR: OPENROUTER_API_KEY environment variable is required.")
		fmt.Fprintln(os.Stderr, "Set it with: export OPENROUTER_API_KEY=your_key_here")
		os.Exit(1)
	}

	client := api.NewOpenRouterClient(apiKey)
	if err := ui.RunREPL(context.Background(), client, model, os.Stdin, os.Stdout); err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: %v\n", err)
		os.Exit(1)
	}
}
