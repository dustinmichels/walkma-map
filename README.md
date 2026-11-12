# WalkMA Map

[![Netlify Status](https://api.netlify.com/api/v1/badges/38ed888f-9b23-4999-aa12-499c030a43e2/deploy-status)](https://app.netlify.com/projects/walkma/deploys)

Interactive dashboard for the [WalkMA Walk Audit Database](https://docs.google.com/spreadsheets/d/1-Vxf7AlXk_WJwwYSVy7F28qjxVXQOAmQ-NN0JImx95Y/edit?gid=379989993#gid=379989993).

## Layout

- `app/`: The dashboard (Vue + Vite + MapLibre) and its Netlify function. See `app/README.md`.
- `netlify.toml`: Build, functions, and redirect config (builds from `app/`).
- `refresh_data.sh`: Refreshes the fallback data files (requires Go).
- `archive/`: Not deployed: notebooks, unused DB pipeline, and the image-ingestion experiment (PDF scrape + YOLO) that produced the existing photos in `app/public/data/images/`. See `archive/README.md`.

## Development

```sh
mise run dev:live   # netlify dev: Vite + gsheet function, live sheet data (http://localhost:8888)
mise run dev        # Vite only: no function, so the app falls back to stale last_run.json
```

## Data

A Netlify function fetches live data from the sheet when the page loads. If that fails, the app (map and audit pages) falls back on `app/public/data/last_run.json` and shows when it was last refreshed. Refresh it, and the function's embedded copy, with:

```sh
./refresh_data.sh
```
