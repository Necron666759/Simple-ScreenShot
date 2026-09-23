import os
import sys

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMenu, QSystemTrayIcon

import config as cfgmod
from capture import (
    REGION_CANCELLED,
    capture_region as do_capture_region,
    copy_screenshot_to_clipboard,
    is_wayland,
    take_screenshot,
)
from settings_dialog import SettingsDialog

ICON_PATH_SYSTEM = "/usr/share/icons/hicolor/scalable/apps/simple-screenshot.svg"

# Клавиши по умолчанию для каждого действия (используются, если в
# конфиге вдруг нет соответствующего ключа — например, после обновления
# приложения со старой версии конфига).
HOTKEY_DEFAULTS = {
    "hotkey": "Print",
    "clipboard_hotkey": "Ctrl+Print",
    "region_hotkey": "Shift+Print",
}


def _bundled_assets_dir():
    """Каталог с иконками рядом со скриптом либо внутри сборки PyInstaller."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "assets")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def find_icon():
    candidates = [
        os.path.join(_bundled_assets_dir(), "simple-screenshot.ico"),
        os.path.join(_bundled_assets_dir(), "simple-screenshot.svg"),
        ICON_PATH_SYSTEM,
    ]
    for p in candidates:
        if os.path.isfile(p):
            return QIcon(p)
    return QIcon.fromTheme("camera-photo", QIcon.fromTheme("applets-screenshooter"))


class TrayApp(QObject):
    # Какие горячие клавиши поддерживает приложение: ключ конфига -> имя
    # метода-обработчика (строки, т.к. используются через getattr после
    # того как все методы класса уже определены).
    HOTKEY_ACTIONS = (
        ("hotkey", "capture_now"),
        ("clipboard_hotkey", "capture_to_clipboard"),
        ("region_hotkey", "capture_region"),
    )

    # Хоткеи перехватываются в ФОНОВОМ потоке (см. hotkey/x11.py и
    # hotkey/windows.py), а создавать/показывать виджеты Qt (например,
    # оверлей выделения области) можно только в главном потоке.
    # pyqtSignal, испущенный из другого потока, Qt автоматически
    # доставляет в основной event loop как QueuedConnection — это и
    # обеспечивает безопасный переход из потока хоткея в главный поток.
    _hotkey_triggered = pyqtSignal(str)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.cfg = cfgmod.load_config()
        self.icon = find_icon()

        self.tray = QSystemTrayIcon(self.icon, self.app)
        self.tray.setToolTip("Simple Screenshot")
        self._build_menu()
        self.tray.activated.connect(self._on_activated)
        self.tray.show()

        self._hotkey_triggered.connect(self._dispatch_hotkey_action)

        # cfg_key -> экземпляр GlobalHotkey/GlobalHotkeyWindows
        self._hotkeys = {}
        self._setup_hotkeys()

        self.settings_dialog_instance = None

    def _build_menu(self):
        menu = QMenu()

        capture_action = QAction("Сделать снимок сейчас", menu)
        capture_action.triggered.connect(self.capture_now)
        menu.addAction(capture_action)

        clipboard_action = QAction("Скопировать снимок в буфер обмена", menu)
        clipboard_action.triggered.connect(self.capture_to_clipboard)
        menu.addAction(clipboard_action)

        region_action = QAction("Выделить область экрана…", menu)
        region_action.triggered.connect(self.capture_region)
        menu.addAction(region_action)

        settings_action = QAction("Настройки…", menu)
        settings_action.triggered.connect(self.open_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        quit_action = QAction("Выход", menu)
        quit_action.triggered.connect(self.app.quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.capture_now()

    # -- горячие клавиши ------------------------------------------------
    def _setup_hotkeys(self):
        if is_wayland():
            # Глобальные хоткеи на Wayland настраиваются средствами самого
            # окружения (см. подсказку в SettingsDialog).
            return
        for cfg_key, method_name in self.HOTKEY_ACTIONS:
            self._register_hotkey(cfg_key, method_name)

    def _register_hotkey(self, cfg_key, method_name):
        try:
            from hotkey import create_hotkey
            default = HOTKEY_DEFAULTS[cfg_key]
            # Коллбэк вызывается из фонового потока хоткея — не выполняем
            # там саму работу (особенно небезопасно для оверлея выделения
            # области, который создаёт виджеты Qt), а лишь испускаем
            # сигнал, который Qt безопасно доставит в главный поток.
            callback = lambda mn=method_name: self._hotkey_triggered.emit(mn)
            self._hotkeys[cfg_key] = create_hotkey(self.cfg.get(cfg_key, default), callback)
        except Exception as e:
            print(f"[simple-screenshot] Не удалось назначить горячую клавишу '{cfg_key}': {e}")

    def _dispatch_hotkey_action(self, method_name):
        """Выполняется в главном потоке (см. _hotkey_triggered)."""
        getattr(self, method_name)()

    # -- действия --------------------------------------------------------
    def capture_now(self):
        ok, result = take_screenshot(self.cfg)
        if ok:
            self.tray.showMessage(
                "Simple Screenshot", f"Скриншот сохранён:\n{result}",
                QSystemTrayIcon.Information, 3000,
            )
        else:
            self.tray.showMessage(
                "Simple Screenshot", f"Ошибка: {result}",
                QSystemTrayIcon.Warning, 5000,
            )

    def capture_to_clipboard(self):
        ok, error = copy_screenshot_to_clipboard()
        if ok:
            self.tray.showMessage(
                "Simple Screenshot", "Скриншот скопирован в буфер обмена",
                QSystemTrayIcon.Information, 2500,
            )
        else:
            self.tray.showMessage(
                "Simple Screenshot", f"Ошибка: {error}",
                QSystemTrayIcon.Warning, 5000,
            )

    def capture_region(self):
        ok, result = do_capture_region(self.cfg)
        if not ok:
            if result == REGION_CANCELLED:
                return  # пользователь сам отменил выделение — без уведомления
            self.tray.showMessage(
                "Simple Screenshot", f"Ошибка: {result}",
                QSystemTrayIcon.Warning, 5000,
            )
            return

        if result is None:
            self.tray.showMessage(
                "Simple Screenshot", "Выделенная область скопирована в буфер обмена",
                QSystemTrayIcon.Information, 2500,
            )
        else:
            self.tray.showMessage(
                "Simple Screenshot", f"Выделенная область сохранена:\n{result}",
                QSystemTrayIcon.Information, 3000,
            )

    def open_settings(self):
        if self.settings_dialog_instance is not None:
            self.settings_dialog_instance.raise_()
            self.settings_dialog_instance.activateWindow()
            return
        dlg = SettingsDialog(self.cfg, self._apply_new_config)
        self.settings_dialog_instance = dlg
        dlg.exec_()
        self.settings_dialog_instance = None

    def _apply_new_config(self, new_cfg):
        self.cfg = new_cfg
        if is_wayland():
            return
        for cfg_key, method_name in self.HOTKEY_ACTIONS:
            default = HOTKEY_DEFAULTS[cfg_key]
            existing = self._hotkeys.get(cfg_key)
            if existing:
                try:
                    existing.set_hotkey(self.cfg.get(cfg_key, default))
                except Exception as e:
                    print(f"[simple-screenshot] Не удалось обновить горячую клавишу '{cfg_key}': {e}")
            else:
                self._register_hotkey(cfg_key, method_name)

    def handle_ipc_command(self, command):
        command = command.strip()
        if command == "capture":
            self.capture_now()
        elif command == "clipboard":
            self.capture_to_clipboard()
        elif command == "region":
            self.capture_region()
        elif command == "settings":
            self.open_settings()
        elif command == "quit":
            self.app.quit()
