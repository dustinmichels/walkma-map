#!/usr/bin/env bash
# refresh_data.sh — Fetch the latest walk audit data from Google Sheets and
# update both fallback files:
#
#   app/netlify/functions/gsheet/data/audits.json  embedded in the Netlify function
#   app/public/data/last_run.json                  {date, data} snapshot the frontend
#                                                  loads if the function is unreachable
#
# Failed downloads and empty results leave files and backups untouched.
# Unchanged audit data preserves the snapshot timestamp and backup history.
# Changed data is staged, then the previous last_run.json is copied to
# app/netlify/functions/gsheet/data/backups/ before replacement. The newest 5
# backups are retained after both replacements succeed.
#
# Usage:
#   ./refresh_data.sh
#
# Requirements: Go
#
# Use the printed git command to stage both fallbacks and backups, then commit.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/app/netlify/functions/gsheet"
go run ./cmd/refresh
