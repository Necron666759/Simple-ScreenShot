"""Хранение и загрузка настроек приложения Simple Screenshot."""
import json
import os
import sys


def _default_save_dir():
    if sys.platform.startswith("win"):
        base = os.environ.get("USERPROFILE") or os.path.expanduser("~")
        return os.path.join(base, "Pictures", "Screenshots")

    for candidate in ("~/Изображения/Скриншоты", "~/Pictures/Screenshots"):
        parent = os.path.expanduser(os.path.dirname(candidate))
        if os.path.isdir(parent):
            return os.path.expanduser(candidate)
    return os.path.expanduser("~/Screenshots")


def _default_config_dir():
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "SimpleScreenshot")
    return os.path.expanduser("~/.config/simple-screenshot")


CONFIG_DIR = _default_config_dir()
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "save_dir": _default_save_dir(),
    "hotkey": "Print",
    "clipboard_hotkey": "Ctrl+Print",
    "region_hotkey": "Shift+Print",
    "autostart": False,
    "format": "png",       # "png" | "jpg"
    "quality": "high",     # "low" | "medium" | "high"
}

# Соответствие уровня качества числовому параметру для QPixmap.save()/QImage.save()
QUALITY_MAP = {
    "low": 40,
    "medium": 70,
    "high": 95,
}


def load_config():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.isfile(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        cfg = dict(DEFAULT_CONFIG)
        cfg.update(data)
        return cfg
    except Exception:
        return dict(DEFAULT_CONFIG)


def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
