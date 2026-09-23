"""Кроссплатформенный доступ к глобальным горячим клавишам.

Использование:
    from hotkey import create_hotkey, parse_hotkey, HotkeyError
"""
import sys

from .common import HotkeyError

__all__ = ["create_hotkey", "parse_hotkey", "HotkeyError"]


def parse_hotkey(text):
    if sys.platform.startswith("win"):
        from .windows import parse_hotkey as _parse
    else:
        from .x11 import parse_hotkey as _parse
    return _parse(text)


def create_hotkey(hotkey_text, callback):
    """Создаёт и сразу активирует перехватчик горячей клавиши."""
    if sys.platform.startswith("win"):
        from .windows import GlobalHotkeyWindows as Impl
    else:
        from .x11 import GlobalHotkey as Impl
    return Impl(hotkey_text, callback)
