package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"

	groq "github.com/conneroisu/groq-go"
	"github.com/joho/godotenv"
	"github.com/sagnikc395/kai/internal/ui"
)

const version = "2.0.0"

var defaultModel = groq.ModelLlama3370BVersatile

func main() {
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Error loading .env file")
	}

	modelStr := string(defaultModel)
	showVersion := false

	flags := flag.NewFlagSet("kai", flag.ExitOnError)
	flags.StringVar(&modelStr, "m", modelStr, "model to use via Groq")
	flags.StringVar(&modelStr, "model", modelStr, "model to use via Groq")
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

	apiKey := os.Getenv("GROQ_API_KEY")
	if apiKey == "" {
		fmt.Fprintln(os.Stderr, "ERROR: GROQ_API_KEY environment variable is required.")
		os.Exit(1)
	}

	client, err := groq.NewClient(apiKey)
	if err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: %v\n", err)
		os.Exit(1)
	}

	if err := ui.RunREPL(context.Background(), client, groq.ChatModel(modelStr), os.Stdin, os.Stdout); err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: %v\n", err)
		os.Exit(1)
	}
}
