"""
02_copy.py — Select the best image from each audit folder and copy it to the frontend.

Expects 01_scrape.py to have already run and populated OUTPUT_DIR with subfolders,
each containing an `images/` subdirectory of candidate photos.

Selection
---------
Images are selected using a three-tier priority system powered by YOLOv8 object detection:

  1. People present  → pick the image with the best aspect ratio match to 700x300
  2. Cars present    → pick the image with the best aspect ratio match to 700x300
  3. Fallback        → pick whichever image has the best aspect ratio

"Cars" includes COCO classes: car (2), bus (5), truck (7).
"""

import os
import shutil

from PIL import Image
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn
from rich.table import Table
from ultralytics import YOLO

console = Console()

# Load YOLOv8 nano model once at module level (downloads on first run)
_model = YOLO("yolov8n.pt")

# COCO class IDs
COCO_PERSON = 0
COCO_VEHICLE_CLASSES = {2, 5, 7}  # car, bus, truck

# --- Configuration ---
OUTPUT_DIR = "data/download"
LOG_FILE = "data/download/copy.log"
PRIMARY_IMAGE_DIR = "app/public/data/images"
MAX_WIDTH = 700  # px — images wider than this are downscaled
JPEG_QUALITY = 85  # 0–95; 85 is a good web balance of size vs. quality
BANNER_RATIO = 700 / 300  # target aspect ratio for the frontend banner


