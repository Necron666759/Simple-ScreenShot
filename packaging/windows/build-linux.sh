#!/bin/bash
# Полная сборка Simple Screenshot под Windows — ЦЕЛИКОМ на Linux, без
# участия настоящей Windows-машины. Используется Wine только для запуска
# PyInstaller (реальный Windows Python + PyQt5 внутри Wine собирают
# нативный .exe), а сами установщики (.exe через NSIS и .msi через
# msitools/wixl) компилируются полностью нативными Linux-инструментами.
#
# Требования (Debian/Ubuntu):
#   sudo dpkg --add-architecture i386
#   sudo apt update
#   sudo apt install -y wine wine32:i386 wine64 nsis msitools wixl wixl-data zstd
#
# Запуск:
#   cd packaging/windows
#   ./build-linux.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PY_VERSION="3.12.14"
PY_TAG="20260901"
PY_URL="https://github.com/astral-sh/python-build-standalone/releases/download/${PY_TAG}/cpython-${PY_VERSION}+${PY_TAG}-x86_64-pc-windows-msvc-install_only.tar.gz"

WINBUILD_DIR="$SCRIPT_DIR/.winbuild"
WINEPREFIX="$WINBUILD_DIR/wineprefix"
PY_DIR="$WINBUILD_DIR/python"

export WINEPREFIX
export WINEARCH=win64
export WINEDEBUG=-all

echo "=== 1. Portable Windows Python ==="
if [ ! -x "$PY_DIR/python.exe" ]; then
    mkdir -p "$WINBUILD_DIR"
    if [ ! -f "$WINBUILD_DIR/python-windows.tar.gz" ]; then
        echo "Скачивание portable Windows Python ${PY_VERSION} (python-build-standalone)…"
        curl -L -o "$WINBUILD_DIR/python-windows.tar.gz" "$PY_URL"
    fi
    tar -xzf "$WINBUILD_DIR/python-windows.tar.gz" -C "$WINBUILD_DIR"
fi
"$PY_DIR/python.exe" --version || true

echo "=== 2. Инициализация Wine-префикса ==="
if [ ! -d "$WINEPREFIX" ]; then
    wineboot --init
fi

echo "=== 3. Установка PyQt5 + PyInstaller под Wine (настоящие Windows-колёса с PyPI) ==="
wine "$PY_DIR/python.exe" -m pip install --upgrade pip --quiet
wine "$PY_DIR/python.exe" -m pip install --quiet -r requirements-windows.txt

echo "=== 4. Сборка SimpleScreenshot.exe через PyInstaller (внутри Wine) ==="
wine "$PY_DIR/python.exe" -m PyInstaller --noconfirm --clean simple-screenshot.spec

if [ ! -f "dist/SimpleScreenshot.exe" ]; then
    echo "Ошибка: PyInstaller не создал dist/SimpleScreenshot.exe" >&2
    exit 1
fi

echo "=== 5. Сборка .exe-установщика через NSIS (нативно на Linux, makensis) ==="
if command -v makensis >/dev/null 2>&1; then
    makensis installer.nsi
else
    echo "[!] makensis не найден — пропускаю сборку .exe-инсталлятора."
    echo "    Установите: sudo apt install nsis"
fi

echo "=== 6. Сборка .msi через wixl (msitools, нативно на Linux) ==="
if command -v wixl >/dev/null 2>&1; then
    wixl -o "dist/SimpleScreenshot-1.3.2.msi" installer.wxs
else
    echo "[!] wixl не найден — пропускаю сборку .msi."
    echo "    Установите: sudo apt install wixl wixl-data"
fi

echo
echo "=== Готово ==="
ls -la dist/*.exe dist/*.msi 2>/dev/null
