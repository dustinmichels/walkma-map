#!/usr/bin/env bash
# refresh_data.sh — Fetch the latest walk audit data from Google Sheets and
# update last_run.json in both the Netlify function folder and app/public/data/.
#
# The Netlify function (app/netlify/functions/gsheet) fetches audit records live
# on each request, with data/audits.json embedded as a fallback. last_run.json
# wraps that same data with a timestamp so the frontend can fall back to it
# when the live function is unreachable, and show the user when it was last refreshed.
#
# Usage:
#   ./refresh_data.sh
#
# Requirements: Go, Python 3
#
# After running, commit both output files to keep the embedded fallback current:
#   git add app/netlify/functions/gsheet/data/audits.json
#   git add app/netlify/functions/gsheet/data/last_run.json
#   git add app/public/data/last_run.json

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GSHEET_DIR="$REPO_ROOT/app/netlify/functions/gsheet"
PUBLIC_DATA_DIR="$REPO_ROOT/app/public/data"

# Step 1: fetch live data and write data/audits.json (run from gsheet dir so
# the default output path "data/audits.json" resolves correctly).
echo "--- Fetching audit data from Google Sheet ---"
cd "$GSHEET_DIR"
go run ./cmd/refresh

# Step 2: wrap the fetched data with a UTC timestamp and write last_run.json
# to both the function folder (embedded fallback) and public/data (served to
# the frontend as a static file).
echo ""
echo "--- Writing last_run.json ---"
python3 - "$GSHEET_DIR/data/audits.json" \
           "$GSHEET_DIR/data/last_run.json" \
           "$PUBLIC_DATA_DIR/last_run.json" <<'PYEOF'
import json, sys, datetime

audits_file, *out_paths = sys.argv[1:]

with open(audits_file) as f:
    data = json.load(f)

payload = {
    "date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "data": data,
}

for path in out_paths:
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {path}")
PYEOF

echo ""
echo "Done. Commit the updated files to keep the fallback current:"
echo "  git add app/netlify/functions/gsheet/data/audits.json"
echo "  git add app/netlify/functions/gsheet/data/last_run.json"
echo "  git add app/public/data/last_run.json"
