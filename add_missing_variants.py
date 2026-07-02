#!/usr/bin/env python3
"""Add missing catalog variants and fetch assets from spritelocker.com."""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "https://spritelocker.com"
CONFIG_FILE = Path("sprites-config.json")
HD_DIR = Path("sprites_hd")
NAMED_DIR = Path("sprites_named")
MAP_FILE = Path("sprites-hd-map.json")

ADDITIONS = [
    {
        "spriteId": "fishy",
        "id": "fishy-gummy",
        "materialId": "gummy",
        "output": "Fishy_Gummy.png",
        "remote": "/sprites/fishy_candy.webp",
    },
    {
        "spriteId": "air",
        "id": "air-holofoil",
        "materialId": "holofoil",
        "output": "Air_Holofoil.png",
        "remote": "/sprites/air_holo.webp",
    },
    {
        "spriteId": "seven",
        "id": "seven-holofoil",
        "materialId": "holofoil",
        "output": "Seven_Holofoil.png",
        "remote": "/sprites/seven_holofoil.webp",
    },
]

MATERIAL_ORDER = ["base", "gold", "gummy", "galaxy", "holofoil", "gem", "cube", "quack"]


def download(url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "sprites-tracker/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            dest.write_bytes(resp.read())
        return True
    except urllib.error.HTTPError:
        return False


def webp_to_png(webp: Path, png: Path) -> bool:
    if not webp.exists():
        return False
    png.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["sips", "-s", "format", "png", str(webp), "--out", str(png)],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and png.exists()


def sort_sprites(sprites: list[dict]) -> list[dict]:
    def key(sprite: dict) -> int:
        material = sprite.get("materialId", "base")
        try:
            return MATERIAL_ORDER.index(material)
        except ValueError:
            return 99

    return sorted(sprites, key=key)


def group_for_sprite(config: dict, sprite_id: str) -> dict | None:
    for group in config.get("groups", []):
        if group.get("spriteId") == sprite_id:
            return group
    return None


def rebuild_catalog(config: dict) -> list[dict]:
    from apply_labels import material_label, sprite_label

    catalog: list[dict] = []
    for group in config.get("groups", []):
        sprite_id = group.get("spriteId")
        for sprite in group.get("sprites", []):
            material_id = sprite.get("materialId", "base")
            source = sprite.get("source")
            catalog.append(
                {
                    "id": sprite["id"],
                    "spriteId": sprite_id,
                    "sprite": sprite_label(config, sprite_id),
                    "materialId": material_id,
                    "material": material_label(config, material_id),
                    "source": f"sprites/{source}" if source else None,
                    "output": f"sprites_named/{sprite['output']}",
                    "filename": sprite["output"],
                    "group_id": group["id"],
                }
            )
    return catalog


def add_to_config(config: dict) -> list[dict]:
    added: list[dict] = []
    existing_ids = {
        sprite["id"]
        for group in config.get("groups", [])
        for sprite in group.get("sprites", [])
    }

    for item in ADDITIONS:
        if item["id"] in existing_ids:
            print(f"  skip {item['id']} (already in config)")
            continue
        group = group_for_sprite(config, item["spriteId"])
        if not group:
            raise SystemExit(f"Missing group for {item['spriteId']}")
        group["sprites"].append(
            {
                "id": item["id"],
                "materialId": item["materialId"],
                "output": item["output"],
            }
        )
        group["sprites"] = sort_sprites(group["sprites"])
        added.append(item)
        print(f"  added {item['spriteId']} / {item['materialId']} -> {item['output']}")
    return added


def fetch_assets(added: list[dict]) -> tuple[dict[str, str], dict[str, str]]:
    by_id: dict[str, str] = {}
    by_key: dict[str, str] = {}
    for item in added:
        webp_name = item["remote"].rsplit("/", 1)[-1]
        webp_path = HD_DIR / webp_name
        png_path = NAMED_DIR / item["output"]
        url = f"{BASE_URL}{item['remote']}"
        if not download(url, webp_path):
            raise SystemExit(f"Failed to download {url}")
        if not webp_to_png(webp_path, png_path):
            raise SystemExit(f"Failed to convert {webp_path} -> {png_path}")
        rel = str(webp_path).replace("\\", "/")
        by_id[item["id"]] = rel
        by_key[f"{item['spriteId']}:{item['materialId']}"] = rel
        print(f"  OK  {webp_name} -> {item['output']}")
    return by_id, by_key


def main() -> None:
    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    print("Updating config...")
    added = add_to_config(config)
    if not added:
        print("Nothing to add.")
        return

    print("Fetching assets...")
    new_by_id, new_by_key = fetch_assets(added)

    catalog = rebuild_catalog(config)
    config["catalog"] = catalog
    config["total"] = len(catalog)

    if MAP_FILE.exists():
        hd_map = json.loads(MAP_FILE.read_text(encoding="utf-8"))
    else:
        hd_map = {"byId": {}, "byKey": {}}

    by_id = dict(hd_map.get("byId") or {})
    by_key = dict(hd_map.get("byKey") or {})
    by_id.update(new_by_id)
    by_key.update(new_by_key)
    hd_map["byId"] = by_id
    hd_map["byKey"] = by_key
    hd_map["downloaded"] = len(by_id)

    CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    MAP_FILE.write_text(json.dumps(hd_map, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\nCatalog: {len(catalog)} entries (+{len(added)})")


if __name__ == "__main__":
    main()
