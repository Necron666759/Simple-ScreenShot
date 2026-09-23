"""Глобальный перехват горячей клавиши в сессии X11 (работает в любом
X11-окружении: XFCE, GNOME on Xorg, KDE Plasma on Xorg, Budgie, MATE и т.д.),
через штатный механизм XGrabKey из python3-xlib — без сторонних демонов.

Под Wayland глобальный перехват клавиш приложениями запрещён протоколом
из соображений безопасности — это ограничение не Simple Screenshot, а
самого Wayland. Поэтому под Wayland пользователю нужно назначить свою
комбинацию клавиш в настройках самого окружения (Параметры -> Клавиши
быстрого доступа) на команду `simple-screenshot --capture`.
"""
import threading

from Xlib import X, XK, display

from .common import HotkeyError

MOD_MASKS = {
    "ctrl": X.ControlMask,
    "control": X.ControlMask,
    "alt": X.Mod1Mask,
    "shift": X.ShiftMask,
    "super": X.Mod4Mask,
    "meta": X.Mod4Mask,
}

# Приведение имён клавиш из Qt (QKeySequence) к именам X11 keysym
KEY_ALIASES = {
    "print": "Print",
    "printscreen": "Print",
    "prtsc": "Print",
    "prntscrn": "Print",
    "esc": "Escape",
}

# Дополнительные маски модификаторов, которые нужно игнорировать
# (CapsLock и NumLock не должны мешать срабатыванию хоткея)
IGNORED_MASKS = [0, X.LockMask, X.Mod2Mask, X.LockMask | X.Mod2Mask]


def parse_hotkey(text):
    """Разбирает строку вида 'Ctrl+Shift+S' или 'Print' в (modmask, keysym)."""
    parts = [p for p in text.replace(" ", "").split("+") if p]
    if not parts:
        raise HotkeyError("Пустая комбинация клавиш.")

    modmask = 0
    key_part = parts[-1]
    for p in parts[:-1]:
        m = MOD_MASKS.get(p.lower())
        if m is None:
            raise HotkeyError(f"Неизвестный модификатор: {p}")
        modmask |= m

    key_lookup = KEY_ALIASES.get(key_part.lower(), key_part)
    keysym = XK.string_to_keysym(key_lookup)
    if keysym == 0:
        keysym = XK.string_to_keysym(key_lookup.capitalize())
    if keysym == 0:
        keysym = XK.string_to_keysym(key_lookup.lower())
    if keysym == 0:
        raise HotkeyError(f"Неизвестная или неподдерживаемая клавиша: {key_part}")
    return modmask, keysym


class GlobalHotkey:
    """Перехватывает одну глобальную комбинацию клавиш и вызывает callback."""

    def __init__(self, hotkey_text, callback):
        self.callback = callback
        self._stop = threading.Event()
        self._thread = None
        self.disp = display.Display()
        self.root = self.disp.screen().root
        self.modmask = 0
        self.keysym = 0
        self.keycode = 0
        self.set_hotkey(hotkey_text)

    def set_hotkey(self, hotkey_text):
        self.stop()
        self.modmask, self.keysym = parse_hotkey(hotkey_text)
        self.keycode = self.disp.keysym_to_keycode(self.keysym)
        if self.keycode == 0:
            raise HotkeyError("Клавиша недоступна на текущей раскладке.")
        self.start()

    def _grab(self):
        for extra in IGNORED_MASKS:
            try:
                self.root.grab_key(
                    self.keycode, self.modmask | extra, True,
                    X.GrabModeAsync, X.GrabModeAsync,
                )
            except Exception:
                pass

    def _ungrab(self):
        for extra in IGNORED_MASKS:
            try:
                self.root.ungrab_key(self.keycode, self.modmask | extra)
            except Exception:
                pass

    def _loop(self):
        self.root.change_attributes(event_mask=X.KeyPressMask)
        self._grab()
        self.disp.sync()
        try:
            while not self._stop.is_set():
                if self.disp.pending_events() == 0:
                    self._stop.wait(0.05)
                    continue
                event = self.disp.next_event()
                if event.type == X.KeyPress and event.detail == self.keycode:
                    try:
                        self.callback()
                    except Exception:
                        pass
        finally:
            self._ungrab()
            try:
                self.disp.sync()
            except Exception:
                pass

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        if self._thread and self._thread.is_alive():
            self._stop.set()
            self._thread.join(timeout=1)
        self._thread = None
