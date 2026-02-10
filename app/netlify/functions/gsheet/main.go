package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"regexp"
	"strings"

	"github.com/PuerkitoBio/goquery"
	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
)

var (
	reRemoveParens  = regexp.MustCompile(`\s*\(.*?\)`)
	reExtractParens = regexp.MustCompile(`\((.*?)\)`)
)

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

// cleanGoogleSheetLink extracts the actual URL from a Google redirect link
func cleanGoogleSheetLink(s string) string {
	// If it's a google redirect link, extract the 'q' parameter
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

// parseCity processes the raw city string to return cleaned CityTown, City, and Neighborhood
func parseCity(raw string) (string, string, string) {
	cityTown := strings.ToUpper(strings.TrimSpace(raw))

	var neighborhood string
	matches := reExtractParens.FindStringSubmatch(cityTown)
	if len(matches) > 1 {
		neighborhood = matches[1]
	}

	cityClean := reRemoveParens.ReplaceAllString(cityTown, "")
	return cityTown, cityClean, neighborhood
}

// FetchWalkAudits retrieves and parses the walk audit data from the Google Sheet
func FetchWalkAudits() ([]WalkAudit, error) {
	// ... (rest of implementation remains, check next chunk)

	// Use the published HTML version to get access to hyperlinks
	url := "https://docs.google.com/spreadsheets/d/1-Vxf7AlXk_WJwwYSVy7F28qjxVXQOAmQ-NN0JImx95Y/pubhtml/sheet?headers=false&gid=379989993"

	resp, err := http.Get(url)
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

	var audits []WalkAudit

	// Iterate over table rows
	doc.Find("tbody tr").Each(func(i int, s *goquery.Selection) {
		// Get all cells in the row
		cells := s.Find("td")
		if cells.Length() < 10 {
			return
		}

		// Helper to safely get text from a cell
		getText := func(idx int) string {
			return strings.TrimSpace(cells.Eq(idx).Text())
		}

		// Special handling for "View" column (index 7) to get the link
		getViewLink := func(idx int) string {
			cell := cells.Eq(idx)
			// check for anchor tag
			a := cell.Find("a")
			if a.Length() > 0 {
				href, exists := a.Attr("href")
				if exists {
					return cleanGoogleSheetLink(href)
				}
			}
			return strings.TrimSpace(cell.Text())
		}

		// Parse CityTown, City, and Neighborhood using helper function
		cityTown, cityClean, neighborhood := parseCity(getText(0))

		// Filter out Header rows or Title rows (using the cleaned value)
		if cityTown == "CITY/TOWN" || strings.Contains(cityTown, "WALK AUDIT DATABASE") {
			return
		}

		// If city is empty, check if it's just an empty row
		if cityTown == "" && getText(1) == "" {
			return
		}

		audit := WalkAudit{
			CityTown:                  cityTown,
			City:                      cityClean,
			Neighborhood:              neighborhood,
			Year:                      getText(1),
			Summary:                   getText(2),
			LongTermRecommendations:   getText(3),
			ShortTermRecommendations:  getText(4),
			StreetsIntersections:      getText(5),
			Themes:                    getText(6),
			View:                      getViewLink(7),
			FacilitatorAuthor:         getText(8),
			OrganizerLeadOrganization: getText(9),
		}

		audits = append(audits, audit)
	})

	return audits, nil
}

func handler(request events.APIGatewayProxyRequest) (*events.APIGatewayProxyResponse, error) {
	audits, err := FetchWalkAudits()
	if err != nil {
		return &events.APIGatewayProxyResponse{
			StatusCode: http.StatusInternalServerError,
			Body:       err.Error(),
		}, nil
	}

	body, _ := json.Marshal(audits)

	return &events.APIGatewayProxyResponse{
		StatusCode: http.StatusOK,
		Headers: map[string]string{
			"Content-Type":                 "application/json",
			"Access-Control-Allow-Origin":  "*",
			"Access-Control-Allow-Methods": "GET",
			"Cache-Control":                "public, max-age=300, s-maxage=3600, stale-while-revalidate=86400",
			"Netlify-CDN-Cache-Control":    "public, max-age=3600, stale-while-revalidate=86400",
		},
		Body: string(body),
	}, nil
}

func main() {
	lambda.Start(handler)
}
