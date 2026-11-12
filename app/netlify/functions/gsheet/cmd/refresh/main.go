// refresh is a CLI tool to update the saved audit data files.
//
// Run from the netlify/functions/gsheet/ directory:
//
//	go run ./cmd/refresh
//
// This fetches the latest data from the live Google Sheet and writes:
//
//	data/audits.json                       embedded into the function binary;
//	                                       served when the live fetch fails or
//	                                       DISABLE_LIVE_UPDATE is set
//	../../../public/data/last_run.json     {date, data} snapshot the frontend
//	                                       loads when the function is unreachable
//
// Commit both files after running to keep the fallbacks current.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"

	"hello/internal/audits"
)

// snapshot is the shape of last_run.json read by the frontend.
type snapshot struct {
	Date string             `json:"date"`
	Data []audits.WalkAudit `json:"data"`
}

func writeJSON(path string, v any) error {
	jsonBytes, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return fmt.Errorf("JSON encoding failed: %w", err)
	}
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		return fmt.Errorf("failed to create directory for %s: %w", path, err)
	}
	if err := os.WriteFile(path, jsonBytes, 0644); err != nil {
		return fmt.Errorf("failed to write %s: %w", path, err)
	}
	fmt.Printf("Wrote %s\n", path)
	return nil
}

// RefreshSavedData fetches the latest walk audit data from the live Google Sheet
// and writes it to outputPath and, if non-empty, a timestamped snapshot to snapshotPath.
func RefreshSavedData(outputPath, snapshotPath string) error {
	fmt.Println("Fetching walk audit data from Google Sheet...")

	data, err := audits.FetchWalkAudits()
	if err != nil {
		return fmt.Errorf("fetch failed: %w", err)
	}

	fmt.Printf("Fetched %d audit records\n", len(data))

	if err := writeJSON(outputPath, data); err != nil {
		return err
	}
	if snapshotPath == "" {
		return nil
	}
	return writeJSON(snapshotPath, snapshot{
		Date: time.Now().UTC().Format(time.RFC3339),
		Data: data,
	})
}

func main() {
	// Default paths assume this is run from the netlify/functions/gsheet/ directory.
	out := flag.String(
		"out",
		"data/audits.json",
		"output path for the embedded fallback data file",
	)
	snap := flag.String(
		"snapshot",
		"../../../public/data/last_run.json",
		"output path for the frontend fallback snapshot (empty to skip)",
	)
	flag.Parse()

	if err := RefreshSavedData(*out, *snap); err != nil {
		log.Fatalf("Error: %v", err)
	}

	fmt.Println("\nDone. Commit the files to keep the fallbacks current:")
	fmt.Printf("  git add %s", *out)
	if *snap != "" {
		fmt.Printf(" %s", *snap)
	}
	fmt.Println()
}
