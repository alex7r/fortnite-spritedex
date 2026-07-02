#!/usr/bin/env python3
"""Apply sprite labels: flat filenames from sprites-config.json."""

from __future__ import annotations

import json
import re
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

CONFIG_FILE = Path("sprites-config.json")
LEGACY_LABELS_FILE = Path("sprites-labels.json")

DEFAULT_MATERIAL = "обычный"
INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00]')

MATERIAL_ALIASES = {
    "золотой": "Золото",
    "золото": "Золото",
    "кристалл": "Кристал",
    "кристал": "Кристал",
    "мармелад": "Мармелад",
    "галактика": "Галактика",
    "пурпур": "Пурпур",
    "пурпру": "Пурпур",
    "обычный": "обычный",
}


def normalize_material(material: str) -> str:
    key = material.strip().casefold()
    return MATERIAL_ALIASES.get(key, material.strip())


def sanitize(part: str) -> str:
    part = part.strip()
    part = INVALID_CHARS.sub("_", part)
    return part or "unnamed"


def sprite_id_from_source(source: str) -> str:
    return Path(source).stem


def material_for(sprite: dict) -> str:
    material = sprite.get("type", "").strip()
    if not material:
        material = sprite.get("name", "").strip()
    material = material or DEFAULT_MATERIAL
    return sanitize(normalize_material(material))


def default_config() -> dict:
    return {
        "version": 2,
        "sourceDir": "sprites",
        "outputDir": "sprites_named",
        "defaultMaterial": DEFAULT_MATERIAL,
        "nameSeparator": "_",
        "materialAliases": MATERIAL_ALIASES,
        "typeSuggestions": [
            "обычный",
            "Золото",
            "Мармелад",
            "Галактика",
            "Кристал",
            "Пурпур",
        ],
        "groups": [],
    }


def migrate_legacy_labels() -> dict:
    data = json.loads(LEGACY_LABELS_FILE.read_text(encoding="utf-8"))
    config = default_config()
    config["groups"] = data.get("groups", [])
    return config


def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    if LEGACY_LABELS_FILE.exists():
        config = migrate_legacy_labels()
        save_config(config)
        return config
    raise SystemExit(f"No config found: {CONFIG_FILE}")


def save_config(config: dict) -> None:
    CONFIG_FILE.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_entries(config: dict) -> list[dict]:
    entries: list[dict] = []
    for group in config["groups"]:
        character = sanitize(group["name"])
        for sprite in group["sprites"]:
            source = sprite.get("source") or sprite.get("file")
            if not source:
                continue
            entries.append(
                {
                    "sprite": sprite,
                    "group": group,
                    "source": Path(source).name,
                    "character": character,
                    "material": material_for(sprite),
                    "sprite_id": sprite.get("id") or sprite_id_from_source(source),
                }
            )
    return entries


def assign_output_names(entries: list[dict], separator: str) -> None:
    used: dict[str, int] = defaultdict(int)

    for entry in entries:
        base = f"{entry['character']}{separator}{entry['material']}"
        used[base] += 1
        count = used[base]
        filename = f"{base}.png" if count == 1 else f"{base}_{count:02d}.png"
        entry["output"] = filename


def sync_sprite_fields(entry: dict) -> None:
    sprite = entry["sprite"]
    sprite["id"] = entry["sprite_id"]
    sprite["source"] = entry["source"]
    sprite["output"] = entry["output"]
    sprite["character"] = entry["character"]
    sprite["material"] = entry["material"]
    if sprite.get("type", "").strip():
        sprite["type"] = entry["material"] if sprite["type"].strip().casefold() in MATERIAL_ALIASES else sprite["type"].strip()
    sprite.pop("file", None)
    sprite.pop("name", None)


def remove_legacy_outputs() -> None:
    for path in (Path("sprites_organized"), Path("sprites_by_material")):
        if path.exists():
            shutil.rmtree(path)


def main() -> None:
    config = load_config()
    source_dir = Path(config.get("sourceDir", "sprites"))
    output_dir = Path(config.get("outputDir", "sprites_named"))
    separator = config.get("nameSeparator", "_")

    entries = build_entries(config)
    assign_output_names(entries, separator)

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir()

    missing: list[str] = []
    catalog: list[dict] = []

    for entry in entries:
        src = source_dir / entry["source"]
        dest = output_dir / entry["output"]
        sync_sprite_fields(entry)

        if not src.exists():
            missing.append(entry["source"])
            continue

        shutil.copy2(src, dest)
        catalog.append(
            {
                "id": entry["sprite_id"],
                "character": entry["character"],
                "material": entry["material"],
                "source": str(source_dir / entry["source"]),
                "output": str(dest),
                "filename": entry["output"],
                "group_id": entry["group"]["id"],
                "group_name": entry["group"]["name"],
            }
        )

    config["updatedAt"] = datetime.now(timezone.utc).isoformat()
    config["catalog"] = catalog
    config["total"] = len(catalog)
    save_config(config)
    remove_legacy_outputs()

    characters = sorted({e["character"] for e in catalog})
    materials = sorted({e["material"] for e in catalog})

    print(f"Saved {len(catalog)} sprites to {output_dir}/")
    print(f"Config updated: {CONFIG_FILE}")
    print(f"Characters: {len(characters)}, Materials: {len(materials)}")
    print("Examples:")
    for item in catalog[:5]:
        print(f"  {item['filename']}  <-  {Path(item['source']).name}")

    if missing:
        print(f"\nMissing source files ({len(missing)}):")
        for name in missing:
            print(f"  {name}")


if __name__ == "__main__":
    main()
