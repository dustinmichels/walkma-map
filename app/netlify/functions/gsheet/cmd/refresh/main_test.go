package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"io/fs"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"strings"
	"testing"

	"hello/internal/audits"
)

type roundTripFunc func(*http.Request) (*http.Response, error)

func (f roundTripFunc) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }

func serveSheet(t *testing.T, body string, fetchErr error) {
	t.Helper()
	previous := http.DefaultClient
	http.DefaultClient = &http.Client{Transport: roundTripFunc(func(*http.Request) (*http.Response, error) {
		if fetchErr != nil {
			return nil, fetchErr
		}
		return &http.Response{
			StatusCode: http.StatusOK,
			Body:       io.NopCloser(strings.NewReader(body)),
			Header:     make(http.Header),
		}, nil
	})}
	t.Cleanup(func() { http.DefaultClient = previous })
}

const sheetHTML = "<table><tbody><tr><td>BOSTON</td><td></td><td>2026</td>" +
	"<td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td>" +
	"</tr></tbody></table>"

func fetchedAudits() []audits.WalkAudit {
	return []audits.WalkAudit{{CityTown: "BOSTON", City: "BOSTON", Year: "2026"}}
}

func putFile(t *testing.T, path string, contents []byte) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, contents, 0644); err != nil {
		t.Fatal(err)
	}
}

func putJSON(t *testing.T, path string, value any) {
	t.Helper()
	contents, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	putFile(t, path, contents)
}

func readTree(t *testing.T, root string) map[string]string {
	t.Helper()
	files := make(map[string]string)
	err := filepath.WalkDir(root, func(path string, entry fs.DirEntry, err error) error {
		if err != nil || entry.IsDir() {
			return err
		}
		contents, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		rel, err := filepath.Rel(root, path)
		files[rel] = string(contents)
		return err
	})
	if err != nil {
		t.Fatal(err)
	}
	return files
}

func seedRefresh(t *testing.T, root string, data []audits.WalkAudit) (string, string, string) {
	t.Helper()
	out := filepath.Join(root, "data", "audits.json")
	snap := filepath.Join(root, "public", "last_run.json")
	backups := filepath.Join(root, "data", "backups")
	putJSON(t, out, data)
	putJSON(t, snap, snapshot{Date: "2020-01-01T00:00:00Z", Data: data})
	for i := 1; i <= maxBackups; i++ {
		putJSON(t, filepath.Join(backups, fmt.Sprintf("last_run_2020010%dT000000Z.json", i)),
			snapshot{Date: fmt.Sprintf("2020-01-0%dT00:00:00Z", i), Data: data})
	}
	return out, snap, backups
}

func TestRefreshRejectedFetchPreservesFiles(t *testing.T) {
	for _, tc := range []struct {
		name string
		body string
		err  error
	}{
		{"download failure", "", errors.New("download failed")},
		{"empty sheet", "<table><tbody></tbody></table>", nil},
		{"unexpected markup", "<html>Sheet unavailable</html>", nil},
	} {
		t.Run(tc.name, func(t *testing.T) {
			root := t.TempDir()
			out, snap, backups := seedRefresh(t, root, fetchedAudits())
			before := readTree(t, root)
			serveSheet(t, tc.body, tc.err)
			if err := RefreshSavedData(out, snap, backups); err == nil {
				t.Fatal("expected refresh rejection")
			}
			if after := readTree(t, root); !reflect.DeepEqual(before, after) {
				t.Fatal("rejected refresh changed saved files or backups")
			}
		})
	}
}

func TestRefreshUnchangedPreservesHistory(t *testing.T) {
	root := t.TempDir()
	out, snap, backups := seedRefresh(t, root, fetchedAudits())
	before := readTree(t, root)
	serveSheet(t, sheetHTML, nil)
	if err := RefreshSavedData(out, snap, backups); err != nil {
		t.Fatal(err)
	}
	if after := readTree(t, root); !reflect.DeepEqual(before, after) {
		t.Fatal("unchanged refresh changed snapshot date or backup history")
	}

	// A matching snapshot must not hide an out-of-sync embedded fallback.
	putJSON(t, out, []audits.WalkAudit{{City: "OLD"}})
	if err := RefreshSavedData(out, snap, backups); err != nil {
		t.Fatal(err)
	}
	if after := readTree(t, root); !reflect.DeepEqual(before, after) {
		t.Fatal("refresh failed to repair the embedded fallback without rotating history")
	}
}

