# Archive

Old experiments and one-off tooling. Nothing here runs as part of the deployed dashboard (`app/`).

| Path | What it is |
| --- | --- |
| `old-py/01_scrape.py`, `old-py/02_copy.py` | Image-ingestion experiment. Produced the photos committed in `app/public/data/images/`, which the dashboard still shows. Not in use: new audits don't get photos. |
| `old-py/*.ipynb` | Exploratory notebooks: sheet cleanup, town boundary prep (`towns.geojson`). |
| `extract/` | Unused pipeline for migrating the sheet into a relational database. See `extract/README.md`. |
| `verify_ids.cjs` | One-off town/audit ID check against the old `audits.geojson` format. |

## Image-ingestion experiment

1. `01_scrape.py` downloads each audit's PDF from the sheet and extracts candidate photos into `data/download/<identifier>/images/`.
2. `02_copy.py` picks the best photo per audit with YOLOv8 (people > cars > aspect ratio; weights in `yolov8n.pt`, gitignored, auto-downloaded) and copies it to `app/public/data/images/<identifier>.jpeg`.

`<identifier>` comes from `get_audit_identifier()` in `01_scrape.py`. The dashboard rebuilds the same name in `auditImageId()` (`app/src/utils.ts`) to find each existing photo, so don't change that function or the images stop showing.

⚠️ `02_copy.py` deletes and recreates `app/public/data/images/` before copying, so running it replaces the existing photos.

The scripts use paths relative to the repo root (`data/`, `app/public/data/`), so run them from there. Requires [uv](https://docs.astral.sh/uv/):

```sh
uv run --project archive/old-py python archive/old-py/01_scrape.py
uv run --project archive/old-py python archive/old-py/02_copy.py
```
