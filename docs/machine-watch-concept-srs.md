# Machine Watch — Concept / Plan / SRS

> Черновик идеи для отдельного проекта (не часть Fortnite Spritedex).
> Цель документа: зафиксировать замысел, протокол и границы MVP, чтобы добить реализацию с основной машины позже.

**Статус:** concept  
**Версия:** 0.1  
**Дата:** 2026-08-12

---

## 1. Проблема

Cursor Cloud Agent привязан к конкретному репозиторию и окружению. Изнутри одного agent-run нельзя надёжно:

- «подключить» другой GitHub-репозиторий к remote Cursor;
- стартовать независимый Cloud Agent на другом repo как sibling-процесс с полной привязкой workspace.

При этом на **основной машине** можно держать лёгкий локальный оркестратор, который:

1. видит новые/существующие checkout’ы на диске;
2. понимает, «знает» ли эта машина данный проект;
3. при необходимости регистрирует машину и/или запускает Cursor Agent (SDK) для setup / auto-claim.

## 2. Цель продукта

Локальный watcher/daemon на основной (и опционально на других) машине(ах), который:

- мониторит набор корневых папок (например `~/Projects`);
- по признаку (файл-маркер / claim-файл) определяет, нужно ли действие;
- если идентификатор текущей машины ещё не зафиксирован для этого checkout — выполняет **claim** и опционально стартует агента для дальнейшей настройки.

Итог: предсказуемый механизм «машина ↔ репозиторий» для будущей автоматизации (идентификация хоста, onboarding environment, триггер cloud/local agent).

## 3. Non-goals (v1)

- Не замена Cursor Desktop / Agents UI.
- Не мульти-tenant SaaS и не общий облачный реестр машин.
- Не обязанность коммитить claim в git (может оставаться local-only).
- Не автозапуск произвольных агентов по любому изменению файлов.
- Не решение ACL/секретов между машинами сверх простого machine id.

## 4. Акторы

| Актор | Роль |
|--------|------|
| Пользователь | Ставит watcher, задаёт watch-roots, API key, политики |
| Watcher (daemon/script) | Сканирует FS, читает маркеры, пишет claim, дергает SDK |
| Cursor Agent (SDK) | Опциональный исполнитель setup-задач |
| Checkout / repo folder | Объект наблюдения |

## 5. Ключевые понятия

### 5.1 Machine ID

Стабильный идентификатор хоста, хранится локально, например:

- путь: `%USERPROFILE%\.cursor\machine-id` (Windows) / `~/.cursor/machine-id` (Unix);
- значение: короткий slug + hash от platform machine GUID / hostname (не PII сверх необходимого);
- генерируется один раз при первом запуске watcher’а.

### 5.2 Claim file

Файл в checkout, фиксирующий «какие машины уже видели/заявили этот проект».

Рекомендуемый путь: `.cursor/host-claim.json`

### 5.3 Pending marker

Опциональный явный триггер «обработай меня», если не хотим срабатывать на каждый незаклеймленный repo.

Рекомендуемый путь: `.cursor/pending-host.json`

### 5.4 Lock

Короткоживущий lock против параллельных запусков: `.cursor/host-claim.lock`

---

## 6. Протокол файлов

### 6.1 `host-claim.json`

```json
{
  "schema": 1,
  "repo": "github.com/owner/name",
  "updatedAt": "2026-08-12T15:40:00Z",
  "machines": {
    "pc-main-a1b2": {
      "hostname": "ALEX-PC",
      "os": "win32",
      "claimedAt": "2026-08-12T15:40:00Z",
      "role": "primary",
      "agentId": null,
      "notes": "claimed by machine-watch without agent"
    }
  }
}
```

Правила:

- `machines[<machineId>]` существует ⇒ для этой машины claim уже сделан → **skip**;
- отсутствует ⇒ нужен claim (+ optional setup);
- файл может быть gitignored (рекомендация v1: **local-only**, не коммитить), либо shared — отдельное продуктовое решение.

### 6.2 `pending-host.json`

```json
{
  "schema": 1,
  "action": "claim",
  "setup": false,
  "prefer": "local",
  "createdAt": "2026-08-12T15:39:00Z"
}
```

| Поле | Смысл |
|------|--------|
| `action` | `claim` \| `claim-and-setup` |
| `setup` | если `true` — после claim стартовать агента |
| `prefer` | `local` \| `cloud` — runtime для агента |
| `repoUrl` | опционально, для cloud start без угадывания remote |

После успеха: удалить или переименовать в `pending-host.done.json` (+ timestamp).

### 6.3 Inbox-событие (будущее)

