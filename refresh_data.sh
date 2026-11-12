#!/usr/bin/env bash
# refresh_data.sh — Fetch the latest walk audit data from Google Sheets and
# update both fallback files:
#
#   app/netlify/functions/gsheet/data/audits.json  embedded in the Netlify function
#   app/public/data/last_run.json                  {date, data} snapshot the frontend
#                                                  loads if the function is unreachable
#
# Usage:
#   ./refresh_data.sh
#
# Requirements: Go
#
# Commit both files afterwards to keep the fallbacks current.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/app/netlify/functions/gsheet"
go run ./cmd/refresh
