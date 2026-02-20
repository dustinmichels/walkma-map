package main

import (
	_ "embed"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strings"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"hello/internal/audits"
)

//go:embed data/audits.json
var savedAuditsJSON []byte

func loadSavedAudits() ([]audits.WalkAudit, error) {
	var result []audits.WalkAudit
	err := json.Unmarshal(savedAuditsJSON, &result)
	return result, err
}

func handler(request events.APIGatewayProxyRequest) (*events.APIGatewayProxyResponse, error) {
	var auditData []audits.WalkAudit
	var err error

	disableLive := strings.TrimSpace(strings.ToLower(os.Getenv("DISABLE_LIVE_UPDATE")))
	if disableLive == "true" || disableLive == "1" {
		log.Println("DISABLE_LIVE_UPDATE is set — loading from embedded saved data")
		auditData, err = loadSavedAudits()
	} else {
		auditData, err = audits.FetchWalkAudits()
		if err != nil {
			log.Printf("Warning: failed to fetch live data (%v); falling back to embedded saved data", err)
			auditData, err = loadSavedAudits()
		}
	}

	if err != nil {
		return &events.APIGatewayProxyResponse{
			StatusCode: http.StatusInternalServerError,
			Body:       err.Error(),
		}, nil
	}

	body, _ := json.Marshal(auditData)

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
