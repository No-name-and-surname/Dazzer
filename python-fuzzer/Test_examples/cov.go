package main

import (
	"bufio"
	"os"
	"strings"
)

func processInput(input string) string {
	input = strings.TrimSpace(input)
	if input == "" {
		return "empty"
	}

	if len(input) < 5 {
		return "short"
	}

	if strings.Contains(input, "crash") {
		if input == "crashnow" {
			panic("simulated panic")
		}
		return "crash_detected"
	}

	hasNumber := false
	for _, char := range input {
		if char >= '0' && char <= '9' {
			hasNumber = true
			break
		}
	}
	if hasNumber {
		return "numeric"
	}

	if len(input) > 20 {
		return "long"
	}
	return "normal"
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	if scanner.Scan() {
		input := scanner.Text()
		result := processInput(input)
		os.Stdout.WriteString(result + "\n")
	}
}