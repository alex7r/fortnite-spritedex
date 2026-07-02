#!/usr/bin/env python3
"""Migrate sprites-config.json to v3 with official Fortnite names and i18n."""

from __future__ import annotations

import json
import re
from pathlib import Path

CONFIG = Path("sprites-config.json")

SPRITES = {
    "group-01": "water",
    "group-02": "earth",
    "group-03": "fire",
    "group-04": "duck",
    "group-05": "ghost",
    "group-06": "king",
    "group-07": "zero-point",
    "group-mqz37r2e": "air",
    "group-mqz38mfk": "fishy",
    "group-mqz39sxq": "dream",
    "group-mqz3ag0q": "burnt-peanut",
    "group-mqz3bjv9": "punk",
    "group-mqz3fy5d": "seven",
    "group-mqz3gb7o": "aura",
    "group-mqz3gwlg": "boss",
    "group-mqz3hc53": "striker",
    "group-mqz3htul": "grim",
    "group-mqz3ib7v": "demon",
}

SPRITE_I18N = {
    "water": {"en": "Water", "ru": "Водный"},
    "earth": {"en": "Earth", "ru": "Земля"},
    "fire": {"en": "Fire", "ru": "Огонь"},
    "duck": {"en": "Duck", "ru": "Утка"},
    "ghost": {"en": "Ghost", "ru": "Призрак"},
    "king": {"en": "King", "ru": "Король"},
    "zero-point": {"en": "Zero Point", "ru": "Нулевой"},
    "air": {"en": "Air", "ru": "Воздух"},
    "fishy": {"en": "Fishy", "ru": "Рыбка"},
    "dream": {"en": "Dream", "ru": "Сонливый"},
    "burnt-peanut": {"en": "Burnt Peanut", "ru": "Орех"},
    "punk": {"en": "Punk", "ru": "Панк"},
    "seven": {"en": "Seven", "ru": "Семёрка"},
    "aura": {"en": "Aura", "ru": "Аура"},
    "boss": {"en": "Boss", "ru": "Босс"},
    "striker": {"en": "Striker", "ru": "Страйкер"},
    "grim": {"en": "Grim", "ru": "Грим"},
    "demon": {"en": "Demon", "ru": "Демон"},
}

MATERIAL_I18N = {
    "base": {"en": "Base", "ru": "Обычный"},
    "gold": {"en": "Gold", "ru": "Золото"},
    "gummy": {"en": "Gummy", "ru": "Мармелад"},
    "galaxy": {"en": "Galaxy", "ru": "Галактика"},
    "holofoil": {"en": "Holofoil", "ru": "Голофоль"},
    "gem": {"en": "Gem", "ru": "Самоцвет"},
}

MATERIAL_ALIASES = {
    "": "base",
    "base": "base",
    "обычный": "base",
    "ordinary": "base",
    "default": "base",
    "gold": "gold",
    "золото": "gold",
    "золотой": "gold",
    "gummy": "gummy",
    "мармелад": "gummy",
    "candy": "gummy",
    "galaxy": "galaxy",
    "галактика": "galaxy",
    "holofoil": "holofoil",
    "кристал": "holofoil",
    "кристалл": "holofoil",
    "crystal": "holofoil",
    "gem": "gem",
    "пурпур": "gem",
    "пурпру": "gem",
    "purple": "gem",
}

FILENAME_PART = {
    sprite_id: SPRITE_I18N[sprite_id]["en"].replace(" ", "")
    for sprite_id in SPRITE_I18N
}


def filename_part_sprite(sprite_id: str) -> str:
    return FILENAME_PART[sprite_id]


def filename_part_material(material_id: str) -> str:
    return MATERIAL_I18N[material_id]["en"].replace(" ", "")


def resolve_material_id(sprite: dict) -> str:
    raw = (sprite.get("materialId") or sprite.get("type") or "").strip()
    if not raw:
        raw = (sprite.get("name") or sprite.get("material") or "").strip()
    key = raw.casefold()
    return MATERIAL_ALIASES.get(key, MATERIAL_ALIASES.get(raw.lower(), "base"))


def output_name(sprite_id: str, material_id: str, separator: str = "_") -> str:
    return f"{filename_part_sprite(sprite_id)}{separator}{filename_part_material(material_id)}.png"


def migrate(data: dict) -> dict:
    groups = []
    for group in data["groups"]:
        gid = group["id"]
        sprite_id = group.get("spriteId") or SPRITES.get(gid)
        if not sprite_id:
            raise ValueError(f"Unknown group: {gid}")

        sprites = []
        for sprite in group["sprites"]:
            material_id = resolve_material_id(sprite)
            sid = sprite.get("id") or Path(sprite.get("source", "")).stem
            sprites.append(
                {
                    "id": sid,
                    "source": Path(sprite.get("source", "")).name,
                    "materialId": material_id,
                    "output": output_name(sprite_id, material_id),
                }
            )

        groups.append({"id": gid, "spriteId": sprite_id, "sprites": sprites})

    return {
        "version": 3,
        "sourceDir": data.get("sourceDir", "sprites"),
        "outputDir": data.get("outputDir", "sprites_named"),
        "defaultMaterial": "base",
        "nameSeparator": "_",
        "defaultLocale": "en",
        "materialAliases": MATERIAL_ALIASES,
        "typeSuggestions": list(MATERIAL_I18N.keys()),
        "i18n": {
            "sprites": SPRITE_I18N,
            "materials": MATERIAL_I18N,
        },
        "groups": groups,
    }


def main() -> None:
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    migrated = migrate(data)
    CONFIG.write_text(json.dumps(migrated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Migrated {CONFIG} to version {migrated['version']}")
    print(f"Sprites: {len(migrated['i18n']['sprites'])}, groups: {len(migrated['groups'])}")


if __name__ == "__main__":
    main()
