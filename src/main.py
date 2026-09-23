#!/usr/bin/env python3
"""Simple Screenshot — простой захват экрана с иконкой в трее.

Использование:
  simple-screenshot                запускает приложение в трее (или, если
                                    уже запущено, ничего не делает)
  simple-screenshot --capture      делает снимок немедленно и сохраняет
                                    его в файл; если приложение уже
                                    работает в трее — просто отправляет
                                    ему команду (удобно для назначения на
                                    хоткей в окружениях Wayland)
  simple-screenshot --copy         делает снимок немедленно и копирует
                                    его в буфер обмена (тоже удобно для
                                    хоткея на Wayland — отдельная команда
                                    от --capture)
  simple-screenshot --region       открывает интерактивное выделение
                                    области экрана (сохранить в файл или
                                    скопировать в буфер — выбор в самом
                                    выделении; на Wayland сразу сохраняет)
  simple-screenshot --settings     открывает окно настроек
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

# Сколько секунд ждать появления системного трея при старте, прежде чем
# сдаться и показать ошибку. Нужно из-за автозапуска: при входе в сессию
# simple-screenshot может стартовать раньше, чем панель (например,
# xfce4-panel) успеет зарегистрировать в DBus сервис трея — в этот
# момент isSystemTrayAvailable() ещё честно вернёт False, хотя трей
# появится буквально через пару секунд.
TRAY_WAIT_TIMEOUT = 15
TRAY_POLL_INTERVAL = 0.5

import ipc
from tray_app import TrayApp


def main():
    args = sys.argv[1:]

    if "--capture" in args:
        if ipc.send_command("capture"):
            return 0
    elif "--copy" in args:
        if ipc.send_command("clipboard"):
            return 0
    elif "--region" in args:
        if ipc.send_command("region"):
            return 0
    elif "--settings" in args:
        if ipc.send_command("settings"):
            return 0
    elif "--quit" in args:
        if ipc.send_command("quit"):
            return 0
        return 0
    else:
        # Обычный запуск без аргументов: если приложение уже работает в
        # трее, не создаём второй экземпляр.
        if ipc.send_command("ping", timeout=200):
            return 0

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Simple Screenshot")

    if not QSystemTrayIcon.isSystemTrayAvailable():
        # Не сдаёмся сразу — это часто автозапуск, и панель рабочего
        # стола может ещё не успеть поднять трей. Подождём немного,
        # периодически перепроверяя.
        deadline = time.monotonic() + TRAY_WAIT_TIMEOUT
        while time.monotonic() < deadline:
            app.processEvents()
            time.sleep(TRAY_POLL_INTERVAL)
            if QSystemTrayIcon.isSystemTrayAvailable():
                break

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(
            None, "Simple Screenshot",
            "Системный трей недоступен в этом окружении рабочего стола.",
        )
        return 1

    tray_app = TrayApp(app)
    ipc.start_server(tray_app.handle_ipc_command)

    if "--capture" in args:
        tray_app.capture_now()
    elif "--copy" in args:
        tray_app.capture_to_clipboard()
    elif "--region" in args:
        tray_app.capture_region()
    elif "--settings" in args:
        tray_app.open_settings()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
