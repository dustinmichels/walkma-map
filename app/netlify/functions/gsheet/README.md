# gsheet Netlify Function

A Go-based serverless function that fetches walk audit data from a published Google Sheet and returns it as JSON.

## How It Works

1. Checks the `DISABLE_LIVE_UPDATE` environment variable. If set, skips the live fetch and returns the embedded saved data immediately.
2. Otherwise, fetches the Google Sheet as published HTML (using the `pubhtml` URL).
3. Parses the HTML table rows using [goquery](https://github.com/PuerkitoBio/goquery).
4. Extracts 12 columns per row, skipping header/title rows and empty rows.
5. For the "View" column, extracts the `href` from anchor tags and unwraps Google redirect URLs.
6. Uppercases the city/town column and strips any parenthetical suffix to produce the clean `city` value (e.g., `"BOSTON (DORCHESTER)"` → `city: "BOSTON"`). Neighborhood comes from its own dedicated column (index 3).
7. If the live fetch fails for any reason, falls back to the embedded saved data and logs a warning.
8. Returns the result as a JSON array.

## Endpoint

```
GET /.netlify/functions/gsheet
```

## Environment Variables

| Variable              | Description                                                                                                                                                           |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DISABLE_LIVE_UPDATE` | Set to `true` or `1` to skip the live Google Sheet fetch entirely and always serve the embedded saved data. Useful when the sheet is unavailable or has changed unexpectedly. The function also falls back to saved data automatically on fetch errors, even without this flag. |

## Caching

The response includes cache headers:

- **Browser:** 5 minutes (`max-age=300`)
- **CDN edge:** 1 hour (`s-maxage=3600`)
- **Stale-while-revalidate:** 1 day (`86400`)

## Fallback Behavior

The function embeds `data/audits.json` at compile time. If the live Google Sheet fetch fails (network error, bad status, parse error), the function logs a warning and serves the embedded data instead of returning an error.

To force the embedded data to be used without any live fetch attempt, set `DISABLE_LIVE_UPDATE=true`.

## Refreshing Saved Data

To update the saved data from the live Google Sheet, run the refresh command from the `netlify/functions/gsheet/` directory:

```bash
cd netlify/functions/gsheet
go run ./cmd/refresh
```

This writes the latest data to `data/audits.json`, which is the file embedded into the Lambda binary at build time. Commit it after running to keep the fallback current.

The output path can be overridden with a flag:

```bash
go run ./cmd/refresh --out path/to/audits.json
```

## Response Fields

The function returns an array of walk audit objects:

| Field                         | Type   | Description                                                                                              |
| ----------------------------- | ------ | -------------------------------------------------------------------------------------------------------- |
| `city_town`                   | string | Full city/town name, uppercased. May include neighborhood in parentheses (e.g., `"BOSTON (DORCHESTER)"`) |
| `city`                        | string | City name with neighborhood stripped (e.g., `"BOSTON"`)                                                  |
| `neighborhood`                | string | Neighborhood name from the dedicated neighborhood column, or empty string                                |
| `year`                        | string | Year the audit was conducted                                                                             |
| `summary`                     | string | Description of the walk audit, its goals, and participants                                               |
| `long_term_recommendations`   | string | Long-term infrastructure improvement recommendations                                                     |
| `short_term_recommendations`  | string | Short-term or quick-fix recommendations                                                                  |
| `streets_intersections`       | string | Streets, intersections, and areas covered by the audit                                                   |
| `themes`                      | string | Comma-separated tags (e.g., `"Comfort & Safety, Schools, Youth"`)                                        |
| `view`                        | string | URL to the full audit report (PDF or Google Doc)                                                         |
| `facilitator_author`          | string | Name(s) of the audit facilitator or author                                                               |
| `organizer_lead_organization` | string | Organization that led or organized the audit                                                             |

## Data Source

The data is sourced from a Google Sheet published at:

```
https://docs.google.com/spreadsheets/d/1-Vxf7AlXk_WJwwYSVy7F28qjxVXQOAmQ-NN0JImx95Y/pubhtml/sheet?headers=false&gid=379989993
```

The sheet columns map to response fields as follows:

| Column Index | Field                                        |
| ------------ | -------------------------------------------- |
| 0            | `city_town` / `city` (parsed from raw value) |
| 1            | _(unused)_                                   |
| 2            | `year`                                       |
| 3            | `neighborhood`                               |
| 4            | `summary`                                    |
| 5            | `long_term_recommendations`                  |
| 6            | `short_term_recommendations`                 |
| 7            | `streets_intersections`                      |
| 8            | `themes`                                     |
| 9            | `view` (link extracted from anchor tag)      |
| 10           | `facilitator_author`                         |
| 11           | `organizer_lead_organization`                |

## Project Structure

```
netlify/functions/gsheet/
├── main.go                  # Lambda handler (env var check, fallback logic)
├── main_test.go             # Integration test for FetchWalkAudits
├── parse_city_test.go       # Unit tests for ParseCity
├── go.mod / go.sum
├── data/
│   └── audits.json          # Embedded fallback data (committed to repo)
├── internal/
│   └── audits/
│       └── audits.go        # Shared types, FetchWalkAudits, ParseCity
└── cmd/
    └── refresh/
        └── main.go          # CLI tool to update saved data files
```
