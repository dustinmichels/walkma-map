# Extract

## Overview

1. **Download** (`extract.py`) — Fetches the WalkMA Walk Audit Google Sheet as an `.xlsx` file, parses each row using a Pydantic model (`WalkAuditDownload`), and saves the result to `data/download/sheet.json`.

2. **Export** (`export.py`) — Reads the JSON, cleans and normalizes the records, then writes four TSV files to `data/output/`:
   - `audits.tsv` — one row per walk audit
   - `facilitators.tsv` — deduplicated list of facilitators
   - `organizations.tsv` — deduplicated list of organizations
   - `themes.tsv` — deduplicated list of themes

**Models** (`models.py`) define the Pydantic schemas used for validation and transformation at each stage.

## Scripts

```sh
ruff check --fix
```
