"""
Download sheet:
    https://docs.google.com/spreadsheets/d/1cpaNsvsAcysRYKPDxvYKT5CuSNm6XGK2FZhqVWPWgsk/edit?gid=379989993#gid=379989993
"""


import requests
import openpyxl
import os
import json
from models import WalkAuditDownload

# --- CONFIGURATION ---
SPREADSHEET_ID = "1cpaNsvsAcysRYKPDxvYKT5CuSNm6XGK2FZhqVWPWgsk"
GID = "379989993"
SAVE_PATH = "data/download/sheet.xlsx"
JSON_OUTPUT_PATH = "data/download/sheet.json"
FRESH_DOWNLOAD = True
# ---------------------


def download_and_process_gsheet():
    """
    Downloads the Google Sheet, processes headers from the first row,
    and maps all specified fields via Pydantic.
    """
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(JSON_OUTPUT_PATH), exist_ok=True)

    if FRESH_DOWNLOAD or not os.path.exists(SAVE_PATH):
        export_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=xlsx&gid={GID}"
        print(f"Downloading sheet: {export_url}")
        try:
            response = requests.get(export_url)
            response.raise_for_status()
            with open(SAVE_PATH, 'wb') as f:
                f.write(response.content)
        except Exception as e:
            print(f"Download failed: {e}")
            if not os.path.exists(SAVE_PATH):
                return

    try:
        wb = openpyxl.load_workbook(SAVE_PATH, data_only=True)
        sheet = wb.active
    except Exception as e:
        print(f"Error loading Excel: {e}")
        return

    rows = list(sheet.rows)
    if not rows:
        print("Sheet is empty.")
        return

    headers = [str(cell.value).strip() if cell.value else f"Col_{i}" for i, cell in enumerate(rows[0])]

    view_col_idx = -1
    if "VIEW" in headers:
        view_col_idx = headers.index("VIEW")

    final_data = []
    print(f"--- Processing {len(rows)-1} potential records ---\n")

    for row_idx, row in enumerate(rows[1:], start=2):
        if all(cell.value is None for cell in row):
            continue

        raw_row_data = {}
        for col_idx, cell in enumerate(row):
            if col_idx >= len(headers):
                continue

            header_name = headers[col_idx]

            if col_idx == view_col_idx:
                link = None
                if cell.hyperlink:
                    link = cell.hyperlink.target
                elif isinstance(cell.value, str) and cell.value.startswith('http'):
                    link = cell.value

                raw_row_data["VIEW"] = str(cell.value) if cell.value else None
                raw_row_data["view_link"] = link
            else:
                val = cell.value
                if hasattr(val, 'isoformat'):
                    val = val.isoformat()
                raw_row_data[header_name] = val

        try:
            audit = WalkAuditDownload(**raw_row_data)
            final_data.append(audit.model_dump(by_alias=True))
            print(f"Row {row_idx}: Success -> {audit.audit_id or 'No ID'}")
        except Exception as e:
            print(f"Row {row_idx}: Validation Error -> {e}")

    with open(JSON_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(final_data)} records to {JSON_OUTPUT_PATH}")
