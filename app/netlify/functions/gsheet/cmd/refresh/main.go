// refresh is a CLI tool to update the saved audit data file.
//
// Run from the netlify/functions/gsheet/ directory:
//
//	go run ./cmd/refresh
//
// This fetches the latest data from the live Google Sheet and writes it to:
//
//	data/audits.json
//
// That file is embedded into the Lambda binary at build time and used as a
// fallback when the live fetch fails, or when USE_SAVED_AUDIT_DATA is set.
// Commit the file after running to keep the fallback current.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"

	"hello/internal/audits"
)

// RefreshSavedData fetches the latest walk audit data from the live Google Sheet
// and writes it as JSON to outputPath.
func RefreshSavedData(outputPath string) error {
	fmt.Println("Fetching walk audit data from Google Sheet...")

	data, err := audits.FetchWalkAudits()
	if err != nil {
		return fmt.Errorf("fetch failed: %w", err)
	}

	fmt.Printf("Fetched %d audit records\n", len(data))

	jsonBytes, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return fmt.Errorf("JSON encoding failed: %w", err)
	}

	if err := os.MkdirAll(filepath.Dir(outputPath), 0755); err != nil {
		return fmt.Errorf("failed to create directory for %s: %w", outputPath, err)
	}
	if err := os.WriteFile(outputPath, jsonBytes, 0644); err != nil {
		return fmt.Errorf("failed to write %s: %w", outputPath, err)
	}

	fmt.Printf("Wrote %s\n", outputPath)
	return nil
}

func main() {
	// Default path assumes this is run from the netlify/functions/gsheet/ directory.
	out := flag.String(
		"out",
		"data/audits.json",
		"output path for the embedded fallback data file",
	)
	flag.Parse()

	if err := RefreshSavedData(*out); err != nil {
		log.Fatalf("Error: %v", err)
	}

	fmt.Println("\nDone. Commit the file to keep the embedded fallback current:")
	fmt.Printf("  git add %s\n", *out)
}
