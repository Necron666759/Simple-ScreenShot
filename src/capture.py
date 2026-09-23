"""Захват экрана.

На Windows и X11 используется штатный механизм Qt
(QScreen.grabWindow) — он одинаково хорошо работает в обеих системах
без дополнительных зависимостей.

Задел на будущее — Wayland: приложения не могут напрямую читать
содержимое экрана (ограничение протокола в целях безопасности),
поэтому используется внешняя утилита `grim` (стандартный инструмент
для wlroots-совместимых композиторов), а для выделения области —
`slurp` (тоже стандартный компаньон grim, сам показывает интерфейс
выделения средствами композитора). Для GNOME/KDE на Wayland в будущем
можно подключить захват через xdg-desktop-portal
(org.freedesktop.portal.Screenshot).

Копирование в буфер обмена использует штатный QClipboard — он тоже
работает одинаково на X11, Windows и Wayland (это отдельный от захвата
экрана механизм Qt, ограничение Wayland касается только чтения
содержимого экрана, а не буфера обмена).
"""
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
import datetime

from PyQt5.QtGui import QGuiApplication, QImage

from config import QUALITY_MAP
from i18n import tr

# Специальное значение результата — пользователь сам отменил выделение
# области (Esc), это не ошибка и не повод показывать уведомление.
REGION_CANCELLED = "__region_cancelled__"


def is_windows():
    return sys.platform.startswith("win")


def is_wayland():
    if is_windows():
        return False
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    return session_type == "wayland" or bool(os.environ.get("WAYLAND_DISPLAY"))


def make_filename(save_dir, fmt):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    ext = "jpg" if fmt == "jpg" else "png"
    return os.path.join(save_dir, f"Screenshot_{ts}.{ext}")


def _grab_pixmap_qt():
    """Захват через Qt — работает на Windows и на X11 (Linux)."""
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        return False, tr("capture.no_screen")
    pixmap = screen.grabWindow(0)
    if pixmap.isNull():
        return False, tr("capture.grab_failed")
    return True, pixmap


def _grab_pixmap_wayland():
    grim = shutil.which("grim")
    if not grim:
        return False, tr("capture.grim_missing")
    tmp_path = os.path.join(tempfile.gettempdir(), f"simple-screenshot-{uuid.uuid4().hex}.png")
    try:
        subprocess.run([grim, tmp_path], check=True, timeout=10)
        image = QImage(tmp_path)
        if image.isNull():
            return False, tr("capture.grim_read_failed")
        return True, image
    except Exception as e:
        return False, tr("capture.grim_call_failed", error=e)
    finally:
        if os.path.isfile(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def grab_pixmap():
    """Захватывает экран целиком и возвращает (True, QPixmap|QImage)
    либо (False, текст_ошибки)."""
    if is_wayland():
        return _grab_pixmap_wayland()
    return _grab_pixmap_qt()


def save_pixmap(pixmap, cfg):
    """Сохраняет уже готовое изображение (QPixmap/QImage) в файл
    согласно настройкам (папка, формат, качество)."""
    save_dir = os.path.expanduser(cfg.get("save_dir"))
    try:
        os.makedirs(save_dir, exist_ok=True)
    except Exception as e:
        return False, tr("capture.mkdir_failed", error=e)

    fmt = cfg.get("format", "png")
    quality = QUALITY_MAP.get(cfg.get("quality", "high"), 95)
    path = make_filename(save_dir, fmt)
    fmt_qt = "JPG" if fmt == "jpg" else "PNG"

    ok = pixmap.save(path, fmt_qt, quality)
    if not ok:
        return False, tr("capture.save_failed")
    return True, path


def copy_pixmap_to_clipboard(pixmap):
    """Копирует уже готовое изображение (QPixmap/QImage) в буфер обмена."""
    clipboard = QGuiApplication.clipboard()
    if clipboard is None:
        return False, tr("capture.clipboard_unavailable")

    # QImage и QPixmap оба поддерживаются setPixmap/setImage; приводим
    # к единому вызову через наличие метода toImage (есть у QPixmap).
    if hasattr(pixmap, "toImage"):
        clipboard.setPixmap(pixmap)
    else:
        clipboard.setImage(pixmap)
    return True, None


def take_screenshot(cfg):
    """Захватывает весь экран и сохраняет результат в файл."""
    ok, result = grab_pixmap()
    if not ok:
        return False, result
    return save_pixmap(result, cfg)


def copy_screenshot_to_clipboard():
    """Захватывает весь экран и копирует результат в буфер обмена."""
    ok, result = grab_pixmap()
    if not ok:
        return False, result
    return copy_pixmap_to_clipboard(result)


# ---------------------------------------------------------------------
# Выделение произвольной области экрана
# ---------------------------------------------------------------------

def _grab_region_qt():
    """Интерактивное выделение области через собственный оверлей Qt —
    работает на X11 и на Windows (см. region_overlay.py)."""
    from region_overlay import select_region_interactive

    action, rect, background = select_region_interactive()
    if action == "cancel" or rect is None or rect.isNull():
        return "cancelled", None
    cropped = background.copy(rect)
    return "ok", (action, cropped)


def _grab_region_wayland():
    """Выделение области на Wayland через связку slurp (интерактивный
    выбор прямоугольника средствами композитора) + grim (сам захват)."""
    slurp = shutil.which("slurp")
    grim = shutil.which("grim")
    if not slurp or not grim:
        return "error", tr("capture.slurp_grim_missing")
    try:
        result = subprocess.run(slurp, capture_output=True, text=True, timeout=120)
    except Exception as e:
        return "error", tr("capture.slurp_call_failed", error=e)

    geometry = result.stdout.strip()
    if result.returncode != 0 or not geometry:
        # Esc в slurp даёт ненулевой код возврата и пустой вывод — это
        # обычная отмена пользователем, а не ошибка.
        return "cancelled", None

    tmp_path = os.path.join(tempfile.gettempdir(), f"simple-screenshot-region-{uuid.uuid4().hex}.png")
    try:
        subprocess.run([grim, "-g", geometry, tmp_path], check=True, timeout=10)
        image = QImage(tmp_path)
        if image.isNull():
            return "error", tr("capture.region_read_failed")
    except Exception as e:
        return "error", tr("capture.grim_call_failed", error=e)
    finally:
        if os.path.isfile(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    # На Wayland slurp уже отработал как интерфейс выделения, отдельную
    # панель "сохранить/скопировать" поверх не показываем — область
    # сразу сохраняется в файл (как и обычный снимок всего экрана).
    return "ok", ("save", image)


def grab_region_pixmap():
    """Возвращает (status, payload):
    - ("ok", (action, pixmap))  — область выделена; action = 'save' | 'copy'
    - ("cancelled", None)       — пользователь отменил выделение (Esc)
    - ("error", сообщение)      — не удалось выполнить выделение/захват
    """
    if is_wayland():
        return _grab_region_wayland()
    return _grab_region_qt()


def capture_region(cfg):
    """Высокоуровневая функция: выделить область и сохранить в файл или
    скопировать в буфер обмена (выбор — в оверлее выделения).

    Возвращает:
      (True, path)                — область сохранена в файл, path — путь
      (True, None)                — область скопирована в буфер обмена
      (False, REGION_CANCELLED)   — пользователь сам отменил выделение
      (False, сообщение)          — произошла ошибка
    """
    status, payload = grab_region_pixmap()
    if status == "cancelled":
        return False, REGION_CANCELLED
    if status == "error":
        return False, payload

    action, pixmap = payload
    if action == "copy":
        return copy_pixmap_to_clipboard(pixmap)
    return save_pixmap(pixmap, cfg)
