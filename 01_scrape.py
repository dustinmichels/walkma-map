import io
import os
import re
import shutil

import fitz  # PyMuPDF
import requests
from openpyxl import load_workbook
from PIL import Image, ImageStat
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn

console = Console()

# --- Configuration ---
FRESH_DOWNLOAD = False
OUTPUT_DIR = "data/download"
FIRST_N_ROWS = None

# --- Image Filtering Configuration ---
MIN_IMAGE_WIDTH = 250
MIN_IMAGE_HEIGHT = 200
MAX_ASPECT_RATIO = 3.0
MIN_ASPECT_RATIO = 0.33
MIN_UNIQUE_COLORS = 1500
MAX_EDGE_BRIGHTNESS = 250


def is_likely_logo(image_bytes):
    """Analyzes image bytes to filter out logos, icons, and flat graphics."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
            return True

        aspect_ratio = width / height
        if aspect_ratio > MAX_ASPECT_RATIO or aspect_ratio < MIN_ASPECT_RATIO:
            return True

        if img.mode in ("RGBA", "LA") or (
            img.mode == "P" and "transparency" in img.info
        ):
            alpha = img.convert("RGBA").getchannel("A")
            bbox = alpha.getextrema()
            if bbox and bbox[0] < 255:
                return True

        rgb_img = img.convert("RGB")
        colors = rgb_img.getcolors(maxcolors=MIN_UNIQUE_COLORS + 1)
        if colors is not None and len(colors) <= MIN_UNIQUE_COLORS:
            return True

        stat = ImageStat.Stat(rgb_img)
        avg_brightness = sum(stat.mean) / 3
        if avg_brightness > 240:
            return True

        corners = [
            rgb_img.getpixel((0, 0)),
            rgb_img.getpixel((width - 1, 0)),
            rgb_img.getpixel((0, height - 1)),
            rgb_img.getpixel((width - 1, height - 1)),
        ]
        if all(sum(c) / 3 >= MAX_EDGE_BRIGHTNESS for c in corners):
            return True

        return False
    except Exception:
        return True


def sanitize_folder_name(name):
    if name is None:
        return "unknown"
    name = str(name).split(",")[0].strip()
    try:
        if isinstance(name, (int, float)) or (
            isinstance(name, str) and name.strip().replace(".", "", 1).isdigit()
        ):
            name = str(int(float(name)))
        else:
            name = str(name).lower()
    except (ValueError, TypeError):
        name = str(name).lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def get_direct_download_url(url):
    if not url or not isinstance(url, str):
        return url
    if "drive.google.com" in url:
        match = re.search(r"/d/([^/]+)", url)
        if match:
            return f"https://drive.google.com/uc?export=download&id={match.group(1)}"
    if "docs.google.com/document" in url:
        match = re.search(r"/d/([^/]+)", url)
        if match:
            return (
                f"https://docs.google.com/document/d/{match.group(1)}/export?format=pdf"
            )
    return url


def extract_images_from_pdf(pdf_path, output_subfolder, progress=None, task=None):
    if not os.path.exists(pdf_path):
        return 0
    image_folder = os.path.join(output_subfolder, "images")
    if os.path.exists(image_folder):
        shutil.rmtree(image_folder)

    try:
        doc = fitz.open(pdf_path)
        image_count = 0
        for i in range(len(doc)):
            for img in doc.get_page_images(i):
                xref = img[0]
                base_image = doc.extract_image(xref)
                if is_likely_logo(base_image["image"]):
                    continue

                if not os.path.exists(image_folder):
                    os.makedirs(image_folder)
                image_count += 1
                with open(
                    os.path.join(
                        image_folder, f"image_{image_count}.{base_image['ext']}"
                    ),
                    "wb",
                ) as f:
                    f.write(base_image["image"])
        doc.close()
        return image_count
    except Exception as e:
        console.print(f"    [red][Images Error][/red] {pdf_path}: {e}")
        return 0


def download_pdf(url, folder_path, filename):
    if not url or url == "No Link Found" or not url.startswith("http"):
        return False
    download_url = get_direct_download_url(url)
    try:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        file_path = os.path.join(folder_path, filename)
        response = requests.get(download_url, timeout=45, stream=True)
        response.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        console.print(f"  [red][Error][/red] {url}: {e}")
        return False


def fetch_and_extract(sheet_id, gid):
    console.print(
        Panel.fit(
            "[bold cyan]Walk Audit Scraper[/bold cyan]\n"
            f"Mode: [yellow]{'Fresh download' if FRESH_DOWNLOAD else 'Re-extract from existing PDFs'}[/yellow]",
            border_style="cyan",
        )
    )

    if FRESH_DOWNLOAD:
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)
        os.makedirs(OUTPUT_DIR)

        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx&gid={gid}"
        excel_path = os.path.join(OUTPUT_DIR, "walk_audit_data.xlsx")

        try:
            console.print("[dim]Fetching spreadsheet...[/dim]")
            res = requests.get(export_url)
            with open(excel_path, "wb") as f:
                f.write(res.content)
            wb = load_workbook(excel_path)
            ws = wb.active

            view_col = next(
                (c.column for c in ws[2] if c.value and "VIEW" in str(c.value).upper()),
                None,
            )
            if not view_col:
                console.print("[red][Error][/red] Could not find VIEW column in spreadsheet.")
                return

            rows = [
                row for row in ws.iter_rows(min_row=3) if row[0].value
            ]
            if FIRST_N_ROWS:
                rows = rows[:FIRST_N_ROWS]

            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("[cyan]Downloading audits...", total=len(rows))
                for row in rows:
                    folder_name = (
                        f"{sanitize_folder_name(row[0].value)}"
                        f"_{sanitize_folder_name(row[1].value)}"
                        f"_{sanitize_folder_name(row[5].value)}"
                    )
                    link_url = (
                        row[view_col - 1].hyperlink.target
                        if row[view_col - 1].hyperlink
                        else "No Link Found"
                    )
                    progress.update(task, description=f"[cyan]{folder_name}[/cyan]")
                    folder_path = os.path.join(OUTPUT_DIR, folder_name)
                    ok = download_pdf(link_url, folder_path, "audit.pdf")
                    if ok:
                        n = extract_images_from_pdf(
                            os.path.join(folder_path, "audit.pdf"), folder_path
                        )
                        console.log(
                            f"[green]✓[/green] {folder_name} "
                            f"[dim]({n} image{'s' if n != 1 else ''})[/dim]"
                        )
                    else:
                        console.log(f"[yellow]–[/yellow] {folder_name} [dim](no PDF)[/dim]")
                    progress.advance(task)

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")

    else:
        folders = [
            f for f in os.listdir(OUTPUT_DIR)
            if os.path.exists(os.path.join(OUTPUT_DIR, f, "audit.pdf"))
        ]
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Re-extracting images...", total=len(folders))
            for folder_name in folders:
                folder_path = os.path.join(OUTPUT_DIR, folder_name)
                progress.update(task, description=f"[cyan]{folder_name}[/cyan]")
                n = extract_images_from_pdf(
                    os.path.join(folder_path, "audit.pdf"), folder_path
                )
                console.log(
                    f"[green]✓[/green] {folder_name} "
                    f"[dim]({n} image{'s' if n != 1 else ''})[/dim]"
                )
                progress.advance(task)

    console.print("[bold green]Done.[/bold green]")


if __name__ == "__main__":
    fetch_and_extract("1-Vxf7AlXk_WJwwYSVy7F28qjxVXQOAmQ-NN0JImx95Y", "379989993")
