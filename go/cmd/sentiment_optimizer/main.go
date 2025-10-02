package main

import (
	"encoding/json"
	"fmt"
	"os"

	"tradingai/go/pkg/optimizer"
)

func main() {
	decoder := json.NewDecoder(os.Stdin)
	var input optimizer.Input
	if err := decoder.Decode(&input); err != nil {
		fmt.Fprintf(os.Stderr, "failed to decode input: %v\n", err)
		os.Exit(1)
	}

	output := optimizer.Optimize(input)
	encoder := json.NewEncoder(os.Stdout)
	encoder.SetEscapeHTML(false)
	if err := encoder.Encode(output); err != nil {
		fmt.Fprintf(os.Stderr, "failed to encode output: %v\n", err)
		os.Exit(1)
	}
}