Отдельная папка вне репо, например `~/CursorWatch/inbox/*.json`:

```json
{
  "action": "cloud-agent",
  "repoUrl": "https://github.com/owner/other-repo",
  "prompt": "Bootstrap environment and report machine-claim strategy"
}
```

Позволяет стартовать cloud agent **по URL**, не требуя предварительного clone рядом с текущим workspace.

---

## 7. Архитектура

```text
┌──────────────────────────────────────────────┐
│ Main machine                                 │
│                                              │
│  machine-watch (daemon)                      │
│    ├─ resolve machine-id                     │
│    ├─ watch roots (poll or FS events)        │
│    ├─ detect checkout (.git / marker)        │
│    ├─ read pending / claim                   │
│    ├─ write claim (deterministic)            │
│    └─ optional: Cursor SDK Agent.create()    │
│         ├─ local:  { cwd: <checkout> }       │
│         └─ cloud:  { repos: [{ url }] }      │
└──────────────────────────────────────────────┘
```

### 7.1 Компоненты

1. **Config** — watch roots, debounce, enableAgent, model, API key env.
2. **Identity** — load/create machine-id.
3. **Scanner** — poll interval или `FileSystemWatcher`.
4. **Policy** — когда срабатывать: только `pending-host` vs любой unclaimed checkout.
5. **ClaimWriter** — атомарная запись JSON + lock.
6. **AgentLauncher** — тонкая обёртка над `@cursor/sdk` / `cursor-sdk`.
7. **Log/State** — journal последних действий (`~/.cursor/machine-watch/log.jsonl`).

### 7.2 Рекомендуемый стек реализации (отдельный проект)

- **Windows-first:** PowerShell watcher + Node/TS worker для SDK, **или** чистый Node/TS daemon.
- Auth: `CURSOR_API_KEY` в env / Windows Credential Manager (не в git).
- Без зависимости от конкретного product-repo (этот SRS можно унести as-is).

---

## 8. Потоки (use cases)

### UC1 — Claim only (MVP)

1. Пользователь кладёт/клонирует repo в watch-root.
2. Создаёт `.cursor/pending-host.json` с `action: "claim"`.
3. Watcher видит маркер.
4. Если `machineId` уже в claim → done-файл, выход.
5. Иначе: lock → дописать machine в `host-claim.json` → unlock → mark pending done.
6. Агент **не** запускается.

### UC2 — Claim + local setup agent

1. Как UC1, но `setup: true`, `prefer: "local"`.
2. После claim: `Agent.create({ local: { cwd } })` + фиксированный prompt
   («проверь `.cursor/environment.json` / AGENTS.md, предложи минимальный setup; не трогай секреты»).
3. В claim записывается `agentId` run’а (если доступен).

### UC3 — Cloud agent by URL (post-MVP)

1. Inbox JSON с `repoUrl`.
2. Watcher вызывает `Agent.create({ cloud: { repos: [{ url, startingRef }] } })`.
3. Не требует локального clone (clone делает cloud runtime).
4. Результат/ссылка на run пишется в journal.

### UC4 — Идемпотентность

Повторный проход по уже заклеймленному checkout с тем же machineId — no-op.

---

## 9. Правила срабатывания (policy)

Предлагаемые режимы конфига:

| Mode | Поведение |
|------|-----------|
| `pending-only` (default MVP) | Только при наличии `pending-host.json` / inbox |
| `unclaimed-checkouts` | Любой `.git` без своего machineId в claim |
| `inbox-only` | Только внешний inbox, репо не сканируются |

Для безопасности по умолчанию: **`pending-only`**.

Дополнительно:

- debounce N секунд после появления маркера;
- global concurrency limit (например 1 agent одновременно);
- allowlist/denylist путей;
- dry-run флаг.

---

## 10. Требования (SRS)

### 10.1 Functional

| ID | Требование | Priority |
|----|------------|----------|
| F1 | Хранить/создавать стабильный machine-id на хосте | Must |
| F2 | Читать конфиг watch-roots и mode | Must |
| F3 | Обнаруживать `pending-host.json` | Must |
| F4 | Писать/обновлять `host-claim.json` атомарно с lock | Must |
| F5 | Идемпотентный skip, если machine уже в claim | Must |
| F6 | Журналировать действия | Must |
| F7 | Опционально стартовать local agent через Cursor SDK | Should |
| F8 | Опционально стартовать cloud agent по `repoUrl` | Could |
| F9 | Dry-run без записи/запуска | Should |
| F10 | Mark pending as done / failed с причиной | Must |

### 10.2 Non-functional

