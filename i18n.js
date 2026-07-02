/**
 * Shared i18n for Fortnite Sprites Pocket Tracker.
 * Locale: auto from localStorage > browser > default "en"
 */
const SpritedexI18n = (() => {
  const STORAGE_KEY = "spritedex-locale";
  const SUPPORTED = ["en", "ru"];

  const UI = {
    en: {
      appTitle: "Fortnite Sprites Pocket Tracker",
      trackerTitle: "Fortnite Sprites Pocket Tracker",
      labelerTitle: "Sprite Labeler",
      collected: "Collected",
      of: "of",
      filterAll: "All",
      filterMissing: "Missing",
      filterCollected: "Collected",
      searchPlaceholder: "Search sprite or variant…",
      export: "Export",
      import: "Import",
      reset: "Reset",
      resetConfirm: "Reset all progress on this device?",
      importError: "Import failed",
      imported: "Imported",
      sprites: "sprites",
      loadError: "Failed to load sprites-config.json",
      loading: "Loading…",
      loadHint: "Run a local server from the project root:",
      noResults: "Nothing found",
      exportImportHint: "Export / import JSON to move progress between devices.",
      labelerHint: "Group = sprite name, field = variant. Empty variant → Base.",
      groupLabel: "Sprite",
      materialLabel: "Variant",
      groupField: "Group",
      addGroup: "+ Group",
      reloadConfig: "Reload config",
      copyJson: "Copy JSON",
      downloadJson: "Download JSON",
      resetDraft: "Reset draft",
      reloadConfirm: "Reload from sprites-config.json? Unsaved draft will be lost.",
      exportPanelTitle: "Export JSON",
      exportPanelHint: "Save as sprites-config.json, then run: python apply_labels.py",
      copyDone: "JSON copied",
      downloadDone: "Download started",
      ready: "Ready",
      reloadDone: "Loaded from config",
      newGroup: "New group",
      unnamedGroup: "(unnamed)",
      deleteGroup: "Delete",
      deleteGroupTitle: "Move sprites to the first group and delete this group",
      materialsCount: "variants",
      groupsNamed: "groups named",
      configFile: "sprites-config.json",
      collectedAria: "collected",
      share: "Share",
      shareCopied: "Link copied",
      sharedViewBanner: "Shared collection — view only",
      saveAndEdit: "Save to memory and edit",
      shareError: "Could not create share link",
      detailTitle: "Sprite details",
      detailAbility: "Ability",
      detailVariantBonus: "Variant bonus",
      detailHowToFind: "How to find",
      detailSummonCost: "Re-summon cost",
      detailDropRate: "Base drop rate (est.)",
      detailMarkCollected: "Mark collected",
      detailMarkMissing: "Remove from collection",
      detailClose: "Close",
      detailInfo: "Details",
      rarityRare: "Rare",
      rarityEpic: "Epic",
      rarityLegendary: "Legendary",
      rarityMythic: "Mythic",
      dust: "Sprite Dust",
      progressSprites: "Sprites (base)",
      progressVariants: "Variants",
      rarestMissing: "Rarest still missing",
      rarestMissingDone: "No missing variants — nice!",
      filterRarityAll: "Any rarity",
      summonLoadout: "Re-summon collected",
      progressMastered: "Mastered",
      filterMastered: "Mastered",
      filterNotMastered: "Not mastered",
      masteryMark: "Mark variant mastered (lvl 5)",
      masteryUnmark: "Remove mastery",
      masteryHint: "Each variant is mastered separately at level 5 + extraction. Mark the specific Gold, Gummy, etc. you completed.",
      masteryAria: "Toggle variant mastery",
      masteredAria: "mastered",
      detailMastery: "Mastery",
    },
    ru: {
      appTitle: "Fortnite Sprites Pocket Tracker",
      trackerTitle: "Карманный трекер спрайтов",
      labelerTitle: "Редактор спрайтов",
      collected: "Собрано",
      of: "из",
      filterAll: "Все",
      filterMissing: "Нет",
      filterCollected: "Есть",
      searchPlaceholder: "Поиск спрайта или варианта…",
      export: "Экспорт",
      import: "Импорт",
      reset: "Сброс",
      resetConfirm: "Сбросить весь прогресс на этом устройстве?",
      importError: "Ошибка импорта",
      imported: "Импортировано",
      sprites: "спрайтов",
      loadError: "Не удалось загрузить sprites-config.json",
      loading: "Загрузка…",
      loadHint: "Запустите сервер из корня проекта:",
      noResults: "Ничего не найдено",
      exportImportHint: "Экспорт / импорт JSON для переноса прогресса между устройствами.",
      labelerHint: "Группа = название спрайта, поле = вариант. Пустой вариант → Базовый.",
      groupLabel: "Спрайт",
      materialLabel: "Вариант",
      groupField: "Группа",
      addGroup: "+ Группа",
      reloadConfig: "Обновить из конфига",
      copyJson: "Копировать JSON",
      downloadJson: "Скачать JSON",
      resetDraft: "Сбросить черновик",
      reloadConfirm: "Перезагрузить из sprites-config.json? Черновик будет потерян.",
      exportPanelTitle: "Экспорт JSON",
      exportPanelHint: "Сохраните как sprites-config.json и выполните: python apply_labels.py",
      copyDone: "JSON скопирован",
      downloadDone: "Файл скачан",
      ready: "Готово",
      reloadDone: "Загружено из конфига",
      newGroup: "Новая группа",
      unnamedGroup: "(без названия)",
      deleteGroup: "Удалить",
      deleteGroupTitle: "Переместить спрайты в первую группу и удалить",
      materialsCount: "вариантов",
      groupsNamed: "групп с названием",
      configFile: "sprites-config.json",
      collectedAria: "собран",
      share: "Поделиться",
      shareCopied: "Ссылка скопирована",
      sharedViewBanner: "Чужая коллекция — только просмотр",
      saveAndEdit: "Сохранить в память и редактировать",
      shareError: "Не удалось создать ссылку",
      detailTitle: "О спрайте",
      detailAbility: "Способность",
      detailVariantBonus: "Бонус варианта",
      detailHowToFind: "Как найти",
      detailSummonCost: "Стоимость пересаммона",
      detailDropRate: "Шанс дропа base (оценка)",
      detailMarkCollected: "Отметить собранным",
      detailMarkMissing: "Убрать из коллекции",
      detailClose: "Закрыть",
      detailInfo: "Подробнее",
      rarityRare: "Редкий",
      rarityEpic: "Эпический",
      rarityLegendary: "Легендарный",
      rarityMythic: "Мифический",
      dust: "Sprite Dust",
      progressSprites: "Спрайты (base)",
      progressVariants: "Варианты",
      rarestMissing: "Самые редкие из недостающих",
      rarestMissingDone: "Ничего не осталось — отлично!",
      filterRarityAll: "Любая редкость",
      summonLoadout: "Пересаммон собранных",
      progressMastered: "Освоено",
      filterMastered: "Освоены",
      filterNotMastered: "Не освоены",
      masteryMark: "Отметить вариант освоенным (5 lvl)",
      masteryUnmark: "Снять освоение",
      masteryHint: "Каждый вариант осваивается отдельно на 5 lvl + экстракция. Отмечайте конкретный Gold, Gummy и т.д.",
      masteryAria: "Переключить освоение варианта",
      masteredAria: "освоен",
      detailMastery: "Освоение",
    },
  };

  let locale = "en";
  let config = null;

  function detectLocale() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && SUPPORTED.includes(saved)) return saved;
    const browser = (navigator.language || "en").toLowerCase();
    if (browser.startsWith("ru")) return "ru";
    return "en";
  }

  function t(key) {
    return UI[locale]?.[key] ?? UI.en[key] ?? key;
  }

  function setLocale(next) {
    if (!SUPPORTED.includes(next)) return;
    locale = next;
    localStorage.setItem(STORAGE_KEY, next);
    document.documentElement.lang = locale;
  }

  function getLocale() {
    return locale;
  }

  function init(cfg) {
    config = cfg;
    locale = detectLocale();
    document.documentElement.lang = locale;
  }

  function spriteName(spriteId) {
    return config?.i18n?.sprites?.[spriteId]?.[locale]
      ?? config?.i18n?.sprites?.[spriteId]?.en
      ?? spriteId;
  }

  function materialName(materialId) {
    return config?.i18n?.materials?.[materialId]?.[locale]
      ?? config?.i18n?.materials?.[materialId]?.en
      ?? materialId;
  }

  function materialSuggestions() {
    const ids = config?.typeSuggestions || Object.keys(config?.i18n?.materials || {});
    return ids.map((id) => materialName(id));
  }

  function materialIdFromInput(value) {
    const raw = (value || "").trim();
    if (!raw) return "base";
    const materials = config?.i18n?.materials || {};
    for (const [id, labels] of Object.entries(materials)) {
      if (labels.en?.toLowerCase() === raw.toLowerCase()) return id;
      if (labels.ru?.toLowerCase() === raw.toLowerCase()) return id;
    }
    return raw.toLowerCase().replace(/\s+/g, "-");
  }

  function materialInputValue(materialId) {
    if (!materialId || materialId === "base") return "";
    return materialName(materialId);
  }

  function localized(metaField) {
    if (!metaField) return "";
    return metaField[locale] ?? metaField.en ?? "";
  }

  function spriteMeta(spriteId) {
    return config?.meta?.sprites?.[spriteId] ?? null;
  }

  function materialMeta(materialId) {
    return config?.meta?.materials?.[materialId] ?? null;
  }

  function rarityLabel(rarity) {
    const labels = {
      rare: { en: "Rare", ru: "Редкий" },
      epic: { en: "Epic", ru: "Эпический" },
      legendary: { en: "Legendary", ru: "Легендарный" },
      mythic: { en: "Mythic", ru: "Мифический" },
    };
    return labels[rarity]?.[locale] ?? labels[rarity]?.en ?? rarity ?? "";
  }

  function summonCost(spriteId, materialId = "base") {
    const sm = spriteMeta(spriteId);
    if (!sm?.rarity) return null;
    const table = config?.meta?.raritySummonCost?.[sm.rarity];
    if (!table) return null;
    const isBase = !materialId || materialId === "base";
    return isBase ? table.base : table.variant;
  }

  function variantBonus(materialId) {
    const bonus = materialMeta(materialId)?.bonus;
    return localized(bonus);
  }

  function spriteAbility(spriteId) {
    return localized(spriteMeta(spriteId)?.ability);
  }

  function spriteSpawnHint(spriteId) {
    return localized(spriteMeta(spriteId)?.spawnHint);
  }

  function createLanguageSwitcher(container) {
    const wrap = document.createElement("div");
    wrap.className = "lang-switch";
    wrap.innerHTML = `
      <button type="button" data-lang="en" aria-label="English">EN</button>
      <button type="button" data-lang="ru" aria-label="Русский">RU</button>
    `;
    const sync = () => {
      wrap.querySelectorAll("button").forEach((btn) => {
        btn.classList.toggle("active", btn.dataset.lang === locale);
      });
    };
    wrap.addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-lang]");
      if (!btn) return;
      setLocale(btn.dataset.lang);
      sync();
      window.dispatchEvent(new CustomEvent("spritedex:localechange"));
    });
    sync();
    container.appendChild(wrap);
    return wrap;
  }

  return {
    t,
    init,
    setLocale,
    getLocale,
    spriteName,
    materialName,
    materialSuggestions,
    materialIdFromInput,
    materialInputValue,
    localized,
    spriteMeta,
    materialMeta,
    rarityLabel,
    summonCost,
    variantBonus,
    spriteAbility,
    spriteSpawnHint,
    createLanguageSwitcher,
    SUPPORTED,
  };
})();
