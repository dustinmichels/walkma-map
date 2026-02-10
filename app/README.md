# app

Interactive data map.

Using vue 3, vite, bun, and maplibre-gl.

## Data Pipeline

Audit data is sourced from a Google Sheet and served via a Netlify Function (`netlify/functions/gsheet`). The app fetches from `/.netlify/functions/gsheet` at page load.

### Caching

The function response is cached at two levels:

- **Netlify CDN** (`Netlify-CDN-Cache-Control`): Cached for 1 hour, with stale content served for up to 24 hours while revalidating in the background. This means the function (and Google Sheets scrape) only runs ~once per hour per edge location.
- **Browser** (`Cache-Control`): Cached for 5 minutes (`max-age=300`). After that the browser revalidates with the CDN, which will typically serve from its own cache.

To change these durations, edit the response headers in `netlify/functions/gsheet/main.go` in the `handler` function. Values are in seconds (e.g. 300 = 5 min, 3600 = 1 hour, 86400 = 24 hours).
