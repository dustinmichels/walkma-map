"""
Download sheet:
    https://docs.google.com/spreadsheets/d/1cpaNsvsAcysRYKPDxvYKT5CuSNm6XGK2FZhqVWPWgsk/edit?gid=379989993#gid=379989993
"""

import requests
import openpyxl
import os
import json
from io import BytesIO
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any

# --- CONFIGURATION ---
# New Spreadsheet ID from your link
SPREADSHEET_ID = "1cpaNsvsAcysRYKPDxvYKT5CuSNm6XGK2FZhqVWPWgsk"
GID = "379989993"  # Defaulting to first sheet, adjust if necessary
SAVE_PATH = "data/download/sheet.xlsx"
JSON_OUTPUT_PATH = "data/download/sheet.json"
FRESH_DOWNLOAD = True 
# ---------------------

class WalkAudit(BaseModel):
    """Represents a single walk audit record from the new spreadsheet structure."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    audit_id: Optional[Any] = Field(None, alias="audit_id")
    city_town: Optional[str] = Field(None, alias="CITY/TOWN")
    year: Optional[Any] = Field(None, alias="YEAR")
    neighborhood: Optional[str] = Field(None, alias="NEIGHBORHOOD")
    summary: Optional[str] = Field(None, alias="SUMMARY")
    long_term_recommendations: Optional[str] = Field(None, alias="LONG TERM RECOMMENDATIONS")
    short_term_recommendations: Optional[str] = Field(None, alias="SHORT TERM RECOMMENDATIONS")
    streets_area_covered: Optional[str] = Field(None, alias="STREETS, INNTERSECTIONS + AREA COVERED")
    themes: Optional[str] = Field(None, alias="THEMES")
    
    # View fields (Custom logic for links)
    view_text: Optional[str] = Field(None, alias="VIEW")
    view_link: Optional[str] = Field(None)
    
    facilitator_author: Optional[str] = Field(None, alias="FACILITATOR/AUTHOR")
    organizations: Optional[str] = Field(None, alias="ORGANIZATIONS")
    plain_text: Optional[str] = Field(None, alias="Plain Text")
    audit_date: Optional[Any] = Field(None, alias="audit_date")
    report_date: Optional[Any] = Field(None, alias="report_date")
    start_address: Optional[str] = Field(None, alias="start_address")
    google_maps: Optional[str] = Field(None, alias="google_maps")
    neighborhood_parsed: Optional[str] = Field(None, alias="neighborhood_parsed")

def download_and_process_gsheet():
    """
    Downloads the new Google Sheet, processes headers from the first row,
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
            if not os.path.exists(SAVE_PATH): return

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

    # NEW: Headers are now in the first row (index 0)
    headers = [str(cell.value).strip() if cell.value else f"Col_{i}" for i, cell in enumerate(rows[0])]
    
    # Locate the VIEW column index for link extraction
    view_col_idx = -1
    if "VIEW" in headers:
        view_col_idx = headers.index("VIEW")

    final_data = []
    print(f"--- Processing {len(rows)-1} potential records ---\n")

    # Data starts from row 2 (index 1)
    for row_idx, row in enumerate(rows[1:], start=2):
        if all(cell.value is None for cell in row):
            continue

        raw_row_data = {}
        for col_idx, cell in enumerate(row):
            if col_idx >= len(headers): continue
            
            header_name = headers[col_idx]
            
            # Special link extraction for the VIEW column
            if col_idx == view_col_idx:
                link = None
                if cell.hyperlink:
                    link = cell.hyperlink.target
                elif isinstance(cell.value, str) and cell.value.startswith('http'):
                    link = cell.value
                
                raw_row_data["VIEW"] = str(cell.value) if cell.value else None
                raw_row_data["view_link"] = link
            else:
                # Standard field mapping
                val = cell.value
                # Convert datetime objects to string for JSON compatibility if needed
                if hasattr(val, 'isoformat'):
                    val = val.isoformat()
                raw_row_data[header_name] = val

        try:
            audit = WalkAudit(**raw_row_data)
            final_data.append(audit.model_dump(by_alias=True))
            print(f"Row {row_idx}: Success -> {audit.audit_id or 'No ID'}")
        except Exception as e:
            print(f"Row {row_idx}: Validation Error -> {e}")

    with open(JSON_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved {len(final_data)} records to {JSON_OUTPUT_PATH}")

if __name__ == "__main__":
    download_and_process_gsheet()