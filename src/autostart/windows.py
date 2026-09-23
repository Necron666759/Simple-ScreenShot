"""Автозапуск на Windows через стандартный пользовательский ключ реестра
HKEY_CURRENT_USER\\...\\Run — не требует прав администратора и не
создаёт файлов в системных папках."""
import sys

RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "SimpleScreenshot"


def _get_exe_command():
    exe = sys.executable
    # При запуске из PyInstaller-сборки sys.executable указывает на сам
    # .exe приложения. При запуске из обычного python.exe (например, при
    # отладке) добавляем путь к скрипту, чтобы автозапуск тоже работал.
    if getattr(sys, "frozen", False):
        return f'"{exe}"'
    return f'"{exe}" "{sys.argv[0]}"'


def is_enabled():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False


def set_autostart(enabled):
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH) as key:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _get_exe_command())
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
