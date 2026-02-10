package main

import (
	"strings"
	"testing"
)

func TestFetchWalkAudits(t *testing.T) {
	audits, err := FetchWalkAudits()
	if err != nil {
		t.Fatalf("FetchWalkAudits failed: %v", err)
	}

	if len(audits) == 0 {
		t.Fatal("Expected at least one walk audit, got none")
	}

	// Optional: Print the first audit to see some data
	t.Logf("Fetched %d audits", len(audits))
	t.Logf("First audit: %+v", audits[0])

	if len(audits) > 0 {
		if audits[0].View != "" && !strings.HasPrefix(audits[0].View, "http") {
			t.Errorf("Expected View to be a link starting with http, got: %s", audits[0].View)
		}
	}
}
