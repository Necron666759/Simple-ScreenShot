"""Автозапуск через freedesktop-стандарт ~/.config/autostart — работает
во всех окружениях, поддерживающих XDG Autostart (XFCE, GNOME, KDE,
Budgie, MATE, Cinnamon и др.)."""
import os

AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")
DESKTOP_FILE = os.path.join(AUTOSTART_DIR, "simple-screenshot.desktop")

DESKTOP_CONTENT = """[Desktop Entry]
Type=Application
Name=Simple Screenshot
Comment=Захват экрана в фоне (значок в трее)
Exec=/usr/bin/simple-screenshot
Icon=simple-screenshot
Terminal=false
X-GNOME-Autostart-enabled=true
Hidden=false
X-GNOME-Autostart-Delay=5
"""


def is_enabled():
    return os.path.isfile(DESKTOP_FILE)


def set_autostart(enabled):
    os.makedirs(AUTOSTART_DIR, exist_ok=True)
    if enabled:
        with open(DESKTOP_FILE, "w", encoding="utf-8") as f:
            f.write(DESKTOP_CONTENT)
    else:
        if os.path.isfile(DESKTOP_FILE):
            os.remove(DESKTOP_FILE)
