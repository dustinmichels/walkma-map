package audits

import (
	"fmt"
	"net/http"
	"net/url"
	"regexp"
	"strings"

	"github.com/PuerkitoBio/goquery"
)

var reRemoveParens = regexp.MustCompile(`\s*\(.*?\)`)

type WalkAudit struct {
	CityTown                  string `json:"city_town"`
	City                      string `json:"city"`
	Neighborhood              string `json:"neighborhood"`
	Year                      string `json:"year"`
	Summary                   string `json:"summary"`
	LongTermRecommendations   string `json:"long_term_recommendations"`
	ShortTermRecommendations  string `json:"short_term_recommendations"`
	StreetsIntersections      string `json:"streets_intersections"`
	Themes                    string `json:"themes"`
	View                      string `json:"view"`
	FacilitatorAuthor         string `json:"facilitator_author"`
	OrganizerLeadOrganization string `json:"organizer_lead_organization"`
}

// cleanGoogleSheetLink extracts the actual URL from a Google redirect link.
func cleanGoogleSheetLink(s string) string {
	if strings.Contains(s, "google.com/url") {
		u, err := url.Parse(s)
		if err == nil {
			q := u.Query().Get("q")
			if q != "" {
				return q
			}
		}
	}
	return s
}

// ParseCity uppercases and trims the raw city string, returning the original
// (cityTown) and a version with any parenthetical suffix stripped (city).
func ParseCity(raw string) (cityTown, city string) {
	cityTown = strings.ToUpper(strings.TrimSpace(raw))
	city = reRemoveParens.ReplaceAllString(cityTown, "")
	return
}

// FetchWalkAudits retrieves and parses the walk audit data from the Google Sheet.
func FetchWalkAudits() ([]WalkAudit, error) {
	sheetURL := "https://docs.google.com/spreadsheets/d/1-Vxf7AlXk_WJwwYSVy7F28qjxVXQOAmQ-NN0JImx95Y/pubhtml/sheet?headers=false&gid=379989993"

	resp, err := http.Get(sheetURL)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch spreadsheet: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("bad status: %s", resp.Status)
	}

	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to parse HTML: %w", err)
	}

	var result []WalkAudit

	doc.Find("tbody tr").Each(func(i int, s *goquery.Selection) {
		cells := s.Find("td")
		if cells.Length() < 12 {
			return
		}

		getText := func(idx int) string {
			return strings.TrimSpace(cells.Eq(idx).Text())
		}

		getViewLink := func(idx int) string {
			cell := cells.Eq(idx)
			a := cell.Find("a")
			if a.Length() > 0 {
				href, exists := a.Attr("href")
				if exists {
					return cleanGoogleSheetLink(href)
				}
			}
			return strings.TrimSpace(cell.Text())
		}

		cityTown, cityClean := ParseCity(getText(0))
		neighborhood := getText(3)

		if cityTown == "CITY/TOWN" || strings.Contains(cityTown, "WALK AUDIT DATABASE") {
			return
		}
		if cityTown == "" && neighborhood == "" {
			return
		}

		result = append(result, WalkAudit{
			CityTown:                  cityTown,
			City:                      cityClean,
			Neighborhood:              neighborhood,
			Year:                      getText(2),
			Summary:                   getText(4),
			LongTermRecommendations:   getText(5),
			ShortTermRecommendations:  getText(6),
			StreetsIntersections:      getText(7),
			Themes:                    getText(8),
			View:                      getViewLink(9),
			FacilitatorAuthor:         getText(10),
			OrganizerLeadOrganization: getText(11),
		})
	})

	return result, nil
}
