# gsheet Netlify Function

A Go-based serverless function that fetches walk audit data from a published Google Sheet and returns it as JSON.

## How It Works

1. Fetches the Google Sheet as published HTML (using the `pubhtml` URL)
2. Parses the HTML table rows using [goquery](https://github.com/PuerkitoBio/goquery)
3. Extracts data from 10 columns per row, skipping header/title rows and empty rows
4. For the "View" column, extracts the `href` from anchor tags and unwraps Google redirect URLs
5. Parses the city/town column to separate city name from neighborhood (e.g., `"BOSTON (DORCHESTER)"` becomes `city: "BOSTON"`, `neighborhood: "DORCHESTER"`)
6. Returns the result as a JSON array

## Endpoint

```
GET /.netlify/functions/gsheet
```

## Caching

The response includes cache headers:

- **Browser:** 5 minutes (`max-age=300`)
- **CDN edge:** 1 hour (`s-maxage=3600`)
- **Stale-while-revalidate:** 1 day (`86400`)

## Response Fields

The function returns an array of walk audit objects with the following fields:

| Field                         | Type   | Description                                                                                              |
| ----------------------------- | ------ | -------------------------------------------------------------------------------------------------------- |
| `city_town`                   | string | Full city/town name, uppercased. May include neighborhood in parentheses (e.g., `"BOSTON (DORCHESTER)"`) |
| `city`                        | string | City name with neighborhood stripped (e.g., `"BOSTON"`)                                                  |
| `neighborhood`                | string | Neighborhood name extracted from parentheses, or empty string                                            |
| `year`                        | string | Year the audit was conducted                                                                             |
| `summary`                     | string | Description of the walk audit, its goals, and participants                                               |
| `long_term_recommendations`   | string | Long-term infrastructure improvement recommendations                                                     |
| `short_term_recommendations`  | string | Short-term or quick-fix recommendations                                                                  |
| `streets_intersections`       | string | Streets, intersections, and areas covered by the audit                                                   |
| `themes`                      | string | Comma-separated tags (e.g., `"Comfort & Safety, Schools, Youth"`). Values may be quoted.                 |
| `view`                        | string | URL to the full audit report (PDF or Google Doc)                                                         |
| `facilitator_author`          | string | Name(s) of the audit facilitator or author                                                               |
| `organizer_lead_organization` | string | Organization that led or organized the audit                                                             |

## Data Source

The data is sourced from a Google Sheet published at:

```
https://docs.google.com/spreadsheets/d/1-Vxf7AlXk_WJwwYSVy7F28qjxVXQOAmQ-NN0JImx95Y/pubhtml/sheet?headers=false&gid=379989993
```

The sheet columns map to the response fields in order:

| Column Index | Field                                          |
| ------------ | ---------------------------------------------- |
| 0            | `city_town` / `city` / `neighborhood` (parsed) |
| 1            | `year`                                         |
| 2            | `summary`                                      |
| 3            | `long_term_recommendations`                    |
| 4            | `short_term_recommendations`                   |
| 5            | `streets_intersections`                        |
| 6            | `themes`                                       |
| 7            | `view` (link extracted from anchor tag)        |
| 8            | `facilitator_author`                           |
| 9            | `organizer_lead_organization`                  |
