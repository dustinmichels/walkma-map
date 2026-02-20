package main

import (
	"testing"

	"hello/internal/audits"
)

func TestParseCity(t *testing.T) {
	tests := []struct {
		input        string
		wantCityTown string
		wantCity     string
	}{
		{"Boston", "BOSTON", "BOSTON"},
		{"Boston (Dorchester)", "BOSTON (DORCHESTER)", "BOSTON"},
		{" Somerville ", "SOMERVILLE", "SOMERVILLE"},
		{"Cambridge(North)", "CAMBRIDGE(NORTH)", "CAMBRIDGE"},
		{" Medford  ( Hillside ) ", "MEDFORD  ( HILLSIDE )", "MEDFORD"},
	}

	for _, tt := range tests {
		gotCityTown, gotCity := audits.ParseCity(tt.input)
		if gotCityTown != tt.wantCityTown {
			t.Errorf("ParseCity(%q) cityTown = %q, want %q", tt.input, gotCityTown, tt.wantCityTown)
		}
		if gotCity != tt.wantCity {
			t.Errorf("ParseCity(%q) city = %q, want %q", tt.input, gotCity, tt.wantCity)
		}
	}
}