func TestRefreshChangedReplacesBothAndPrunes(t *testing.T) {
	root := t.TempDir()
	out, snap, backups := seedRefresh(t, root, []audits.WalkAudit{{City: "OLD"}})
	before := readTree(t, root)
	serveSheet(t, sheetHTML, nil)
	if err := RefreshSavedData(out, snap, backups); err != nil {
		t.Fatal(err)
	}
	contents, err := os.ReadFile(out)
	if err != nil {
		t.Fatal(err)
	}
	var data []audits.WalkAudit
	if err := json.Unmarshal(contents, &data); err != nil || !reflect.DeepEqual(data, fetchedAudits()) {
		t.Fatalf("embedded fallback has incorrect data: %s (%v)", contents, err)
	}
	contents, err = os.ReadFile(snap)
	if err != nil {
		t.Fatal(err)
	}
	var saved snapshot
	if err := json.Unmarshal(contents, &saved); err != nil || !reflect.DeepEqual(saved.Data, data) || saved.Date == "2020-01-01T00:00:00Z" {
		t.Fatalf("snapshot was not refreshed consistently: %s (%v)", contents, err)
	}
	history := readTree(t, backups)
	if len(history) != maxBackups {
		t.Fatalf("got %d backups, want %d", len(history), maxBackups)
	}
	if _, exists := history["last_run_20200101T000000Z.json"]; exists {
		t.Fatal("oldest backup was not pruned")
	}
	foundPrevious := false
	for name, contents := range history {
		if !strings.HasPrefix(name, "last_run_2020010") && contents == before[filepath.Join("public", "last_run.json")] {
			foundPrevious = true
		}
	}
	if !foundPrevious {
		t.Fatal("previous snapshot was not preserved byte-for-byte")
	}
	for path := range readTree(t, root) {
		if strings.HasPrefix(filepath.Base(path), ".refresh-") {
			t.Fatalf("temporary file left behind: %s", path)
		}
	}
}

func TestRefreshStagingFailurePreservesFiles(t *testing.T) {
	root := t.TempDir()
	out, _, backups := seedRefresh(t, root, []audits.WalkAudit{{City: "OLD"}})
	before := readTree(t, root)
	serveSheet(t, sheetHTML, nil)
	// A path below an existing file cannot be staged. No destination or backup
	// may change when a replacement cannot be prepared.
	if err := RefreshSavedData(out, filepath.Join(out, "last_run.json"), backups); err == nil {
		t.Fatal("expected invalid destination to fail")
	}
	if after := readTree(t, root); !reflect.DeepEqual(before, after) {
		t.Fatal("failed preparation changed saved files or backups")
	}
}

func TestRefreshBackupFailureCleansStagedFiles(t *testing.T) {
	root := t.TempDir()
	out, snap, _ := seedRefresh(t, root, []audits.WalkAudit{{City: "OLD"}})
	before := readTree(t, root)
	serveSheet(t, sheetHTML, nil)
	if err := RefreshSavedData(out, snap, out); err == nil {
		t.Fatal("expected backup creation at a file path to fail")
	}
	if after := readTree(t, root); !reflect.DeepEqual(before, after) {
		t.Fatal("backup failure changed fallbacks or left staged files behind")
	}
}

func TestRefreshCommand(t *testing.T) {
	if os.Getenv("REFRESH_CLI_TEST") == "1" {
		serveSheet(t, sheetHTML, nil)
		flag.CommandLine = flag.NewFlagSet("refresh", flag.ExitOnError)
		os.Args = []string{"refresh", "--out", "data/audits.json", "--snapshot", "public/last_run.json", "--backup-dir", "data/backups"}
		main()
		return
	}
	root := filepath.Join(t.TempDir(), "repo with ' quote")
	_, _, backups := seedRefresh(t, root, []audits.WalkAudit{{City: "OLD"}})
	runGit := func(args ...string) string {
		t.Helper()
		cmd := exec.Command("git", append([]string{"-C", root}, args...)...)
		output, err := cmd.CombinedOutput()
		if err != nil {
			t.Fatalf("git %v: %v\n%s", args, err, output)
		}
		return string(output)
	}
	runGit("init", "--quiet")
	runGit("add", ".")
	// A local index baseline is enough to check staging deletions; no commit or
	// user Git identity is needed.
	executable, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	cmd := exec.Command(executable, "-test.run=^TestRefreshCommand$")
	cmd.Dir = root
	cmd.Env = append(os.Environ(), "REFRESH_CLI_TEST=1")
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("refresh CLI failed: %v\n%s", err, output)
	}
	t.Logf("CLI output:\n%s", output)
	var staging string
	for _, line := range strings.Split(string(output), "\n") {
		if strings.HasPrefix(line, "  git ") {
			staging = strings.TrimSpace(line)
		}
	}
	if staging == "" {
		t.Fatalf("missing staging command in CLI output:\n%s", output)
	}
	cmd = exec.Command("sh", "-c", staging)
	cmd.Dir = t.TempDir() // The printed command must work outside the function directory.
	if output, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("printed staging command failed: %v\n%s", err, output)
	}
	if diff := runGit("diff", "--name-only"); diff != "" {
		t.Fatalf("refresh left unstaged changes: %s", diff)
	}
	if files := runGit("ls-files"); strings.Contains(files, "last_run_20200101T000000Z.json") {
		t.Fatal("printed command did not stage the rotated backup deletion")
	}
	for path := range readTree(t, backups) {
		if !strings.Contains(runGit("ls-files"), filepath.ToSlash(filepath.Join("data", "backups", path))) {
			t.Fatalf("backup was not staged: %s", path)
		}
	}
	indexSnapshot := runGit("show", ":public/last_run.json")
	contents, err := os.ReadFile(filepath.Join(root, "public", "last_run.json"))
	if err != nil || !bytes.Equal([]byte(indexSnapshot), contents) {
		t.Fatal("printed command did not stage the refreshed snapshot")
	}
}
