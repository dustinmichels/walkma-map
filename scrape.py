import os
import re

import pandas as pd
import requests
from openpyxl import load_workbook

# Global configuration
OUTPUT_DIR = "data/download"


def sanitize_folder_name(name):
    """
    Converts strings like 'Barnstable (Hyannis)' into 'barnstable_hyannis'.
    Removes special characters and replaces spaces/punctuation with underscores.
    """
    if not name:
        return "unknown"
    # Convert to lowercase
    name = str(name).lower()
    # Replace non-alphanumeric characters (including parens) with underscores
    name = re.sub(r"[^a-z0-9]+", "_", name)
    # Remove leading/trailing underscores
    return name.strip("_")


def download_pdf(url, folder_path, filename):
    """
    Downloads a PDF from a URL and saves it to the specified folder.
    """
    if not url or url == "No Link Found" or not url.startswith("http"):
        print(f"  [Skipped] No valid URL for {filename}")
        return False

    try:
        # Create the specific directory if it doesn't exist
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        file_path = os.path.join(folder_path, filename)

        # Download the content
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        with open(file_path, "wb") as f:
            f.write(response.content)

        print(f"  [Success] Downloaded: {file_path}")
        return True
    except Exception as e:
        print(f"  [Error] Failed to download {url}: {e}")
        return False


def fetch_and_organize_walk_audits(sheet_id, gid):
    """
    Downloads the Google Sheet, extracts PDF links, and organizes files into folders.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx&gid={gid}"
    excel_path = os.path.join(OUTPUT_DIR, "walk_audit_data.xlsx")

    try:
        print(f"Downloading sheet from Google to {excel_path}...")
        response = requests.get(export_url)
        response.raise_for_status()

        with open(excel_path, "wb") as f:
            f.write(response.content)

        wb = load_workbook(excel_path)
        ws = wb.active

        # Identify headers and data
        view_col_idx = None
        header_row_num = 2  # Based on the specific layout of your sheet

        for cell in ws[header_row_num]:
            val = str(cell.value).strip().upper() if cell.value else ""
            if val == "VIEW":
                view_col_idx = cell.column
                break

        if not view_col_idx:
            print(f"Could not find 'VIEW' column in row {header_row_num}.")
            return

        print(f"Processing rows and downloading PDFs...\n" + "=" * 50)

        for row in ws.iter_rows(min_row=header_row_num + 1):
            if all(cell.value is None for cell in row):
                continue

            # 1. Extract Info
            city_raw = row[0].value
            year_raw = row[1].value

            # 2. Extract Link
            target_cell = row[view_col_idx - 1]
            link_url = (
                target_cell.hyperlink.target
                if target_cell.hyperlink
                else "No Link Found"
            )

            # 3. Create Folder Name: city_year
            city_slug = sanitize_folder_name(city_raw)
            year_slug = sanitize_folder_name(year_raw)
            folder_name = f"{city_slug}_{year_slug}"
            target_folder = os.path.join(OUTPUT_DIR, folder_name)

            # 4. Create File Name
            # We'll call it "walk_audit.pdf" or use the city_year naming
            file_name = f"walk_audit_{folder_name}.pdf"

            print(f"Row: {city_raw} ({year_raw}) -> Folder: {folder_name}")

            # 5. Perform Download
            download_pdf(link_url, target_folder, file_name)

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    SHEET_ID = "1-Vxf7AlXk_WJwwYSVy7F28qjxVXQOAmQ-NN0JImx95Y"
    GID = "379989993"
    fetch_and_organize_walk_audits(SHEET_ID, GID)
