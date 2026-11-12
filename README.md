# WalkMA Map

[![Netlify Status](https://api.netlify.com/api/v1/badges/38ed888f-9b23-4999-aa12-499c030a43e2/deploy-status)](https://app.netlify.com/projects/walkma/deploys)

Interactive dashboard for the [WalkMA Walk Audit Database](https://docs.google.com/spreadsheets/d/1-Vxf7AlXk_WJwwYSVy7F28qjxVXQOAmQ-NN0JImx95Y/edit?gid=379989993#gid=379989993).

Live site: <https://audits.walkmass.org/> (Netlify), deployed from the [WalkMassachusetts/audit-map](https://github.com/WalkMassachusetts/audit-map) fork, which is kept in sync with this repo.

## Layout

- `app/`: The dashboard (Vue + Vite + MapLibre) and its Netlify function. See `app/README.md`.
- `netlify.toml`: Build, functions, and redirect config (builds from `app/`).
- `.github/workflows/deploy-pages.yml`: Publishes a mirror to GitHub Pages on push to `main`. It has no Netlify function, so it always shows the `last_run.json` snapshot.
- `refresh_data.sh`: Refreshes the fallback data files (requires Go).
- `apps-script/`: Google Apps Script that keeps the sheet's SLUG column (permanent audit page URLs) filled. See `apps-script/README.md`.
- `archive/`: Not deployed: notebooks, unused DB pipeline, and the image-ingestion experiment (PDF scrape + YOLO) that produced the existing photos in `app/public/data/images/`. See `archive/README.md`.

## Development

```sh
mise run dev:live   # netlify dev: Vite + gsheet function, live sheet data (http://localhost:8888)
mise run dev        # Vite only: no function, so the app falls back to stale last_run.json
```

## Data

The Netlify function fetches live audit data from the published Google Sheet. If that fetch fails, it serves its embedded fallback. If the function itself is unreachable, the website loads its own fallback snapshot.

Each audit page URL (`/audit/<slug>`) comes from the sheet's SLUG column (L), which [`apps-script/Slugs.gs`](apps-script/README.md) fills once per row so edits to other cells don't break shared links. Rows without a slug fall back to one generated from city, year, neighborhood and streets.

### Refreshing the saved data

From the repository root, run (requires Go):

```sh
./refresh_data.sh
```

The refresh maintains two fallback files:

- `app/netlify/functions/gsheet/data/audits.json`: Audit array embedded in the Netlify function at build time.
- `app/public/data/last_run.json`: `{date, data}` snapshot used by the website when the function is unreachable.

The script:

1. **Downloads and checks the sheet data.** Download errors or zero parsed audits stop the refresh without changing either fallback or the backups.
2. **Checks for changes.** If the audit data matches the current website snapshot, its timestamp and backups stay untouched. An out-of-sync function fallback is still repaired.
3. **Prepares changed data.** Writes replacement JSON to temporary files beside their destinations before changing either fallback.
4. **Backs up the previous snapshot.** If one exists, copies it to `app/netlify/functions/gsheet/data/backups/last_run_<UTC time>.json`.
5. **Replaces the fallbacks, then prunes backups.** Renames the prepared files into place. Only after both replacements succeed does it delete older backups, keeping the newest 5.
6. **Prints a staging command.** The shell-quoted `git -C ... add -- ...` command works from any directory and stages both fallbacks plus backup additions and deletions.

### Committing and deploying

Review the refresh output and changed data, then run the printed staging command, commit, push, and deploy as usual. Refreshing alone does not update the deployed fallback files.

Backups are committed to Git. Deleted backups remain available in Git history if they were previously committed; the five-file limit applies to the current backup directory, not repository history.

### Recovery and limits

Each file replacement is atomic, but the two-file update is **not a transaction**. An interruption between replacements can leave the fallbacks out of sync. Rerun the refresh successfully before committing.

To restore a backup, copy its entire contents over `app/public/data/last_run.json` and write its `data` array to `app/netlify/functions/gsheet/data/audits.json`. Commit and deploy both restored files.

An empty result is rejected, but a nonempty result is not proof that every sheet row was parsed correctly. Check the printed audit count and data changes before committing.

See the [function README](app/netlify/functions/gsheet/README.md#refreshing-saved-data) for direct CLI usage and custom output paths.
