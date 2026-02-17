"""
02_copy.py — Select the best image from each audit folder and copy it to the frontend.

Expects 01_scrape.py to have already run and populated OUTPUT_DIR with subfolders,
each containing an `images/` subdirectory of candidate photos.

Scoring
-------
Each candidate image receives a score based on:
  1. Resolution    — base score is (width x height) / 1000.
  2. Orientation   — landscape (w >= h) is boosted (x1.3); portrait is penalized
                     (x0.8 mild, x0.5 for very narrow).
  3. Face detection — images with detected faces are boosted significantly:
       1 face → x2.5,  2 faces → x3.0,  3 faces → x3.5, etc.

Face detection uses OpenCV's Haar Cascade classifier
(haarcascade_frontalface_default.xml), a pre-trained XML model bundled with
opencv-python. The cascade scans the image at multiple scales looking for the
geometric patterns of a frontal human face.

  Pros: reliable for clear, upright frontal shots; mature and fast technology.
  Cons: works best on frontal faces — people shot from behind, at odd angles,
        or small in the frame may not be detected, falling back to the
        resolution/aspect-ratio score alone.
"""

import os
import shutil

import cv2
import numpy as np
from PIL import Image
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn
from rich.table import Table

console = Console()

# Load the face cascade once at module level
_face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# --- Configuration ---
OUTPUT_DIR = "data/download"
PRIMARY_IMAGE_DIR = "app/public/data/images"


def count_faces(image_path):
    """Return the number of faces detected in the image using OpenCV Haar cascades."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            return 0
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = _face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )
        return len(faces) if isinstance(faces, np.ndarray) else 0
    except Exception:
        return 0


def get_image_score(image_path):
    """
    Calculates a quality score. Higher scores go to images that:
    1. Contain detected faces (using OpenCV Haar cascade).
    2. Have higher resolution.
    3. Have landscape orientation (width > height).
    4. Have standard photographic aspect ratios.
    """
    try:
        with Image.open(image_path) as img:
            w, h = img.size
            score = (w * h) / 1000

            aspect_ratio = w / h
            if aspect_ratio >= 1.0:
                score *= 1.3  # boost for landscape
            elif aspect_ratio >= 0.7:
                score *= 0.8  # mild penalty for portrait
            else:
                score *= 0.5  # strong penalty for very tall/narrow

            n_faces = count_faces(image_path)
            if n_faces > 0:
                score *= 2.5 + (0.5 * (n_faces - 1))  # extra boost per additional face

            return score, n_faces
    except Exception:
        return 0, 0


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

    results = []  # (folder_name, n_candidates, best_score, n_faces) or score=None for skipped

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
                results.append((folder_name, 0, None, 0))
                progress.advance(task)
                continue

            img_files = [
                os.path.join(images_path, f)
                for f in os.listdir(images_path)
                if f.startswith("image_")
            ]
            if not img_files:
                results.append((folder_name, 0, None, 0))
                progress.advance(task)
                continue

            scored = sorted(
                ((f, *get_image_score(f)) for f in img_files),
                key=lambda x: x[1],
                reverse=True,
            )
            best_img, best_score, best_faces = scored[0]
            ext = best_img.rsplit(".", 1)[-1]
            shutil.copy2(
                best_img, os.path.join(PRIMARY_IMAGE_DIR, f"{folder_name}.{ext}")
            )
            results.append((folder_name, len(img_files), best_score, best_faces))
            progress.advance(task)

    # Summary table
    table = Table(title="Results", show_lines=False, header_style="bold cyan")
    table.add_column("Folder", style="dim", no_wrap=False)
    table.add_column("Candidates", justify="right")
    table.add_column("Faces", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Status", justify="center")

    selected = sum(1 for _, n, s, f in results if s is not None)
    skipped = len(results) - selected

    for folder_name, n_candidates, score, n_faces in results:
        if score is None:
            table.add_row(folder_name, "—", "—", "—", "[yellow]skipped[/yellow]")
        else:
            face_str = f"[green]{n_faces}[/green]" if n_faces > 0 else "[dim]0[/dim]"
            table.add_row(
                folder_name,
                str(n_candidates),
                face_str,
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
