"""
02_copy.py — Select the best image from each audit folder and copy it to the frontend.

Expects 01_scrape.py to have already run and populated OUTPUT_DIR with subfolders,
each containing an `images/` subdirectory of candidate photos.
"""

import os
import shutil

from PIL import Image
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn
from rich.table import Table

console = Console()

# --- Configuration ---
OUTPUT_DIR = "data/download"
PRIMARY_IMAGE_DIR = "app/public/data/images"


def get_image_score(image_path):
    """
    Calculates a quality score. Higher scores go to images that:
    1. Have human skin tones (likely a person in shot).
    2. Have higher resolution.
    3. Have standard photographic aspect ratios.
    """
    try:
        with Image.open(image_path) as img:
            w, h = img.size
            score = (w * h) / 1000

            aspect_ratio = w / h
            if not (0.7 <= aspect_ratio <= 1.5):
                score *= 0.6

            ycbcr = img.convert("YCbCr")
            skin_pixels = 0
            step = 10  # Sample ~1% of pixels for performance

            for x in range(0, w, step):
                for y in range(0, h, step):
                    _, cb, cr = ycbcr.getpixel((x, y))
                    if 80 <= cb <= 120 and 133 <= cr <= 173:
                        skin_pixels += 1

            sample_count = (w / step) * (h / step)
            if sample_count > 0 and (skin_pixels / sample_count) > 0.01:
                score *= 2.5

            return score
    except Exception:
        return 0


def copy_best_images():
    """Score all candidate images per folder and copy the winner to the frontend."""
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

    results = []  # (folder_name, n_candidates, best_score) or None for skipped

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
                results.append((folder_name, 0, None))
                progress.advance(task)
                continue

            img_files = [
                os.path.join(images_path, f)
                for f in os.listdir(images_path)
                if f.startswith("image_")
            ]
            if not img_files:
                results.append((folder_name, 0, None))
                progress.advance(task)
                continue

            scored = sorted(
                ((f, get_image_score(f)) for f in img_files),
                key=lambda x: x[1],
                reverse=True,
            )
            best_img, best_score = scored[0]
            ext = best_img.rsplit(".", 1)[-1]
            shutil.copy2(
                best_img, os.path.join(PRIMARY_IMAGE_DIR, f"{folder_name}.{ext}")
            )
            results.append((folder_name, len(img_files), best_score))
            progress.advance(task)

    # Summary table
    table = Table(title="Results", show_lines=False, header_style="bold cyan")
    table.add_column("Folder", style="dim", no_wrap=False)
    table.add_column("Candidates", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Status", justify="center")

    selected = sum(1 for _, n, s in results if s is not None)
    skipped = len(results) - selected

    for folder_name, n_candidates, score in results:
        if score is None:
            table.add_row(folder_name, "—", "—", "[yellow]skipped[/yellow]")
        else:
            table.add_row(
                folder_name,
                str(n_candidates),
                str(int(score)),
                "[green]✓[/green]",
            )

    console.print(table)
    console.print(
        f"\n[bold green]{selected}[/bold green] images copied, "
        f"[yellow]{skipped}[/yellow] folders skipped."
    )


if __name__ == "__main__":
    copy_best_images()
