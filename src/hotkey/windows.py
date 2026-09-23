"""Глобальный перехват горячей клавиши на Windows через штатный WinAPI
RegisterHotKey/UnregisterHotKey (user32.dll) с помощью ctypes — без
сторонних библиотек, по аналогии с XGrabKey в модуле для X11.

RegisterHotKey регистрирует комбинацию за потоком, который его вызвал,
поэтому регистрация и цикл обработки сообщений выполняются в одном и
том же выделенном потоке.
"""
import ctypes
import itertools
import threading
from ctypes import wintypes

from .common import HotkeyError

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

MOD_ALIASES = {
    "ctrl": MOD_CONTROL,
    "control": MOD_CONTROL,
    "alt": MOD_ALT,
    "shift": MOD_SHIFT,
    "win": MOD_WIN,
    "super": MOD_WIN,
    "meta": MOD_WIN,
}

# Именованные клавиши -> виртуальный код клавиши Windows (VK_*)
VK_MAP = {
    "print": 0x2C, "printscreen": 0x2C, "prtsc": 0x2C, "prntscrn": 0x2C,
    "esc": 0x1B, "escape": 0x1B,
    "space": 0x20, "tab": 0x09,
    "enter": 0x0D, "return": 0x0D,
    "delete": 0x2E, "del": 0x2E,
    "insert": 0x2D, "ins": 0x2D,
    "home": 0x24, "end": 0x23,
    "pageup": 0x21, "pagedown": 0x22,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73, "f5": 0x74, "f6": 0x75,
    "f7": 0x76, "f8": 0x77, "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
}

WM_HOTKEY = 0x0312
PM_REMOVE = 0x0001
_id_counter = itertools.count(1)


def parse_hotkey(text):
    """Разбирает строку вида 'Ctrl+Shift+S' или 'Print' в (modifiers, vk)."""
    parts = [p for p in text.replace(" ", "").split("+") if p]
    if not parts:
        raise HotkeyError("Пустая комбинация клавиш.")

    modifiers = 0
    key_part = parts[-1]
    for p in parts[:-1]:
        m = MOD_ALIASES.get(p.lower())
        if m is None:
            raise HotkeyError(f"Неизвестный модификатор: {p}")
        modifiers |= m

    key_lower = key_part.lower()
    if key_lower in VK_MAP:
        vk = VK_MAP[key_lower]
    elif len(key_part) == 1 and key_part.isalnum():
        vk = ord(key_part.upper())
    else:
        raise HotkeyError(f"Неизвестная или неподдерживаемая клавиша: {key_part}")
    return modifiers, vk


class GlobalHotkeyWindows:
    """Перехватывает одну глобальную комбинацию клавиш и вызывает callback."""

    def __init__(self, hotkey_text, callback):
        self.callback = callback
        self._thread = None
        self._stop_event = threading.Event()
        self.modifiers = 0
        self.vk = 0
        self.hotkey_id = next(_id_counter)
        self.set_hotkey(hotkey_text)

    def set_hotkey(self, hotkey_text):
        self.stop()
        self.modifiers, self.vk = parse_hotkey(hotkey_text)
        self.start()

    def _run(self):
        user32 = ctypes.windll.user32
        ok = user32.RegisterHotKey(None, self.hotkey_id, self.modifiers | MOD_NOREPEAT, self.vk)
        if not ok:
            print(
                "[simple-screenshot] Не удалось зарегистрировать горячую клавишу "
                "(возможно, она уже занята другой программой)."
            )
            return
        try:
            msg = wintypes.MSG()
            while not self._stop_event.is_set():
                has_msg = user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE)
                if has_msg:
                    if msg.message == WM_HOTKEY and msg.wParam == self.hotkey_id:
                        try:
                            self.callback()
                        except Exception:
                            pass
                else:
                    self._stop_event.wait(0.05)
        finally:
            user32.UnregisterHotKey(None, self.hotkey_id)

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=1)
        self._thread = None
