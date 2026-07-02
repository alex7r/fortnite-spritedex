#!/usr/bin/env python3
"""Extract individual Fortnite Klombo sprites from a sprite sheet."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

INPUT_IMAGE = Path("image.png")
OUTPUT_DIR = Path("sprites")

SPRITE_HEIGHT = 115
SPRITE_WIDTH = 80
CHECKBOX_GAP = 5


def detect_checkboxes(arr: np.ndarray) -> list[dict]:
    rgb = arr[:, :, :3].astype(float)
    bright = rgb.mean(axis=2)
    dark = (bright < 50) & (arr[:, :, 3] > 200)

    labeled, num = ndimage.label(dark)
    checkboxes: list[dict] = []

    for i in range(1, num + 1):
        ys, xs = np.where(labeled == i)
        area = len(ys)
        ymin, ymax = ys.min(), ys.max()
        xmin, xmax = xs.min(), xs.max()
        bw, bh = xmax - xmin + 1, ymax - ymin + 1

        if not (28 <= bw <= 42 and 28 <= bh <= 42 and 150 <= area <= 500):
            continue

        sub = dark[ymin : ymax + 1, xmin : xmax + 1]
        fill_ratio = sub.sum() / (bw * bh)
        if not (0.08 <= fill_ratio <= 0.45):
            continue

        checkboxes.append(
            {
                "x": int(xmin),
                "y": int(ymin),
                "cx": (xmin + xmax) / 2,
                "cy": (ymin + ymax) / 2,
            }
        )

    return sorted(checkboxes, key=lambda c: (c["cy"], c["cx"]))


def cluster_rows(checkboxes: list[dict], threshold: float = 35) -> list[list[dict]]:
    if not checkboxes:
        return []

    rows: list[list[dict]] = [[checkboxes[0]]]
    for cb in checkboxes[1:]:
        row_mean_y = np.mean([c["cy"] for c in rows[-1]])
        if abs(cb["cy"] - row_mean_y) < threshold:
            rows[-1].append(cb)
        else:
            rows.append([cb])

    # Drop tiny outlier clusters between real sprite rows.
    rows = [sorted(row, key=lambda c: c["cx"]) for row in rows if len(row) >= 2]
    return rows


def remove_checkbox_artifacts(sprite: Image.Image) -> Image.Image:
    """Remove stray checkbox outlines that leak into neighboring crops."""
    arr = np.array(sprite)
    h, w = arr.shape[:2]
    rgb = arr[:, :, :3].astype(float)
    bright = rgb.mean(axis=2)

    dark = (bright < 45) & (arr[:, :, 3] > 200)
    labeled, num = ndimage.label(dark)

    remove_mask = np.zeros((h, w), dtype=bool)
    for i in range(1, num + 1):
        ys, xs = np.where(labeled == i)
        bw = xs.max() - xs.min() + 1
        bh = ys.max() - ys.min() + 1
        area = len(ys)
        if 24 <= bw <= 48 and 24 <= bh <= 48 and 120 <= area <= 650:
            remove_mask[ys, xs] = True

    if not remove_mask.any():
        return sprite

    arr = arr.copy()
    arr[remove_mask, 3] = 0
    return Image.fromarray(arr)


def trim_transparent(sprite: Image.Image) -> Image.Image:
    arr = np.array(sprite)
    alpha = arr[:, :, 3]
    rgb = arr[:, :, :3].astype(float)
    bright = rgb.mean(axis=2)

    # Ignore background, checkbox outlines, and faint edge artifacts.
    content = (alpha > 10) & (bright > 62) & ~(
        (rgb[:, :, 0] > 235) & (rgb[:, :, 1] > 235) & (rgb[:, :, 2] > 235)
    )
    if not content.any():
        return sprite

    ys, xs = np.where(content)
    pad = 2
    x1 = max(0, int(xs.min()) - pad)
    y1 = max(0, int(ys.min()) - pad)
    x2 = min(sprite.width - 1, int(xs.max()) + pad)
    y2 = min(sprite.height - 1, int(ys.max()) + pad)

    # Drop top rows that only contain leaked checkbox fragments.
    dark = bright < 45
    for _ in range(8):
        row_slice = dark[y1 : y1 + 1, x1 : x2 + 1]
        if row_slice.mean() > 0.12:
            y1 += 1
        else:
            break

    return sprite.crop((x1, y1, x2 + 1, y2 + 1))


def crop_sprite(img: Image.Image, checkbox: dict) -> Image.Image:
    cx = checkbox["cx"]
    left = int(cx - SPRITE_WIDTH / 2)
    right = int(cx + SPRITE_WIDTH / 2)
    top = int(checkbox["y"] - SPRITE_HEIGHT - CHECKBOX_GAP)
    bottom = int(checkbox["y"] - 2)

    left = max(0, left)
    top = max(0, top)
    right = min(img.width, right)
    bottom = min(img.height, bottom)

    sprite = img.crop((left, top, right, bottom))
    sprite = remove_checkbox_artifacts(sprite)
    return trim_transparent(sprite)


def main() -> None:
    img = Image.open(INPUT_IMAGE).convert("RGBA")
    arr = np.array(img)

    h, w = arr.shape[:2]
    # Mask watermark area
    arr_masked = arr.copy()
    arr_masked[h - 65 :, w - 210 :, 3] = 0

    checkboxes = detect_checkboxes(arr_masked)
    rows = cluster_rows(checkboxes)

    OUTPUT_DIR.mkdir(exist_ok=True)

    total = 0
    manifest_lines = ["# Fortnite Klombo sprites extracted from image.png", ""]

    for row_idx, row in enumerate(rows, start=1):
        for col_idx, cb in enumerate(row, start=1):
            sprite = crop_sprite(img, cb)
            filename = f"row{row_idx:02d}_col{col_idx:02d}.png"
            out_path = OUTPUT_DIR / filename
            sprite.save(out_path)
            total += 1
            manifest_lines.append(f"{filename} — row {row_idx}, column {col_idx}")

    manifest_path = OUTPUT_DIR / "README.txt"
    manifest_path.write_text("\n".join(manifest_lines) + f"\n\nTotal: {total} sprites\n", encoding="utf-8")

    print(f"Extracted {total} sprites into {OUTPUT_DIR}/")
    print(f"Rows: {len(rows)}")
    for i, row in enumerate(rows, start=1):
        print(f"  Row {i}: {len(row)} sprites")


if __name__ == "__main__":
    main()
