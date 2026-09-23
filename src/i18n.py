"""Минимальная система интернационализации (EN/RU) для Simple Screenshot.

Язык хранится в конфиге (cfg["language"] — "en" или "ru") и кэшируется в
памяти процесса функцией get_language(), чтобы не перечитывать файл
конфига на каждый вызов tr(). set_language() сразу сохраняет выбор на
диск независимо от остальных, возможно ещё не применённых, настроек в
открытом диалоге настроек — переключение языка интерфейса не должно
требовать нажатия "Сохранить".
"""
import config as cfgmod

LANGUAGES = ("en", "ru")
DEFAULT_LANGUAGE = "en"

_current = None


def get_language():
    global _current
    if _current is None:
        cfg = cfgmod.load_config()
        lang = cfg.get("language", DEFAULT_LANGUAGE)
        _current = lang if lang in LANGUAGES else DEFAULT_LANGUAGE
    return _current


def set_language(lang):
    global _current
    if lang not in LANGUAGES or lang == _current:
        return
    _current = lang
    cfg = cfgmod.load_config()
    cfg["language"] = lang
    cfgmod.save_config(cfg)


STRINGS = {
    "app_name": {"en": "Simple Screenshot", "ru": "Simple Screenshot"},

    # -- трей / меню -----------------------------------------------------
    "tray.capture_now": {"en": "Take screenshot now", "ru": "Сделать снимок сейчас"},
    "tray.capture_clipboard": {"en": "Copy screenshot to clipboard", "ru": "Скопировать снимок в буфер обмена"},
    "tray.capture_region": {"en": "Select screen region…", "ru": "Выделить область экрана…"},
    "tray.settings": {"en": "Settings…", "ru": "Настройки…"},
    "tray.quit": {"en": "Quit", "ru": "Выход"},

    "notify.saved": {"en": "Screenshot saved:\n{path}", "ru": "Скриншот сохранён:\n{path}"},
    "notify.error": {"en": "Error: {error}", "ru": "Ошибка: {error}"},
    "notify.clipboard_saved": {"en": "Screenshot copied to clipboard", "ru": "Скриншот скопирован в буфер обмена"},
    "notify.region_clipboard_saved": {"en": "Selected region copied to clipboard", "ru": "Выделенная область скопирована в буфер обмена"},
    "notify.region_saved": {"en": "Selected region saved:\n{path}", "ru": "Выделенная область сохранена:\n{path}"},

    # -- ошибка запуска (main.py) -----------------------------------------
    "main.tray_unavailable": {
        "en": "System tray is not available in this desktop environment.",
        "ru": "Системный трей недоступен в этом окружении рабочего стола.",
    },

    # -- диалог настроек ---------------------------------------------------
    "settings.title": {"en": "Settings — Simple Screenshot", "ru": "Настройки — Simple Screenshot"},
    "settings.save_location": {"en": "Screenshot save location", "ru": "Место сохранения скриншотов"},
    "settings.browse": {"en": "Browse", "ru": "Обзор"},
    "settings.hotkeys": {"en": "Hotkeys", "ru": "Горячие клавиши"},
    "settings.hotkey.save": {"en": "Save screenshot to file:", "ru": "Сохранить снимок в файл:"},
    "settings.hotkey.clipboard": {"en": "Copy to clipboard:", "ru": "Скопировать в буфер обмена:"},
    "settings.hotkey.region": {"en": "Select screen region:", "ru": "Выделить область экрана:"},
    "settings.hotkey_note_wayland": {
        "en": (
            "Wayland session detected: applications cannot intercept global "
            "hotkeys directly. Assign these combinations in your desktop "
            "environment's settings (\"Keyboard/Shortcuts\" section) to the "
            "commands: simple-screenshot --capture (save to file), "
            "simple-screenshot --copy (copy to clipboard) and "
            "simple-screenshot --region (select region)."
        ),
        "ru": (
            "Обнаружена сессия Wayland: приложения не могут перехватывать "
            "глобальные клавиши напрямую. Назначьте эти комбинации в "
            "настройках вашего окружения (раздел «Клавиши/Сочетания клавиш») "
            "на команды: simple-screenshot --capture (сохранить в файл), "
            "simple-screenshot --copy (скопировать в буфер обмена) и "
            "simple-screenshot --region (выделить область)."
        ),
    },
    "settings.hotkey_note_default": {
        "en": (
            "All combinations are intercepted globally at any time during "
            "the session, regardless of which window is active."
        ),
        "ru": (
            "Все комбинации перехватываются глобально в любой момент "
            "работы сессии, независимо от того, какое окно активно."
        ),
    },
    "settings.autostart": {
        "en": "Launch automatically at login (in background, tray only)",
        "ru": "Запускать автоматически при входе в систему (фоново, в трее)",
    },
    "settings.format": {"en": "File format", "ru": "Формат файла"},
    "settings.quality": {"en": "Screenshot quality", "ru": "Качество снимков"},
    "settings.quality.low": {"en": "Low", "ru": "Низкое"},
    "settings.quality.medium": {"en": "Medium", "ru": "Среднее"},
    "settings.quality.high": {"en": "High", "ru": "Высокое"},
    "settings.save": {"en": "Save", "ru": "Сохранить"},
    "settings.cancel": {"en": "Cancel", "ru": "Отмена"},
    "settings.choose_dir_title": {"en": "Select folder to save to", "ru": "Выберите папку для сохранения"},

    "settings.error.title": {"en": "Error", "ru": "Ошибка"},
    "settings.error.no_dir": {"en": "Please specify a save folder.", "ru": "Укажите папку для сохранения."},
    "settings.error.mkdir_failed": {"en": "Failed to create the folder: {error}", "ru": "Не удалось создать папку: {error}"},
    "settings.error.hotkey_missing": {"en": "Set a key combination: {label}", "ru": "Задайте комбинацию клавиш: {label}"},
    "settings.error.hotkey_duplicate": {
        "en": "Hotkeys \u201c{first}\u201d and \u201c{second}\u201d are the same. Assign a unique combination to each action.",
        "ru": "Горячие клавиши «{first}» и «{second}» совпадают. Назначьте каждому действию свою комбинацию.",
    },
    "settings.error.hotkey_invalid_title": {"en": "Invalid combination", "ru": "Некорректная комбинация"},

    # -- выделение области (region_overlay.py) ----------------------------
    "region.hint": {"en": "Select an area with the mouse — Esc to cancel", "ru": "Выделите область мышью — Esc для отмены"},
    "region.save": {"en": "Save", "ru": "Сохранить"},
    "region.copy": {"en": "Copy", "ru": "Копировать"},

    # -- ошибки захвата (capture.py) ---------------------------------------
    "capture.no_screen": {"en": "Could not access the screen.", "ru": "Не удалось получить доступ к экрану."},
    "capture.grab_failed": {"en": "Failed to capture the screen.", "ru": "Не удалось выполнить захват экрана."},
    "capture.grim_missing": {
        "en": (
            "Screen capture on Wayland requires the 'grim' utility. Install "
            "the 'grim' package (and 'slurp' for region selection) via your "
            "distribution's package manager."
        ),
        "ru": (
            "Захват экрана под Wayland требует утилиту 'grim'. Установите "
            "пакет 'grim' (и 'slurp' для выбора области) через менеджер "
            "пакетов вашего дистрибутива."
        ),
    },
    "capture.grim_read_failed": {"en": "Could not read the image captured by grim.", "ru": "Не удалось прочитать снимок, сделанный grim."},
    "capture.grim_call_failed": {"en": "Error calling grim: {error}", "ru": "Ошибка вызова grim: {error}"},
    "capture.mkdir_failed": {"en": "Failed to create the save folder: {error}", "ru": "Не удалось создать папку сохранения: {error}"},
    "capture.save_failed": {"en": "Failed to save the screenshot file.", "ru": "Не удалось сохранить файл скриншота."},
    "capture.clipboard_unavailable": {"en": "Clipboard is not available in this environment.", "ru": "Буфер обмена недоступен в этом окружении."},
    "capture.slurp_grim_missing": {
        "en": (
            "Region selection on Wayland requires the 'slurp' and 'grim' "
            "utilities. Install both packages via your distribution's "
            "package manager."
        ),
        "ru": (
            "Выделение области на Wayland требует утилиты 'slurp' и 'grim'. "
            "Установите оба пакета через менеджер пакетов вашего дистрибутива."
        ),
    },
    "capture.slurp_call_failed": {"en": "Error calling slurp: {error}", "ru": "Ошибка вызова slurp: {error}"},
    "capture.region_read_failed": {"en": "Could not read the captured region image.", "ru": "Не удалось прочитать снимок выделенной области."},
}


def tr(key, **kwargs):
    entry = STRINGS.get(key)
    if entry is None:
        return key
    lang = get_language()
    text = entry.get(lang) or entry.get(DEFAULT_LANGUAGE) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
