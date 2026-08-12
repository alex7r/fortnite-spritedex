# Fortnite Spritedex — agent notes

Static pocket tracker for Fortnite pet sprites (Chapter 7 Season 3). No build step, no package manager.

## Run locally

```bash
python3 -m http.server 8765
# open http://localhost:8765/tracker.html
```

Or `./serve.sh`.

## Key files

| Path | Role |
|------|------|
| `tracker.html` | Main tracker UI |
| `labeler.html` | Labeling tool (dev) |
| `sprites-config.json` | Pets / variants config |
| `i18n.js` | EN/RU strings |
| `sprites_named/` | Fallback PNG sprites |
| `sprites_hd/` | HD WebP from Sprite Locker |
| `fetch_spritelocker.py` | Refresh HD assets |
| `sync_roster.py` | Sync full roster + media from Sprite Locker |

## Cursor Cloud specific instructions

- Stack is static HTML/JS + optional Python 3 scripts. Do not add Node unless asked.
- After UI changes, verify with a local `python3 -m http.server 8765` and open `/tracker.html`.
- Prefer editing existing files over new frameworks.
- Live site: https://alex7r.github.io/fortnite-spritedex/tracker.html
