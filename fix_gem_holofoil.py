#!/usr/bin/env python3
"""Fix gem/holofoil variant labels and assets against spritelocker.com."""

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

SPRITE_SLUG = {
    "water": "water",
    "earth": "earth",
    "fire": "fire",
    "duck": "duck",
    "ghost": "ghost",
    "king": "king",
    "zero-point": "zeropoint",
    "air": "air",
    "seven": "seven",
    "fishy": "fishy",
    "dream": "dream",
    "burnt-peanut": "theburntpeanut",
    "punk": "punk",
    "aura": "drifter",
    "boss": "boss",
    "striker": "soccer",
    "grim": "grimreaper",
    "demon": "demon",
}

MATERIAL_SLUG = {
    "base": "basic",
    "gold": "gold",
    "gummy": "candy",
    "galaxy": "galaxy",
    "gem": "gem",
    "holofoil": "holofoil",
    "cube": "cube",
    "quack": "quack",
}

# Relabel existing catalog rows (materialId + output filename).
RELABEL_RENAME_FROM = {
    "row02_col05": "Earth_Holofoil.png",
    "row03_col05": "Fire_Gem.png",
    "row04_col11": "Demon_Holofoil.png",
    "row05_col05": "Ghost_Gem.png",
    "row06_col05": "King_Gem.png",
    "row06_col10": "Aura_Holofoil.png",
    "row05_col14": "Striker_Gem.png",
}

RELABEL = {
    "row02_col05": ("gem", "Earth_Gem.png"),
    "row03_col05": ("holofoil", "Fire_Holofoil.png"),
    "row04_col11": ("gem", "Demon_Gem.png"),
    "row05_col05": ("holofoil", "Ghost_Holofoil.png"),
    "row06_col05": ("holofoil", "King_Holofoil.png"),
    "row06_col10": ("gem", "Aura_Gem.png"),
    "row05_col14": ("holofoil", "Striker_Holofoil.png"),
}

REMOVE_IDS = {"row04_col05", "row02_col10", "row07_col05"}

OBSOLETE_FILES = [
    "Earth_Holofoil.png",
    "Fire_Gem.png",
    "Duck_Holofoil.png",
    "Dream_Gem.png",
    "ZeroPoint_Holofoil.png",
    "Demon_Holofoil.png",
    "Aura_Holofoil.png",
    "Ghost_Gem.png",
    "King_Gem.png",
    "Striker_Gem.png",
    "earth_holofoil.webp",
    "fire_gem.webp",
    "duck_holofoil.webp",
    "dream_gem.webp",
    "zeropoint_holofoil.webp",
    "demon_holofoil.webp",
    "drifter_holofoil.webp",
    "ghost_gem.webp",
    "king_gem.webp",
    "soccer_gem.webp",
]


def remote_path(sprite_id: str, material_id: str) -> str | None:
    slug = SPRITE_SLUG.get(sprite_id)
    if not slug:
        return None
    if material_id == "holofoil":
        variant = {"ghost": "holo"}.get(sprite_id, "holofoil")
    else:
        variant = MATERIAL_SLUG.get(material_id)
    if not variant:
        return None
    return f"/sprites/{slug}_{variant}.webp"


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


def apply_group_fixes(config: dict) -> None:
    for group in config.get("groups", []):
        sprites = group.get("sprites", [])
        group["sprites"] = [s for s in sprites if s.get("id") not in REMOVE_IDS]
        for sprite in group["sprites"]:
            fix = RELABEL.get(sprite.get("id"))
            if not fix:
                continue
            material_id, output = fix
            sprite["materialId"] = material_id
            sprite["output"] = output


def rebuild_catalog(config: dict) -> list[dict]:
    from apply_labels import material_label, sprite_label

    catalog: list[dict] = []
    for group in config.get("groups", []):
        sprite_id = group.get("spriteId")
        for sprite in group.get("sprites", []):
            material_id = sprite.get("materialId", "base")
            output = sprite.get("output", "")
            catalog.append(
                {
                    "id": sprite["id"],
                    "spriteId": sprite_id,
                    "sprite": sprite_label(config, sprite_id),
                    "materialId": material_id,
                    "material": material_label(config, material_id),
                    "source": f"sprites/{sprite.get('source', '')}",
                    "output": f"sprites_named/{output}",
                    "filename": output,
                    "group_id": group["id"],
                }
            )
    return catalog


def fetch_assets(catalog: list[dict]) -> tuple[dict[str, str], dict[str, str]]:
    by_id: dict[str, str] = {}
    by_key: dict[str, str] = {}
    targets = {item["id"] for item in catalog if item["id"] in RELABEL or item["id"] in {
        "row04_col06", "row02_col12", "row03_col11", "row07_col06", "row07_col11",
    }}

    for item in catalog:
        if item["id"] not in targets and item["id"] not in REMOVE_IDS:
            continue
        sprite_id = item["spriteId"]
        material_id = item["materialId"]
        remote = remote_path(sprite_id, material_id)
        if not remote:
            continue
        webp_name = remote.rsplit("/", 1)[-1]
        webp_path = HD_DIR / webp_name
        png_path = NAMED_DIR / item["filename"]
        if download(f"{BASE_URL}{remote}", webp_path):
            webp_to_png(webp_path, png_path)
            rel = str(webp_path).replace("\\", "/")
            by_id[item["id"]] = rel
            by_key[f"{sprite_id}:{material_id}"] = rel
            print(f"  OK  {webp_name} -> {item['filename']}")
        else:
            old_name = RELABEL_RENAME_FROM.get(item["id"])
            old_png = NAMED_DIR / old_name if old_name else None
            if old_png and old_png.exists() and old_name != item["filename"]:
                old_png.rename(png_path)
                print(f"  RENAME {old_name} -> {item['filename']}")
            else:
                print(f"  MISS {remote} ({item['filename']})")

    return by_id, by_key


def main() -> None:
    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    apply_group_fixes(config)
    catalog = rebuild_catalog(config)
    config["catalog"] = catalog
    config["total"] = len(catalog)
    config["version"] = 5

    print("Fetching corrected assets...")
    new_map, new_keys = fetch_assets(catalog)

    for name in OBSOLETE_FILES:
        for base in (NAMED_DIR, HD_DIR):
            path = base / name
            if path.exists():
                path.unlink()
                print(f"  removed {path}")

    if MAP_FILE.exists():
        hd_map = json.loads(MAP_FILE.read_text(encoding="utf-8"))
    else:
        hd_map = {"byId": {}, "byKey": {}}

    by_id = dict(hd_map.get("byId") or {})
    by_key = dict(hd_map.get("byKey") or {})
    for remove_id in REMOVE_IDS:
        by_id.pop(remove_id, None)
    for key, path in new_map.items():
        by_id[key] = path
    for key, path in new_keys.items():
        by_key[key] = path
    for key in list(by_key):
        if key.endswith(":holofoil") and key.split(":", 1)[0] in {
            "earth", "duck", "zero-point", "demon", "aura",
        }:
            by_key.pop(key, None)
        if key.endswith(":gem") and key.split(":", 1)[0] in {
            "fire", "ghost", "king", "striker", "dream",
        }:
            by_key.pop(key, None)

    hd_map["byId"] = by_id
    hd_map["byKey"] = by_key
    hd_map["downloaded"] = len(by_id)
    MAP_FILE.write_text(json.dumps(hd_map, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nCatalog: {len(catalog)} entries (was 87, removed {len(REMOVE_IDS)} extras)")


if __name__ == "__main__":
    main()
