@echo off
REM Полная сборка Simple Screenshot для Windows: PyInstaller -> Inno Setup.
REM Запускать этот файл на Windows 10/11 из папки packaging\windows.
REM Требования: Python 3.9+ в PATH, установленный Inno Setup 6
REM (https://jrsoftware.org/isinfo.php), доступ к интернету для pip install.

setlocal

echo === 1. Установка Python-зависимостей ===
python -m pip install --upgrade pip
python -m pip install -r requirements-windows.txt
if errorlevel 1 goto :error

echo === 2. Сборка .exe через PyInstaller ===
pyinstaller --noconfirm --clean simple-screenshot.spec
if errorlevel 1 goto :error

echo === 3. Поиск компилятора Inno Setup (ISCC.exe) ===
set "ISCC="
for %%P in (
    "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
    "%ProgramFiles%\Inno Setup 6\ISCC.exe"
) do (
    if exist %%P set "ISCC=%%~P"
)

if "%ISCC%"=="" (
    echo.
    echo [!] Inno Setup 6 не найден. Установите его с https://jrsoftware.org/isdl.php
    echo     и запустите этот скрипт заново, либо вручную выполните:
    echo     iscc installer.iss
    goto :error
)

echo === 4. Сборка установщика через Inno Setup ===
"%ISCC%" installer.iss
if errorlevel 1 goto :error

echo.
echo === Готово! ===
echo Установщик находится в папке: ..\..\dist\SimpleScreenshot-Setup-*.exe
goto :eof

:error
echo.
echo Сборка завершилась с ошибкой.
exit /b 1
