package app

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"

	groq "github.com/conneroisu/groq-go"
	"github.com/joho/godotenv"
	"github.com/sagnikc395/kai/internal/tui"
)

const Version = "2.0.0"

var defaultModel = groq.ModelLlama3370BVersatile

func Run(ctx context.Context, args []string, input io.Reader, output io.Writer, errOutput io.Writer) error {
	_ = godotenv.Load()

	modelStr := string(defaultModel)
	showVersion := false

	flags := flag.NewFlagSet("kai", flag.ContinueOnError)
	flags.SetOutput(errOutput)
	flags.StringVar(&modelStr, "m", modelStr, "model to use via Groq")
	flags.StringVar(&modelStr, "model", modelStr, "model to use via Groq")
	flags.BoolVar(&showVersion, "V", false, "print version")
	flags.BoolVar(&showVersion, "version", false, "print version")
	flags.Usage = func() {
		fmt.Fprintf(flags.Output(), "Usage: kai [options]\n\n")
		fmt.Fprintf(flags.Output(), "A Bubble Tea-powered coding assistant in your terminal.\n\n")
		fmt.Fprintf(flags.Output(), "Options:\n")
		flags.PrintDefaults()
	}

	if err := flags.Parse(args); err != nil {
		if errors.Is(err, flag.ErrHelp) {
			return nil
		}
		return err
	}

	if showVersion {
		fmt.Fprintln(output, Version)
		return nil
	}

	apiKey := os.Getenv("GROQ_API_KEY")
	if apiKey == "" {
		return fmt.Errorf("GROQ_API_KEY environment variable is required")
	}

	client, err := groq.NewClient(apiKey)
	if err != nil {
		return err
	}

	return tui.Run(ctx, client, groq.ChatModel(modelStr), input, output)
}
