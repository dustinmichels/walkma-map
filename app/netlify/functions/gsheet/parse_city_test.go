package main

import "testing"

func TestParseCity(t *testing.T) {
	tests := []struct {
		input        string
		wantCityTown string
		wantCity     string
		wantNeigh    string
	}{
		{"Boston", "BOSTON", "BOSTON", ""},
		{"Boston (Dorchester)", "BOSTON (DORCHESTER)", "BOSTON", "DORCHESTER"},
		{" Somerville ", "SOMERVILLE", "SOMERVILLE", ""},
		{"Cambridge(North)", "CAMBRIDGE(NORTH)", "CAMBRIDGE", "NORTH"},
		{" Medford  ( Hillside ) ", "MEDFORD  ( HILLSIDE )", "MEDFORD", " HILLSIDE "},
	}

	for _, tt := range tests {
		gotCityTown, gotCity, gotNeigh := parseCity(tt.input)
		if gotCityTown != tt.wantCityTown {
			t.Errorf("parseCity(%q) cityTown = %q, want %q", tt.input, gotCityTown, tt.wantCityTown)
		}
		if gotCity != tt.wantCity {
			t.Errorf("parseCity(%q) city = %q, want %q", tt.input, gotCity, tt.wantCity)
		}
		if gotNeigh != tt.wantNeigh {
			t.Errorf("parseCity(%q) neighborhood = %q, want %q", tt.input, gotNeigh, tt.wantNeigh)
		}
	}
}
