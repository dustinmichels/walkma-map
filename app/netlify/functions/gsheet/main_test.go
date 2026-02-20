package main

import (
	"strings"
	"testing"

	"hello/internal/audits"
)

func TestFetchWalkAudits(t *testing.T) {
	data, err := audits.FetchWalkAudits()
	if err != nil {
		t.Fatalf("FetchWalkAudits failed: %v", err)
	}

	if len(data) == 0 {
		t.Fatal("Expected at least one walk audit, got none")
	}

	t.Logf("Fetched %d audits", len(data))
	t.Logf("First audit: %+v", data[0])

	if len(data) > 0 {
		if data[0].View != "" && !strings.HasPrefix(data[0].View, "http") {
			t.Errorf("Expected View to be a link starting with http, got: %s", data[0].View)
		}
	}
}