| ID | Требование | Priority |
|----|------------|----------|
| N1 | Работа на Windows 10+ (основной сценарий) | Must |
| N2 | Не требовать Node в target product-repos; Node только у watcher-проекта | Should |
| N3 | Секреты только из env/credential store | Must |
| N4 | CPU/IO: poll ≤ 1×/5s или event-based; без busy-loop | Must |
| N5 | Ошибки SDK не должны ронять daemon; retry с backoff | Must |
| N6 | Документация установки ≤ 1 страница README | Should |

### 10.3 Security / privacy

- Не логировать API key.
- Machine-id не должен содержать email/username обязательно; hostname — опционально и локально.
- По умолчанию claim **не коммитить** (добавить в `.gitignore` шаблон проекта watcher’а / инструкцию).
- Agent prompt — allowlisted template, без исполнения произвольного текста из pending без явного opt-in (`allowCustomPrompt: false` by default).

---

## 11. MVP scope

Сделать минимально:

1. CLI/daemon: `machine-watch once` и `machine-watch serve`.
2. Identity + pending-only policy + claim writer.
3. Journal в `~/.cursor/machine-watch/`.
4. README с примером `pending-host.json`.
5. Заглушка `AgentLauncher` (dry interface); реальный SDK — phase 2.

Не делать в MVP:

- cloud inbox;
- GUI;
- sync claim через git;
- multi-machine coordination service.

---

## 12. Phase plan

### Phase 0 — Spec (этот документ)
Зафиксировать протокол файлов и policy.

### Phase 1 — Claim daemon
Watcher + machine-id + pending + claim + journal.

### Phase 2 — Local agent hook
Интеграция `@cursor/sdk` / `cursor-sdk`, template prompt, запись `agentId`.

### Phase 3 — Cloud inbox
Старт cloud agent по URL; ссылка на run в journal / optional notify.

### Phase 4 — Hardening
Service install (Task Scheduler / launchd), metrics, richer policies.

---

## 13. Пример конфига watcher’а

`~/.cursor/machine-watch/config.json`

```json
{
  "schema": 1,
  "machineIdPath": "~/.cursor/machine-id",
  "watchRoots": ["~/Projects"],
  "mode": "pending-only",
  "pollSeconds": 5,
  "debounceSeconds": 2,
  "maxConcurrentAgents": 1,
  "enableAgent": false,
  "defaultPrefer": "local",
  "model": "composer-2.5",
  "dryRun": false
}
```

Env:

- `CURSOR_API_KEY` — обязателен только если `enableAgent: true`.

---

## 14. Пример prompt template (phase 2)

```text
You are running as a setup agent triggered by machine-watch.
Machine ID: {{machineId}}
Hostname: {{hostname}}
Checkout: {{cwd}}

Tasks:
1) Confirm .cursor/host-claim.json already contains this machineId (do not duplicate).
2) If .cursor/environment.json or AGENTS.md exists, summarize how to run the project locally.
3) Do not modify application source unless pending-host.setupRequestsCodeChanges is true.
4) Reply with a short setup checklist.
```

---

## 15. Риски и решения

| Риск | Митигация |
|------|-----------|
| Спам агентами на каждый clone | `pending-only` + locks + concurrency limit |
| Claim в git → merge conflicts | Default local-only / gitignore |
| SDK ключ отсутствует | Claim работает без агента; agent step skip + log |
| Путаница local vs cloud | Явное поле `prefer`; cloud только при `repoUrl` |
| Watcher упал | `once` режим из Task Scheduler + serve отдельно |

---

## 16. Критерии готовности идеи (definition of ready для отдельного repo)

- [ ] Создан отдельный репозиторий `machine-watch` (имя TBD)
- [ ] Перенесён этот SRS
- [ ] Реализован Phase 1 (claim-only)
- [ ] Ручной тест: pending → claim → second pass no-op
- [ ] Решение: gitignore claim или shared (зафиксировать в README)

---

## 17. Открытые вопросы

1. Claim **local-only** или иногда коммитить для shared inventory машин команды?
2. Один watcher на все Projects или per-repo opt-in только через pending?
3. Нужен ли сразу Windows Service, или достаточно ручного/`pwsh` в background?
4. Python SDK vs TypeScript SDK — что удобнее на основной машине?
5. Связка с Cursor Environment snapshots: должен ли setup-agent ещё и триггерить snapshot, или это руками?

---

## 18. Резюме одной фразой

**Machine Watch** — локальный сторож на основной машине: видит маркер в checkout, если этот host ещё не в claim — регистрирует machine-id (детерминированно) и опционально стартует Cursor Agent (SDK) для setup/cloud bootstrap; сам Cloud Agent «из агента» другой repo не подключает.
