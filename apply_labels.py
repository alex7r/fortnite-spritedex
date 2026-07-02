#!/usr/bin/env python3
"""Apply sprite labels: flat English filenames from sprites-config.json."""

from __future__ import annotations

import json
import re
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

CONFIG_FILE = Path("sprites-config.json")
SOURCE_DIR = Path("sprites")
OUTPUT_DIR = Path("sprites_named")
MANIFEST_OUT = OUTPUT_DIR / "catalog.json"

DEFAULT_MATERIAL = "base"
INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00]')


def sanitize(part: str) -> str:
    part = part.strip()
    part = INVALID_CHARS.sub("_", part)
    return part or "unnamed"


def sprite_label(config: dict, sprite_id: str) -> str:
    return config["i18n"]["sprites"][sprite_id]["en"]


def material_label(config: dict, material_id: str) -> str:
    return config["i18n"]["materials"][material_id]["en"]


def output_filename(config: dict, sprite_id: str, material_id: str) -> str:
    sep = config.get("nameSeparator", "_")
    sprite = sanitize(sprite_label(config, sprite_id).replace(" ", ""))
    material = sanitize(material_label(config, material_id).replace(" ", ""))
    return f"{sprite}{sep}{material}.png"


def build_entries(config: dict) -> list[dict]:
    entries: list[dict] = []
    for group in config["groups"]:
        gid = group["spriteId"]
        for sprite in group["sprites"]:
            material_id = sprite.get("materialId", DEFAULT_MATERIAL)
            entries.append(
                {
                    "sprite": sprite,
                    "group": group,
                    "source": sprite["source"],
                    "sprite_id": gid,
                    "material_id": material_id,
                    "group_row_id": group["id"],
                }
            )
    return entries


def assign_output_names(config: dict, entries: list[dict]) -> None:
    used: dict[str, int] = defaultdict(int)
    for entry in entries:
        base = output_filename(config, entry["sprite_id"], entry["material_id"]).removesuffix(".png")
        used[base] += 1
        count = used[base]
        filename = f"{base}.png" if count == 1 else f"{base}_{count:02d}.png"
        entry["output"] = filename


def main() -> None:
    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    entries = build_entries(config)
    assign_output_names(config, entries)

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir()

    catalog: list[dict] = []
    missing: list[str] = []

    for entry in entries:
        src = SOURCE_DIR / entry["source"]
        dest = OUTPUT_DIR / entry["output"]
        entry["sprite"]["output"] = entry["output"]
        entry["sprite"]["materialId"] = entry["material_id"]

        if not src.exists():
            missing.append(entry["source"])
            continue

        shutil.copy2(src, dest)
        catalog.append(
            {
                "id": entry["sprite"]["id"],
                "spriteId": entry["sprite_id"],
                "sprite": sprite_label(config, entry["sprite_id"]),
                "materialId": entry["material_id"],
                "material": material_label(config, entry["material_id"]),
                "source": str(src),
                "output": str(dest),
                "filename": entry["output"],
                "group_id": entry["group_row_id"],
            }
        )

    config["updatedAt"] = datetime.now(timezone.utc).isoformat()
    config["catalog"] = catalog
    config["total"] = len(catalog)
    CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    MANIFEST_OUT.write_text(
        json.dumps(
            {
                "version": config.get("version", 3),
                "total": len(catalog),
                "sprites": catalog,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Saved {len(catalog)} sprites to {OUTPUT_DIR}/")
    for item in catalog[:5]:
        print(f"  {item['filename']}  <-  {Path(item['source']).name}")
    if missing:
        print(f"Missing ({len(missing)}):", ", ".join(missing))


if __name__ == "__main__":
    main()
