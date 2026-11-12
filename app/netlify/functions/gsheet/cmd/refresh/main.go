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
// Before overwriting, the previous snapshot is copied to
// data/backups/last_run_<UTC time>.json; only the newest 5 backups are kept.
//
// Commit both files after running to keep the fallbacks current.
package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io/fs"
	"log"
	"os"
	"path/filepath"
	"slices"
	"sort"
	"strings"
	"time"

	"hello/internal/audits"
)

// maxBackups is how many previous snapshots are kept in the backup directory.
const maxBackups = 5

// snapshot is the shape of last_run.json read by the frontend.
type snapshot struct {
	Date string             `json:"date"`
	Data []audits.WalkAudit `json:"data"`
}

// stageJSON prepares a replacement beside its destination so rename is atomic.
// An empty path means the destination already has the requested contents.
func stageJSON(path string, v any) (string, error) {
	jsonBytes, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return "", fmt.Errorf("JSON encoding failed: %w", err)
	}
	existing, err := os.ReadFile(path)
	if err == nil && bytes.Equal(existing, jsonBytes) {
		return "", nil
	}
	if err != nil && !errors.Is(err, fs.ErrNotExist) {
		return "", fmt.Errorf("failed to read %s: %w", path, err)
	}
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		return "", fmt.Errorf("failed to create directory for %s: %w", path, err)
	}
	f, err := os.CreateTemp(filepath.Dir(path), ".refresh-*.json")
	if err != nil {
		return "", err
	}
	ready := false
	defer func() {
		if !ready {
			os.Remove(f.Name())
		}
	}()
	if err = f.Chmod(0644); err == nil {
		_, err = f.Write(jsonBytes)
	}
	closeErr := f.Close()
	if err != nil {
		return "", err
	}
	if closeErr != nil {
		return "", closeErr
	}
	ready = true
	return f.Name(), nil
}

// backupSnapshot copies the existing snapshot without pruning older backups.
// A missing snapshot is not an error: there is nothing to back up.
func backupSnapshot(snapshotPath, backupDir string) error {
	existing, err := os.ReadFile(snapshotPath)
	if errors.Is(err, fs.ErrNotExist) {
		return nil
	}
	if err != nil {
		return fmt.Errorf("failed to read %s for backup: %w", snapshotPath, err)
	}
	if err := os.MkdirAll(backupDir, 0755); err != nil {
		return fmt.Errorf("failed to create backup directory %s: %w", backupDir, err)
	}

	// Compact UTC timestamps sort lexically in chronological order.
	name := "last_run_" + time.Now().UTC().Format("20060102T150405Z") + ".json"
	backupPath := filepath.Join(backupDir, name)
	if err := os.WriteFile(backupPath, existing, 0644); err != nil {
		return fmt.Errorf("failed to write backup %s: %w", backupPath, err)
	}
	fmt.Printf("Backed up previous snapshot to %s\n", backupPath)
	return nil
}

// pruneBackups runs only after both fallback replacements succeed.
func pruneBackups(backupDir string) error {
	backups, err := filepath.Glob(filepath.Join(backupDir, "last_run_*.json"))
	if err != nil {
		return fmt.Errorf("failed to list backups: %w", err)
	}
	if len(backups) <= maxBackups {
		return nil
	}
	sort.Strings(backups)
	for _, old := range backups[:len(backups)-maxBackups] {
		if err := os.Remove(old); err != nil {
			return fmt.Errorf("failed to delete old backup %s: %w", old, err)
		}
		fmt.Printf("Deleted old backup %s\n", old)
	}
	return nil
}

// RefreshSavedData fetches the latest walk audit data from the live Google Sheet
// and writes it to outputPath and, if non-empty, a timestamped snapshot to
// snapshotPath, backing up the previous snapshot into backupDir first.
func RefreshSavedData(outputPath, snapshotPath, backupDir string) error {
	fmt.Println("Fetching walk audit data from Google Sheet...")

	data, err := audits.FetchWalkAudits()
	if err != nil {
		return fmt.Errorf("fetch failed: %w", err)
	}

	fmt.Printf("Fetched %d audit records\n", len(data))
	if len(data) == 0 {
		return errors.New("refusing to replace saved data with zero audits")
	}

	snapshotChanged := snapshotPath != ""
	if snapshotChanged {
		existing, err := os.ReadFile(snapshotPath)
		if err != nil && !errors.Is(err, fs.ErrNotExist) {
			return fmt.Errorf("failed to read snapshot: %w", err)
		}
		if err == nil {
			var previous snapshot
			if err := json.Unmarshal(existing, &previous); err != nil {
				return fmt.Errorf("failed to decode existing snapshot: %w", err)
			}
			snapshotChanged = !slices.Equal(previous.Data, data)
		}
	}

	// Stage every replacement before making a backup or changing either fallback.
	outputTemp, err := stageJSON(outputPath, data)
	if err != nil {
		return err
	}
	if outputTemp != "" {
		defer os.Remove(outputTemp)
	}
	var snapshotTemp string
	if snapshotChanged {
		snapshotTemp, err = stageJSON(snapshotPath, snapshot{
			Date: time.Now().UTC().Format(time.RFC3339),
			Data: data,
		})
		if err != nil {
			return err
		}
		if snapshotTemp != "" {
			defer os.Remove(snapshotTemp)
		}
		if err := backupSnapshot(snapshotPath, backupDir); err != nil {
			return err
		}
	}

	// Each rename is atomic, but the pair is not a cross-file transaction.
	for _, replacement := range []struct{ temp, path string }{
		{outputTemp, outputPath}, {snapshotTemp, snapshotPath},
	} {
		if replacement.temp == "" {
			continue
		}
		if err := os.Rename(replacement.temp, replacement.path); err != nil {
			return fmt.Errorf("failed to replace %s: %w", replacement.path, err)
		}
		fmt.Printf("Wrote %s\n", replacement.path)
	}
	if snapshotChanged {
		return pruneBackups(backupDir)
	}
	fmt.Println("Snapshot and backups unchanged.")
	return nil
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
	backupDir := flag.String(
		"backup-dir",
		"data/backups",
		fmt.Sprintf("directory for copies of the previous snapshot (newest %d kept)", maxBackups),
	)
	flag.Parse()

	if err := RefreshSavedData(*out, *snap, *backupDir); err != nil {
		log.Fatalf("Error: %v", err)
	}

	cwd, err := os.Getwd()
	if err != nil {
		log.Fatal(err)
	}
	quote := func(s string) string {
		return "'" + strings.ReplaceAll(s, "'", "'\\''") + "'"
	}
	fmt.Println("\nDone. Commit the files to keep the fallbacks current:")
	fmt.Printf("  git -C %s add -- %s", quote(cwd), quote(*out))
	if *snap != "" {
		fmt.Printf(" %s", quote(*snap))
		// No backup directory exists on a first run or an unchanged refresh.
		if _, err := os.Stat(*backupDir); err == nil {
			fmt.Printf(" %s", quote(*backupDir))
		}
	}
	fmt.Println()
}
