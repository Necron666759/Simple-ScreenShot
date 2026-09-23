"""Кроссплатформенное управление автозапуском.

Использование:
    import autostart
    autostart.set_autostart(True)
    autostart.is_enabled()
"""
import sys

if sys.platform.startswith("win"):
    from .windows import is_enabled, set_autostart
else:
    from .linux import is_enabled, set_autostart

__all__ = ["is_enabled", "set_autostart"]
