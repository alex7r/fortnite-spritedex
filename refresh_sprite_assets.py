#!/usr/bin/env python3
"""Re-download HD sprites from spritelocker.com and refresh sprites_named PNGs."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from fetch_spritelocker import (
    BASE_URL,
    MAP_FILE,
    OUTPUT_DIR,
    spritelocker_path,
)

CONFIG_FILE = Path("sprites-config.json")
NAMED_DIR = Path("sprites_named")
SOURCE_DIR = Path("sprites")


def download(path: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(f"{BASE_URL}{path}", headers={"User-Agent": "sprites-tracker/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            dest.write_bytes(resp.read())
        return True
    except urllib.error.HTTPError:
        return False


def webp_to_png(webp: Path, png: Path) -> bool:
    png.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["sips", "-s", "format", "png", str(webp), "--out", str(png)],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and png.exists()


def png_from_source(source: str, png: Path) -> bool:
    src = SOURCE_DIR / source
    if not src.exists():
        return False
    png.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["sips", "-s", "format", "png", str(src), "--out", str(png)],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and png.exists()


def catalog_for_sprites(config: dict, sprite_ids: set[str]) -> list[dict]:
    return [item for item in config.get("catalog", []) if item.get("spriteId") in sprite_ids]


def refresh_sprites(sprite_ids: set[str]) -> None:
    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    items = catalog_for_sprites(config, sprite_ids)

    if MAP_FILE.exists():
        hd_map = json.loads(MAP_FILE.read_text(encoding="utf-8"))
    else:
        hd_map = {"byId": {}, "byKey": {}}

    by_id: dict[str, str] = dict(hd_map.get("byId") or {})
    by_key: dict[str, str] = dict(hd_map.get("byKey") or {})

    ok = 0
    fallback = 0
    failed = 0

    for item in items:
        item_id = item["id"]
        sprite_id = item["spriteId"]
        material_id = item.get("materialId", "base")
        sprite_key = f"{sprite_id}:{material_id}"
        filename = item.get("filename") or Path(item.get("output", "")).name
        png_path = NAMED_DIR / filename

        remote = spritelocker_path(sprite_id, material_id)
        if remote:
            webp_name = remote.rsplit("/", 1)[-1]
            webp_path = OUTPUT_DIR / webp_name
            if download(remote, webp_path) and webp_to_png(webp_path, png_path):
                rel = str(webp_path).replace("\\", "/")
                by_id[item_id] = rel
                by_key[sprite_key] = rel
                ok += 1
                print(f"  OK   {sprite_id}/{material_id} <- {webp_name}")
                continue
            print(f"  FAIL remote {remote} ({filename})")

        # No HD on Sprite Locker — use cropped source if available.
        source = item.get("source", "")
        source_file = Path(source).name if source else ""
        group_sprite = next(
            (
                s
                for group in config.get("groups", [])
                if group.get("spriteId") == sprite_id
                for s in group.get("sprites", [])
                if s.get("id") == item_id
            ),
            None,
        )
        if group_sprite and group_sprite.get("source"):
            source_file = group_sprite["source"]

        by_id.pop(item_id, None)
        by_key.pop(sprite_key, None)

        if source_file and png_from_source(source_file, png_path):
            fallback += 1
            print(f"  LOCAL {sprite_id}/{material_id} <- sprites/{source_file}")
            continue

        failed += 1
        print(f"  MISS {sprite_id}/{material_id} ({filename})")

    # Remove stale HD files for refreshed sprites when no longer mapped.
    mapped_webp = {Path(path).name for path in by_id.values()}
    for sprite_id in sprite_ids:
        for path in list(OUTPUT_DIR.glob(f"{'air' if sprite_id == 'air' else 'seven'}*.webp")):
            if path.name not in mapped_webp and sprite_id in path.name:
                pass  # keep unrelated files

    stale = []
    if "air" in sprite_ids:
        stale_path = OUTPUT_DIR / "air_gem.webp"
        if stale_path.exists() and "air:gem" not in by_key:
            stale.append(stale_path)

    for path in stale:
        path.unlink()
        print(f"  removed stale {path.name}")

    hd_map["byId"] = by_id
    hd_map["byKey"] = by_key
    hd_map["downloaded"] = len(by_id)
    MAP_FILE.write_text(json.dumps(hd_map, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\nHD refreshed: {ok}, local fallback: {fallback}, failed: {failed}")
    print(f"Map: {MAP_FILE}")


def main() -> None:
    targets = set(sys.argv[1:]) if len(sys.argv) > 1 else {"air", "seven"}
    print(f"Refreshing: {', '.join(sorted(targets))}")
    refresh_sprites(targets)


if __name__ == "__main__":
    main()
