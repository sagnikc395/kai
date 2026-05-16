package main

import (
	"context"
	"fmt"
	"os"

	"github.com/sagnikc395/kai/internal/app"
)

func main() {
	if err := app.Run(context.Background(), os.Args[1:], os.Stdin, os.Stdout, os.Stderr); err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: %v\n", err)
		os.Exit(1)
	}
}
