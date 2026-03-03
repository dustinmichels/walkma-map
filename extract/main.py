import requests
import openpyxl
import os
import json
from io import BytesIO
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

# --- CONFIGURATION ---
SPREADSHEET_ID = "1-Vxf7AlXk_WJwwYSVy7F28qjxVXQOAmQ-NN0JImx95Y"
GID = "379989993"
SAVE_PATH = "data/download/sheet.xlsx"
JSON_OUTPUT_PATH = "data/sheet.json"
FRESH_DOWNLOAD = True  # Set to False to use the local file if it exists
# ---------------------

class WalkAudit(BaseModel):
    """Represents a single walk audit record from the spreadsheet."""
    model_config = ConfigDict(populate_by_name=True)

    city_town: Optional[str] = Field(None, alias="CITY/TOWN")
    year: Optional[float] = Field(None, alias="YEAR")
    neighborhood: Optional[str] = Field(None, alias="NEIGHBORHOOD")
    summary: Optional[str] = Field(None, alias="SUMMARY")
    long_term_recommendations: Optional[str] = Field(None, alias="LONG TERM RECOMMENDATIONS")
    short_term_recommendations: Optional[str] = Field(None, alias="SHORT TERM RECOMMENDATIONS")
    streets_area_covered: Optional[str] = Field(None, alias="STREETS, INNTERSECTIONS + AREA COVERED")
    themes: Optional[str] = Field(None, alias="THEMES")
    view_text: Optional[str] = Field(None)
    view_link: Optional[str] = Field(None)
    facilitator_author: Optional[str] = Field(None, alias="FACILITATOR/AUTHOR")
    organizations: Optional[str] = Field(None, alias="ORGANIZATIONS")

def download_and_process_gsheet():
    """
    Downloads or loads a Google Sheet as an Excel file, validates with Pydantic,
    and saves the results to a JSON file.
    """
    
    # Ensure directories exist
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(JSON_OUTPUT_PATH), exist_ok=True)
    
    should_download = FRESH_DOWNLOAD or not os.path.exists(SAVE_PATH)

    if should_download:
        export_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=xlsx&gid={GID}"
        print(f"Downloading sheet from: {export_url}...")
        
        try:
            response = requests.get(export_url)
            response.raise_for_status()
            with open(SAVE_PATH, 'wb') as f:
                f.write(response.content)
            print(f"File saved to: {SAVE_PATH}")
        except requests.exceptions.RequestException as e:
            print(f"Error downloading the file: {e}")
            if not os.path.exists(SAVE_PATH):
                return
            print("Falling back to existing local file...")

    print(f"Loading workbook from: {SAVE_PATH}...")
    try:
        wb = openpyxl.load_workbook(SAVE_PATH)
        sheet = wb.active
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return

    rows = list(sheet.rows)
    if len(rows) < 2:
        print("Sheet does not have enough rows.")
        return

    # Extract headers from Row 2 (index 1)
    headers = [str(cell.value).strip() if cell.value else f"Col_{i+1}" for i, cell in enumerate(rows[1])]
    
    final_data = []

    print(f"\n--- Processing Rows ---\n")

    # Iterate over data rows starting from row 3 (index 2)
    for row_idx, row in enumerate(rows[2:], start=3):
        if all(cell.value is None for cell in row):
            continue

        raw_row_data = {}
        for col_idx, cell in enumerate(row):
            header_name = headers[col_idx]
            
            # Special handling for Column I (index 8) to extract links
            if col_idx == 8:
                link = None
                if cell.hyperlink:
                    link = cell.hyperlink.target
                elif isinstance(cell.value, str) and (cell.value.startswith('http')):
                    link = cell.value
                
                raw_row_data["view_text"] = str(cell.value) if cell.value else None
                raw_row_data["view_link"] = link
            else:
                raw_row_data[header_name] = cell.value

        # Validate with Pydantic
        try:
            audit = WalkAudit(**raw_row_data)
            # Use model_dump instead of dict (Pydantic V2)
            final_data.append(audit.model_dump(by_alias=True))
            
            # Print feedback
            print(f"Processed Row {row_idx}: {audit.city_town} ({audit.year})")
        except Exception as e:
            print(f"Validation error at row {row_idx}: {e}")

    # Save to JSON
    with open(JSON_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nSuccess! Total records processed: {len(final_data)}")
    print(f"Data saved to: {JSON_OUTPUT_PATH}")

if __name__ == "__main__":
    download_and_process_gsheet()