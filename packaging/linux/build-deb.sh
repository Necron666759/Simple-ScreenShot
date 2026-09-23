#!/bin/sh
# Собирает simple-screenshot_<version>_all.deb из общего кроссплатформенного
# src/ и метаданных packaging/linux. Запускать на Linux (Debian/Ubuntu) с
# установленным dpkg-deb.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SRC_DIR="$PROJECT_ROOT/src"
LINUX_META_DIR="$SCRIPT_DIR"

VERSION="$(grep -m1 '^Version:' "$LINUX_META_DIR/DEBIAN/control" | awk '{print $2}')"
PKG_ROOT="$PROJECT_ROOT/build/simple-screenshot_${VERSION}_all"

rm -rf "$PKG_ROOT"
mkdir -p "$PKG_ROOT"

cp -r "$LINUX_META_DIR"/DEBIAN "$PKG_ROOT/"
cp -r "$LINUX_META_DIR"/usr "$PKG_ROOT/"

mkdir -p "$PKG_ROOT/usr/lib/simple-screenshot"
cp "$SRC_DIR"/main.py "$SRC_DIR"/config.py "$SRC_DIR"/capture.py \
   "$SRC_DIR"/ipc.py "$SRC_DIR"/tray_app.py "$SRC_DIR"/settings_dialog.py \
   "$SRC_DIR"/region_overlay.py "$SRC_DIR"/i18n.py \
   "$PKG_ROOT/usr/lib/simple-screenshot/"

# hotkey/ и autostart/ — берём только Linux-релевантные файлы.
# windows.py (WinAPI-хоткей и реестровый автозапуск) в Linux-пакет не
# кладём: он никогда не импортируется на этой ОС (выбор бэкенда идёт по
# sys.platform в рантайме) и был бы мёртвым грузом, только раздувающим .deb.
mkdir -p "$PKG_ROOT/usr/lib/simple-screenshot/hotkey"
cp "$SRC_DIR"/hotkey/__init__.py "$SRC_DIR"/hotkey/common.py "$SRC_DIR"/hotkey/x11.py \
   "$PKG_ROOT/usr/lib/simple-screenshot/hotkey/"

mkdir -p "$PKG_ROOT/usr/lib/simple-screenshot/autostart"
cp "$SRC_DIR"/autostart/__init__.py "$SRC_DIR"/autostart/linux.py \
   "$PKG_ROOT/usr/lib/simple-screenshot/autostart/"

# assets/ — только svg (используется как запасной путь поиска иконки в
# tray_app.py); .ico нужен исключительно для сборки под Windows и в
# Linux-пакет не входит.
mkdir -p "$PKG_ROOT/usr/lib/simple-screenshot/assets"
cp "$SRC_DIR"/assets/simple-screenshot.svg \
   "$PKG_ROOT/usr/lib/simple-screenshot/assets/"

find "$PKG_ROOT" -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

chmod 0755 "$PKG_ROOT/DEBIAN/postinst" "$PKG_ROOT/DEBIAN/postrm"
chmod 0755 "$PKG_ROOT/usr/bin/simple-screenshot"
chmod 0755 "$PKG_ROOT/usr/lib/simple-screenshot/main.py"
find "$PKG_ROOT/usr/lib/simple-screenshot" -name "*.py" ! -name main.py -exec chmod 0644 {} \;
find "$PKG_ROOT" -type d -exec chmod 0755 {} \;
find "$PKG_ROOT" -name "*.svg" -o -name "*.ico" | xargs -r chmod 0644
chmod 0644 "$PKG_ROOT/DEBIAN/control"

dpkg-deb --build --root-owner-group "$PKG_ROOT"
echo "Готово: $PROJECT_ROOT/build/simple-screenshot_${VERSION}_all.deb"
