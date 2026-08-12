#!/usr/bin/env python3
"""Sync sprites-config + HD/PNG assets to the current Sprite Locker roster (117+)."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

BASE_URL = "https://spritelocker.com"
CONFIG_FILE = Path("sprites-config.json")
HD_DIR = Path("sprites_hd")
NAMED_DIR = Path("sprites_named")
MAP_FILE = Path("sprites-hd-map.json")
MANIFEST_OUT = NAMED_DIR / "catalog.json"

# Internal id → spritelocker.com filename prefix
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
    "peely": "peely",
    "llama": "llama",
    "batman": "fossilmeal",
    "vini-jr": "cokeparmesan",
    "pollo": "companystargazer",
    "john-wick": "fillergrunt",
    "ironmouse": "pedicureantacid",
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

HOLOFOIL_SLUG_OVERRIDE = {
    "ghost": "holo",
    "air": "holo",
}

MATERIAL_ORDER = ["base", "gold", "gummy", "galaxy", "holofoil", "gem", "cube", "quack"]

# Canonical roster matching spritelocker.com (Punk Gem kept — asset already shipped).
ROSTER: dict[str, list[str]] = {
    "water": ["base", "gold", "gummy", "galaxy", "gem", "holofoil", "quack"],
    "earth": ["base", "gold", "gummy", "galaxy", "gem", "cube", "quack"],
    "fire": ["base", "gold", "gummy", "galaxy", "holofoil", "cube", "quack"],
    "fishy": ["base", "gold", "gummy", "galaxy", "cube"],
    "air": ["base", "gold", "gummy", "galaxy", "holofoil"],
    "duck": ["base", "gold", "gummy", "galaxy", "gem"],
    "ghost": ["base", "gold", "gummy", "galaxy", "holofoil"],
    "demon": ["base", "gold", "gummy", "galaxy", "gem"],
    "king": ["base", "gold", "gummy", "galaxy", "holofoil"],
    "aura": ["base", "gold", "gummy", "galaxy", "gem"],
    "striker": ["base", "gold", "gummy", "galaxy", "holofoil"],
    "dream": ["base", "gold", "gummy", "galaxy", "cube"],
    "punk": ["base", "gold", "gummy", "galaxy", "gem", "cube"],
    "boss": ["base", "gold", "gummy", "galaxy", "cube"],
    "seven": ["base", "gold", "gummy", "galaxy", "holofoil"],
    "peely": ["base", "gold", "gummy", "galaxy", "holofoil"],
    "llama": ["base", "gold", "gummy", "galaxy", "gem"],
    "batman": ["base", "gold", "gummy", "galaxy", "holofoil", "cube"],
    "grim": ["base", "gold", "gummy", "galaxy", "gem", "holofoil", "cube"],
    "zero-point": ["base", "gold", "gummy", "galaxy", "gem", "holofoil", "cube", "quack"],
    "burnt-peanut": ["base"],
    "vini-jr": ["base"],
    "pollo": ["base"],
    "john-wick": ["base"],
    "ironmouse": ["base"],
}

SPRITE_ORDER = list(ROSTER.keys())

I18N_SPRITES = {
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
    "peely": {"en": "Peeky Peely", "ru": "Пики Пили"},
    "llama": {"en": "Lootin' Llama", "ru": "Лутин Лама"},
    "batman": {"en": "Batman", "ru": "Бэтмен"},
    "vini-jr": {"en": "Vini Jr.", "ru": "Вини Jr."},
    "pollo": {"en": "Pollo", "ru": "Полло"},
    "john-wick": {"en": "John Wick", "ru": "Джон Уик"},
    "ironmouse": {"en": "Ironmouse", "ru": "Айронмаус"},
}

META_SPRITES = {
    "water": {
        "rarity": "rare",
        "dropRate": 0.1392,
        "ability": {
            "en": "Replenishes shields for you and nearby squadmates while in water.",
            "ru": "Восстанавливает щиты вам и союзникам рядом, пока вы в воде.",
        },
        "spawnHint": {
            "en": "Spawns near water — lakes, rivers and the coastline.",
            "ru": "Появляется у воды — озёра, реки и побережье.",
        },
    },
    "earth": {
        "rarity": "rare",
        "dropRate": 0.1392,
        "ability": {
            "en": "Higher chance to find rare items when opening chests.",
            "ru": "Выше шанс найти редкий лут при открытии сундуков.",
        },
        "spawnHint": {
            "en": "Found around forests and wooded areas.",
            "ru": "В лесах и зеленой местности.",
        },
    },
    "fire": {
        "rarity": "rare",
        "dropRate": 0.1392,
        "ability": {
            "en": "Creates a fiery burst after dealing enough damage to an enemy.",
            "ru": "Огненный взрыв после достаточного урона по врагу.",
        },
        "spawnHint": {
            "en": "Found around city / built-up POIs.",
            "ru": "В городах и застроенных POI.",
        },
    },
    "air": {
        "rarity": "rare",
        "ability": {
            "en": "Sprint faster, jump higher while sprinting, and take zero fall damage.",
            "ru": "Быстрее спринт и выше прыжок на бегу; без урона от падения.",
        },
        "spawnHint": {
            "en": "Chests, Rare Chests and Sprite Chests across the map.",
            "ru": "Сундуки, Rare Chest и Sprite Chest по карте.",
        },
    },
    "fishy": {
        "rarity": "rare",
        "dropRate": 0.1379,
        "ability": {
            "en": "Swim faster and gain a brief speed boost when you take damage.",
            "ru": "Быстрее плаваете и получаете краткий буст скорости при уроне.",
        },
        "spawnHint": {
            "en": "Found in chests across the map.",
            "ru": "В сундуках по карте.",
        },
    },
    "duck": {
        "rarity": "epic",
        "dropRate": 0.0522,
        "ability": {
            "en": "Emoting or using Jam Tracks replenishes shields.",
            "ru": "Эмоции и Jam Tracks восстанавливают щиты.",
        },
        "spawnHint": {
            "en": "From Sprite Chests across the map.",
            "ru": "Из Sprite Chest по карте.",
        },
    },
    "ghost": {
        "rarity": "epic",
        "dropRate": 0.0522,
        "ability": {
            "en": "Grants a short cloak when you reload.",
            "ru": "Краткая невидимость при перезарядке.",
        },
        "spawnHint": {
            "en": "Only spawns at night on the island.",
            "ru": "Появляется только ночью на острове.",
        },
    },
    "king": {
        "rarity": "epic",
        "dropRate": 0.0522,
        "ability": {
            "en": "Your pickaxe deals more damage.",
            "ru": "Кирка наносит больше урона.",
        },
        "spawnHint": {
            "en": "From Sprite Chests across the map.",
            "ru": "Из Sprite Chest по карте.",
        },
    },
    "demon": {
        "rarity": "epic",
        "dropRate": 0.0522,
        "ability": {
            "en": "Siphons health and shields when you eliminate an opponent.",
            "ru": "Восстанавливает HP и щиты за элиминацию.",
        },
        "spawnHint": {
            "en": "From Sprite Chests across the map.",
            "ru": "Из Sprite Chest по карте.",
        },
    },
    "striker": {
        "rarity": "epic",
        "dropRate": 0.0574,
        "ability": {
            "en": "Gain Overdrive when you mantle, hurdle, or wall scramble.",
            "ru": "Overdrive при перелезании, перепрыгивании или скалолазании.",
        },
        "spawnHint": {
            "en": "Score a goal at the Soccer Pitch POI.",
            "ru": "Забейте гол на Soccer Pitch POI.",
        },
    },
    "aura": {
        "rarity": "epic",
        "dropRate": 0.0574,
        "ability": {
            "en": "Gain a Shock Rock charge when you deal enough damage to enemies.",
            "ru": "Заряд Shock Rock после достаточного урона по врагам.",
        },
        "spawnHint": {
            "en": "Found in chests and Supply Drops across the map.",
            "ru": "В сундуках и Supply Drop по карте.",
        },
    },
    "dream": {
        "rarity": "legendary",
        "dropRate": 0.02436,
        "ability": {
            "en": "Grants a random item each level; legendary loot at max level.",
            "ru": "Случайный предмет за уровень; на макс. уровне — легендарный лут.",
        },
        "spawnHint": {
            "en": "Chests only — a rarer spawn.",
            "ru": "Только сундуки — более редкий спавн.",
        },
    },
    "punk": {
        "rarity": "legendary",
        "dropRate": 0.02436,
        "ability": {
            "en": "Chance of infinite ammo — possibly nothing, or infinitely something.",
            "ru": "Шанс бесконечных патронов — или ничего, или бесконечно чего-то.",
        },
        "spawnHint": {
            "en": "Chests only — a rarer spawn. Gem variant marked Soon on Sprite Locker.",
            "ru": "Только сундуки — более редкий спавн. Gem на Sprite Locker пока Soon.",
        },
    },
    "boss": {
        "rarity": "legendary",
        "dropRate": 0.0263,
        "ability": {
            "en": "Boosts your maximum health and shields.",
            "ru": "Увеличивает максимум HP и щитов.",
        },
        "spawnHint": {
            "en": "Always drops when you defeat any boss.",
            "ru": "Выпадает с любого побеждённого босса.",
        },
    },
    "seven": {
        "rarity": "legendary",
        "ability": {
            "en": "Enemy player foot trails are visible to your squad.",
            "ru": "Следы врагов видны всему скваду.",
        },
        "spawnHint": {
            "en": "Sprite Chests in unranked BR / Zero Build. A Sprite Locator helps.",
            "ru": "Sprite Chest в unranked BR / Zero Build. Sprite Locator повышает шанс.",
        },
    },
    "peely": {
        "rarity": "legendary",
        "ability": {
            "en": "Marks rare sprite variants and carriers nearby — but also reveals you.",
            "ru": "Помечает редкие варианты спрайтов и носителей рядом — и вас тоже.",
        },
        "spawnHint": {
            "en": "High ground — mountainous parts of the map.",
            "ru": "Высоты — гористые зоны карты.",
        },
    },
    "llama": {
        "rarity": "legendary",
        "ability": {
            "en": "Chance of a weapon upgrade when you open an ammo box (scales with level).",
            "ru": "Шанс апгрейда оружия при открытии ящика патронов (растёт с уровнем).",
        },
        "spawnHint": {
            "en": "Relic Chests, plus Sprite/Rare Chests around Golden Grove and Calamari Canyon.",
            "ru": "Relic Chest, а также Sprite/Rare Chest у Golden Grove и Calamari Canyon.",
        },
    },
    "batman": {
        "rarity": "mythic",
        "ability": {
            "en": "Leap and deploy the Bat Cape to glide; find rare Sprites in chests more often.",
            "ru": "Прыжок и Bat Cape для планирования; чаще редкие спрайты в сундуках.",
        },
        "spawnHint": {
            "en": "Beat DC beach NPCs / complete DC quests, or open Sprite Chests.",
            "ru": "Победите DC NPC на пляже / квесты DC, либо Sprite Chest.",
        },
    },
    "zero-point": {
        "rarity": "mythic",
        "dropRate": 0.01044,
        "ability": {
            "en": "Spawns a Shield Bubble Jr. when you use a healing item on yourself.",
            "ru": "Shield Bubble Jr. при использовании лечения на себе.",
        },
        "spawnHint": {
            "en": "Vault / keycard Sprite Chests — among the rarest collectibles.",
            "ru": "Vault / keycard Sprite Chest — одни из самых редких.",
        },
    },
    "grim": {
        "rarity": "mythic",
        "dropRate": 9.8e-07,
        "ability": {
            "en": "Attackers who damage you are marked for your squad.",
            "ru": "Атакующие вас враги помечаются для сквада.",
        },
        "spawnHint": {
            "en": "Found in chests across the map — extremely rare.",
            "ru": "В сундуках по карте — крайне редкий.",
        },
    },
    "burnt-peanut": {
        "rarity": "mythic",
        "dropRate": 0.015,
        "ability": {
            "en": "Chance for bonus loot from eliminations, including Mythic items when maxed.",
            "ru": "Шанс бонусного лута за элиминации, включая мифик на макс. уровне.",
        },
        "spawnHint": {
            "en": "Drops from Relic Chests (~1.5%). Normal form only — no variants.",
            "ru": "Из Relic Chest (~1.5%). Только обычная форма — без вариантов.",
        },
    },
    "vini-jr": {
        "rarity": "mythic",
        "ability": {
            "en": "Sprint to unlock a slidekick that damages enemies and boosts fire rate / reload.",
            "ru": "Спринт открывает слайд-удар: урон и буст скорострельности / перезарядки.",
        },
        "spawnHint": {
            "en": "Sprite Chests and Rare Chests — Sprite Chests have the best odds. Normal only.",
            "ru": "Sprite Chest и Rare Chest — лучше шанс в Sprite Chest. Только обычный.",
        },
    },
    "pollo": {
        "rarity": "mythic",
        "ability": {
            "en": "After an elimination, you and your squad regenerate shields briefly.",
            "ru": "После элиминации вы и сквад кратко регенерируете щиты.",
        },
        "spawnHint": {
            "en": "Sprite Chests and Rare Chests — Sprite Chests have the best odds. Normal only.",
            "ru": "Sprite Chest и Rare Chest — лучше шанс в Sprite Chest. Только обычный.",
        },
    },
    "john-wick": {
        "rarity": "mythic",
        "ability": {
            "en": "Reveals nearby enemies after you knock or eliminate a player.",
            "ru": "Показывает врагов рядом после нокдауна или элиминации.",
        },
        "spawnHint": {
            "en": "The Simpsons Reload map (Springfield) — Relic/Sprite Chests, Portable Extractor, or a win. Normal only.",
            "ru": "Карта The Simpsons Reload (Springfield) — Relic/Sprite Chest, Portable Extractor или победа. Только обычный.",
        },
    },
    "ironmouse": {
        "rarity": "mythic",
        "ability": {
            "en": "Regenerates health when low and cloaks you with low gravity while healing.",
            "ru": "Реген HP при низком здоровье + невидимость и низкая гравитация на время лечения.",
        },
        "spawnHint": {
            "en": "Relic Chests. A Sprite Locator improves Mythic odds. Normal only.",
            "ru": "Relic Chest. Sprite Locator повышает шанс мифика. Только обычный.",
        },
    },
}

META_MATERIALS = {
    "base": {"bonus": {"en": "", "ru": ""}},
    "gold": {
        "bonus": {
            "en": "Bonus XP from eliminations",
            "ru": "Бонусный XP за элиминации",
        }
    },
    "gummy": {
        "bonus": {
            "en": "+10% Sprite Dust when extracting",
            "ru": "+10% Sprite Dust при экстракции",
        }
    },
    "galaxy": {
        "bonus": {
            "en": "+20% ammo when looting",
            "ru": "+20% патронов при луте",
        }
    },
    "holofoil": {
        "bonus": {
            "en": "Better squad odds to find rare sprites",
            "ru": "Выше шанс сквада найти редкие спрайты",
        }
    },
    "gem": {
        "bonus": {
            "en": "−30% fall damage",
            "ru": "−30% урона от падения",
        }
    },
    "cube": {
        "bonus": {
            "en": "Overdrive while caught in the Storm",
            "ru": "Overdrive, пока вы в шторме",
        }
    },
    "quack": {
        "bonus": {
            "en": "Shares half its progress with other sprites in your match inventory (Mastery unlock)",
            "ru": "Делится половиной прогресса с другими спрайтами в инвентаре (разблокировка Mastery)",
        }
    },
}


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
    return f"/sprites/{slug}_{variant}.webp"


def sanitize(part: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00]', "_", part.strip()) or "unnamed"


def output_filename(sprite_id: str, material_id: str) -> str:
    sprite = sanitize(
        I18N_SPRITES[sprite_id]["en"]
        .replace(" ", "")
        .replace("'", "")
        .replace(".", "")
    )
    material_labels = {
        "base": "Base",
        "gold": "Gold",
        "gummy": "Gummy",
        "galaxy": "Galaxy",
        "holofoil": "Holofoil",
        "gem": "Gem",
        "cube": "Cube",
        "quack": "Quack",
    }
    material = material_labels[material_id]
    return f"{sprite}_{material}.png"


def scrape_paths() -> set[str]:
    req = urllib.request.Request(f"{BASE_URL}/", headers={"User-Agent": "sprites-tracker/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    return set(re.findall(r"/sprites/[a-z0-9_]+\.webp", html))


def download(path: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(f"{BASE_URL}{path}", headers={"User-Agent": "sprites-tracker/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            dest.write_bytes(resp.read())
        return True
    except urllib.error.HTTPError as exc:
        print(f"  HTTP {exc.code} {path}")
        return False


def webp_to_png(webp: Path, png: Path) -> bool:
    try:
        with Image.open(webp) as img:
            img.save(png, format="PNG")
        return png.exists()
    except Exception as exc:  # noqa: BLE001
        print(f"  convert fail {webp.name}: {exc}")
        return False


def existing_entry_map(config: dict) -> dict[tuple[str, str], dict]:
    found: dict[tuple[str, str], dict] = {}
    for group in config.get("groups", []):
        sprite_id = group["spriteId"]
        for sprite in group.get("sprites", []):
            material_id = sprite.get("materialId", "base")
            found[(sprite_id, material_id)] = sprite
    return found


def sync_config(config: dict) -> list[tuple[str, str]]:
    """Rewrite groups/catalog/i18n/meta to match ROSTER. Returns newly added keys."""
    existing = existing_entry_map(config)
    added: list[tuple[str, str]] = []

    config["i18n"]["sprites"] = I18N_SPRITES
    config["meta"]["sprites"] = META_SPRITES
    config["meta"]["materials"] = META_MATERIALS
    config["meta"]["spriteOrder"] = SPRITE_ORDER

    groups: list[dict] = []
    for idx, sprite_id in enumerate(SPRITE_ORDER, start=1):
        materials = ROSTER[sprite_id]
        sprites: list[dict] = []
        for material_id in sorted(materials, key=lambda m: MATERIAL_ORDER.index(m)):
            prev = existing.get((sprite_id, material_id))
            entry_id = prev["id"] if prev else f"{sprite_id}-{material_id}"
            filename = output_filename(sprite_id, material_id)
            item: dict = {
                "id": entry_id,
                "materialId": material_id,
                "output": filename,
            }
            if prev and prev.get("source"):
                item["source"] = prev["source"]
            sprites.append(item)
            if not prev:
                added.append((sprite_id, material_id))
        groups.append(
            {
                "id": f"group-{idx:02d}-{sprite_id}",
                "spriteId": sprite_id,
                "sprites": sprites,
            }
        )

    config["groups"] = groups
    catalog = rebuild_catalog(config)
    config["catalog"] = catalog
    config["total"] = len(catalog)
    config["updatedAt"] = datetime.now(timezone.utc).isoformat()
    config["version"] = max(int(config.get("version") or 5), 6)
    return added


def rebuild_catalog(config: dict) -> list[dict]:
    catalog: list[dict] = []
    for group in config["groups"]:
        sprite_id = group["spriteId"]
        for sprite in group["sprites"]:
            material_id = sprite["materialId"]
            source = sprite.get("source")
            catalog.append(
                {
                    "id": sprite["id"],
                    "spriteId": sprite_id,
                    "sprite": I18N_SPRITES[sprite_id]["en"],
                    "materialId": material_id,
                    "material": material_id.title() if material_id != "base" else "Base",
                    "source": f"sprites/{source}" if source else None,
                    "output": f"sprites_named/{sprite['output']}",
                    "filename": sprite["output"],
                    "group_id": group["id"],
                }
            )
    # Fix material display names to match i18n EN labels
    mat_en = {
        "base": "Base",
        "gold": "Gold",
        "gummy": "Gummy",
        "galaxy": "Galaxy",
        "holofoil": "Holofoil",
        "gem": "Gem",
        "cube": "Cube",
        "quack": "Quack",
    }
    for item in catalog:
        item["material"] = mat_en[item["materialId"]]
    return catalog


def fetch_all(config: dict, available: set[str]) -> dict:
    by_id: dict[str, str] = {}
    by_key: dict[str, str] = {}
    ok = 0
    miss = 0

    HD_DIR.mkdir(exist_ok=True)
    NAMED_DIR.mkdir(exist_ok=True)

    for item in config["catalog"]:
        sprite_id = item["spriteId"]
        material_id = item["materialId"]
        remote = spritelocker_path(sprite_id, material_id)
        png_path = NAMED_DIR / item["filename"]
        if not remote:
            miss += 1
            print(f"  NO MAP {sprite_id}/{material_id}")
            continue
        if remote not in available:
            # still try download — scrape may miss some
            pass
        webp_name = remote.rsplit("/", 1)[-1]
        webp_path = HD_DIR / webp_name
        if download(remote, webp_path) and webp_to_png(webp_path, png_path):
            rel = str(webp_path).replace("\\", "/")
            by_id[item["id"]] = rel
            by_key[f"{sprite_id}:{material_id}"] = rel
            ok += 1
            print(f"  OK  {sprite_id}/{material_id} <- {webp_name}")
        else:
            miss += 1
            # keep existing named PNG if present
            if png_path.exists():
                print(f"  KEEP local PNG {item['filename']} (no HD)")
            else:
                print(f"  MISS {sprite_id}/{material_id}")

    return {
        "version": 1,
        "source": BASE_URL,
        "scraped": sorted(available),
        "downloaded": len(by_id),
        "fallbackDir": "sprites_named",
        "byId": by_id,
        "byKey": by_key,
        "ok": ok,
        "miss": miss,
    }


def write_named_manifest(config: dict) -> None:
    MANIFEST_OUT.write_text(
        json.dumps(
            {
                "version": config.get("version", 6),
                "total": config["total"],
                "sprites": config["catalog"],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    print("Scraping Sprite Locker…")
    available = scrape_paths()
    print(f"  {len(available)} remote paths")

    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    print("Syncing config…")
    added = sync_config(config)
    for sprite_id, material_id in added:
        print(f"  + {sprite_id}/{material_id}")

    print(f"Fetching {config['total']} assets…")
    hd_map = fetch_all(config, available)
    ok, miss = hd_map.pop("ok"), hd_map.pop("miss")

    CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    MAP_FILE.write_text(json.dumps(hd_map, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_named_manifest(config)

    print(f"\nCatalog: {config['total']} (added {len(added)})")
    print(f"HD OK: {ok}, miss: {miss}")
    print(f"Wrote {CONFIG_FILE}, {MAP_FILE}, {MANIFEST_OUT}")


if __name__ == "__main__":
    main()
