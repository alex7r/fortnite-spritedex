# Fortnite Sprites Pocket Tracker

Карманный pet-проект: простой трекер коллекции спрайтов Fortnite (Chapter 7 Season 3). Сделан для себя и друзей — без бэкенда, всё работает в браузере.

**Демо:** https://alex7r.github.io/fortnite-spritedex/tracker.html

---

## Зачем это

Может пригодиться, если нужен лёгкий офлайн-трекер с минимумом зависимостей: отметил спрайты — прогресс сохранился в `localStorage`, можно поделиться ссылкой на текущий набор.

За время разработки появился более качественный и причёсанный вариант — **[Sprite Locker](https://spritelocker.com/)**. Там удобная таблица по вариантам, экспорт для Discord, картинки получше и больше фич. Если нужен полноценный чеклист — смотрите туда.

Этот репозиторий остаётся как простая альтернатива: открыть, потыкать, не регистрироваться.

---

## Возможности

- 84 спрайта, официальные названия (Water, Duck, Zero Point и т.д.)
- Варианты: Base, Gold, Gummy, Galaxy, Gem, Holofoil
- EN / RU — язык по настройкам браузера, можно переключить вручную
- Прогресс в `localStorage` на устройстве
- **Share** — короткая ссылка `?s=...` с текущей коллекцией (режим просмотра; чтобы редактировать — «Сохранить в память и редактировать»)
- Мобильная вёрстка

---

## HD-спрайты (Sprite Locker)

Часть картинок взята с [spritelocker.com](https://spritelocker.com/) — там они заметно чётче. Скрипт скачивает доступные варианты (Base/Gold/Gummy/Galaxy); Gem, Holofoil, Air, Seven и прочие отсутствующие — из локального `sprites_named/`.

```bash
python3 fetch_spritelocker.py
```

---

## Локальный запуск

Нужен HTTP-сервер (из-за `fetch` конфига):

```bash
./serve.sh
# → http://localhost:8765/tracker.html
```

Или:

```bash
python3 -m http.server 8765
```

---

## Структура

| Файл | Назначение |
|------|------------|
| `tracker.html` | Трекер коллекции |
| `labeler.html` | Редактор меток (для своего конфига) |
| `sprites-config.json` | Список спрайтов и вариантов |
| `sprites_named/` | PNG с английскими именами (fallback) |
| `sprites_hd/` | HD WebP с [Sprite Locker](https://spritelocker.com/) |
| `sprites-hd-map.json` | Маппинг catalog id → HD файл |
| `fetch_spritelocker.py` | Скачать HD-спрайты с spritelocker.com |
| `i18n.js` | Переводы EN/RU |
| `apply_labels.py` | Пересборка `sprites_named/` из конфига |

---

## Дисклеймер

Неофициальный фан-проект. Fortnite и связанные названия — торговые марки Epic Games, Inc. Проект не связан с Epic Games.