def save_compressed(src_path, dest_path):
    """Resize to MAX_WIDTH and save as JPEG. Returns output file size in KB."""
    with Image.open(src_path) as img:
        img = img.convert("RGB")  # drop alpha, normalise mode for JPEG
        if img.width > MAX_WIDTH:
            new_height = int(img.height * MAX_WIDTH / img.width)
            img = img.resize((MAX_WIDTH, new_height), Image.LANCZOS)
        img.save(dest_path, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return os.path.getsize(dest_path) // 1024


def detect_classes(image_path):
    """
    Run YOLOv8 on the image and return the set of detected COCO class IDs.
    Returns an empty set on error.
    """
    try:
        results = _model(image_path, verbose=False)
        detected = set()
        for r in results:
            for cls in r.boxes.cls.tolist():
                detected.add(int(cls))
        return detected
    except Exception:
        return set()


def get_ratio_score(path):
    """Return aspect-ratio similarity score for the given image path (higher = better)."""
    try:
        with Image.open(path) as img:
            w, h = img.size
        return 1.0 / (1.0 + abs((w / h) - BANNER_RATIO))
    except Exception:
        return 0.0


def pick_best_image(img_files):
    """
    Pick the best cover image using a three-tier priority:
      1. Images with people  → best ratio wins
      2. Images with cars    → best ratio wins
      3. Any image           → best ratio wins

    Returns (best_path, tier, best_ratio_score, candidates) where:
      - tier is "person", "car", or "ratio"
      - candidates is a list of (path, has_person, has_car, ratio)
    """
    candidates = []
    for path in img_files:
        classes = detect_classes(path)
        has_person = COCO_PERSON in classes
        has_car = bool(classes & COCO_VEHICLE_CLASSES)
        r = get_ratio_score(path)
        candidates.append((path, has_person, has_car, r))

    # Tier 1: images with people
    with_person = [(p, r) for p, hp, hc, r in candidates if hp]
    if with_person:
        best_path, best_r = max(with_person, key=lambda x: x[1])
        return best_path, "person", best_r, candidates

    # Tier 2: images with cars / vehicles
    with_car = [(p, r) for p, hp, hc, r in candidates if hc]
    if with_car:
        best_path, best_r = max(with_car, key=lambda x: x[1])
        return best_path, "car", best_r, candidates

    # Tier 3: best aspect ratio only
    best_path, _, _, best_r = max(candidates, key=lambda x: x[3])
    return best_path, "ratio", best_r, candidates


def copy_best_images():
    """Pick the best image per folder and copy it to the frontend."""
    console.print(
        Panel.fit(
            f"[bold cyan]Image Selector[/bold cyan]\n"
            f"[dim]{OUTPUT_DIR}[/dim] [cyan]→[/cyan] [dim]{PRIMARY_IMAGE_DIR}[/dim]",
            border_style="cyan",
        )
    )

    if os.path.exists(PRIMARY_IMAGE_DIR):
        shutil.rmtree(PRIMARY_IMAGE_DIR)
    os.makedirs(PRIMARY_IMAGE_DIR)

    folders = sorted(
        f for f in os.listdir(OUTPUT_DIR) if os.path.isdir(os.path.join(OUTPUT_DIR, f))
    )

    results = []  # (folder_name, n_candidates, tier, ratio, size_kb) — tier=None if skipped
    detail_logs = []  # (folder_name, candidates, best_path)

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Scoring images...", total=len(folders))

        for folder_name in folders:
            progress.update(task, description=f"[cyan]{folder_name}[/cyan]")

            images_path = os.path.join(OUTPUT_DIR, folder_name, "images")
            if not os.path.exists(images_path):
                results.append((folder_name, 0, None, None, 0))
                progress.advance(task)
                continue

            img_files = [
                os.path.join(images_path, f)
                for f in os.listdir(images_path)
                if f.startswith("image_")
            ]
            if not img_files:
                results.append((folder_name, 0, None, None, 0))
                progress.advance(task)
                continue

            best_img, tier, best_r, candidates = pick_best_image(img_files)
            dest = os.path.join(PRIMARY_IMAGE_DIR, f"{folder_name}.jpeg")
            size_kb = save_compressed(best_img, dest)
            results.append((folder_name, len(img_files), tier, best_r, size_kb))
            detail_logs.append((folder_name, candidates, best_img))
            progress.advance(task)

    # Summary table
    TIER_STYLE = {
        "person": "[green]person[/green]",
        "car": "[yellow]car[/yellow]",
        "ratio": "[dim]ratio[/dim]",
    }

    table = Table(title="Results", show_lines=False, header_style="bold cyan")
    table.add_column("Folder", style="dim", no_wrap=False)
    table.add_column("Candidates", justify="right")
    table.add_column("Selected by", justify="center")
    table.add_column("Ratio score", justify="right")
    table.add_column("Size", justify="right")
    table.add_column("Status", justify="center")

    selected = sum(1 for _, n, t, r, sz in results if t is not None)
    skipped = len(results) - selected

    for folder_name, n_candidates, tier, best_r, size_kb in results:
        if tier is None:
            table.add_row(folder_name, "—", "—", "—", "—", "[yellow]skipped[/yellow]")
        else:
            ratio_str = (
                f"[green]{best_r:.2f}[/green]"
                if best_r >= 0.8
                else f"[dim]{best_r:.2f}[/dim]"
            )
            table.add_row(
                folder_name,
                str(n_candidates),
                TIER_STYLE[tier],
                ratio_str,
                f"{size_kb} KB",
                "[green]✓[/green]",
            )

    console.print(table)
    console.print(
        f"\n[bold green]{selected}[/bold green] images copied, "
        f"[yellow]{skipped}[/yellow] folders skipped."
    )

    if detail_logs:
        with open(LOG_FILE, "w") as log_file:
            log_console = Console(file=log_file, no_color=True, highlight=False)
            for folder_name, candidates, best_path in detail_logs:
                detail = Table(
                    title=folder_name,
                    show_lines=False,
                    header_style="bold",
                    title_justify="left",
                )
                detail.add_column("Image", no_wrap=True)
                detail.add_column("Person", justify="center")
                detail.add_column("Car", justify="center")
                detail.add_column("Ratio", justify="right")
                detail.add_column("", justify="center")

                for path, has_person, has_car, r in candidates:
                    filename = os.path.basename(path)
                    detail.add_row(
                        filename,
                        "yes" if has_person else "no",
                        "yes" if has_car else "no",
                        f"{r:.3f}",
                        "<-- best" if path == best_path else "",
                    )

                log_console.print(detail)
                log_console.print()

        console.print(f"\n[dim]Per-image scores logged to {LOG_FILE}[/dim]")


if __name__ == "__main__":
    copy_best_images()
