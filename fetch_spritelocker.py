#!/usr/bin/env python3
"""Scrape and download sprite images from spritelocker.com."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "https://spritelocker.com"
CONFIG_FILE = Path("sprites-config.json")
OUTPUT_DIR = Path("sprites_hd")
MAP_FILE = Path("sprites-hd-map.json")

SPRITE_SLUG = {
    "water": "water",
    "earth": "earth",
    "fire": "fire",
    "duck": "duck",
    "ghost": "ghost",
    "king": "king",
    "zero-point": "zeropoint",
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

# spritelocker.com uses non-standard slugs for some holofoil assets.
HOLOFOIL_SLUG_OVERRIDE = {
    "ghost": "holo",
}


def scrape_paths() -> list[str]:
    req = urllib.request.Request(f"{BASE_URL}/", headers={"User-Agent": "sprites-tracker/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    return sorted(set(re.findall(r"/sprites/[a-z0-9_]+\.webp", html)))


def spritelocker_path(sprite_id: str, material_id: str) -> str | None:
    slug = SPRITE_SLUG.get(sprite_id)
    if not slug:
        return None
    if material_id == "holofoil":
        variant = HOLOFOIL_SLUG_OVERRIDE.get(sprite_id, "holofoil")
    else:
        variant = MATERIAL_SLUG.get(material_id)
    if not variant:
        return None
    path = f"/sprites/{slug}_{variant}.webp"
    return path


def download(path: str, dest: Path) -> bool:
    url = f"{BASE_URL}{path}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "sprites-tracker/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            dest.write_bytes(resp.read())
        return True
    except urllib.error.HTTPError:
        return False


def main() -> None:
    available = set(scrape_paths())
    print(f"Found {len(available)} sprite paths on {BASE_URL}")

    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    catalog = config.get("catalog") or []

    existing_map: dict = {}
    if MAP_FILE.exists():
        existing_map = json.loads(MAP_FILE.read_text(encoding="utf-8"))

    OUTPUT_DIR.mkdir(exist_ok=True)

    by_id: dict[str, str] = dict(existing_map.get("byId") or {})
    by_key: dict[str, str] = dict(existing_map.get("byKey") or {})
    downloaded = 0
    missing = 0

    for item in catalog:
        sprite_id = item.get("spriteId")
        material_id = item.get("materialId", "base")
        sprite_key = f"{sprite_id}:{material_id}"
        remote = spritelocker_path(sprite_id, material_id)
        if not remote:
            missing += 1
            continue

        filename = remote.rsplit("/", 1)[-1]
        dest = OUTPUT_DIR / filename
        if download(remote, dest):
            rel = str(dest).replace("\\", "/")
            by_id[item["id"]] = rel
            by_key[sprite_key] = rel
            downloaded += 1
            print(f"  OK  {filename}  <-  {item.get('filename', item['id'])}")
        else:
            missing += 1
            print(f"  FAIL {remote}")

    manifest = {
        "version": 1,
        "source": BASE_URL,
        "scraped": sorted(set(existing_map.get("scraped") or []) | available),
        "downloaded": len(by_id),
        "fallbackDir": "sprites_named",
        "byId": by_id,
        "byKey": by_key,
    }
    MAP_FILE.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nDownloaded {downloaded} HD sprites to {OUTPUT_DIR}/")
    print(f"Missing on spritelocker (use local): {missing}")
    print(f"Map: {MAP_FILE}")


if __name__ == "__main__":
    main()
