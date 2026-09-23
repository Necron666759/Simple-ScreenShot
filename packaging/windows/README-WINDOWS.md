# Simple Screenshot — сборка под Windows 10/11

Код приложения кроссплатформенный (общий `src/` для Linux и Windows).
Есть **три способа** получить установщик — от «уже готово» до «собери
сам»:

## Способ 1: готовые файлы уже в этой поставке

В комплекте с этим README лежат уже собранные и проверенные файлы —
`SimpleScreenshot.exe`, `SimpleScreenshot-Setup-1.3.0.exe` (NSIS) и
`SimpleScreenshot-1.3.0.msi` (WiX/MSI). Их можно сразу переносить на
Windows 10/11 и запускать. Как именно они собраны и проверены — см.
раздел «Как это собрано» ниже.

## Способ 2: пересобрать самому — но тоже на Linux, без Windows

Реальный Windows `.exe` можно получить, не имея под рукой ни одной
Windows-машины: PyInstaller запускается под **Wine** с настоящим
portable-сборкой Windows Python (проект `python-build-standalone`),
а установщики `.exe` (NSIS) и `.msi` (wixl/msitools) компилируются уже
нативными Linux-инструментами — без Wine.

Требования (Debian/Ubuntu):
```bash
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install -y wine wine32:i386 wine64 nsis msitools wixl wixl-data zstd curl
```

Сборка одной командой:
```bash
cd packaging/windows
./build-linux.sh
```

Скрипт сам:
1. скачивает portable Windows Python 3.12 (с GitHub-релизов
   `astral-sh/python-build-standalone`) — один раз, дальше берётся из кэша
   `packaging/windows/.winbuild/`;
2. поднимает Wine-префикс и ставит в него `PyQt5` + `pyinstaller`
   (настоящие Windows-колёса с PyPI, устанавливаются через pip внутри Wine);
3. запускает PyInstaller **под Wine** — получается подлинный Windows
   PE32+ `.exe` (это единственный шаг, где вообще нужен Wine);
4. собирает `.exe`-установщик через `makensis` (NSIS) — **нативно на
   Linux**, без Wine;
5. собирает `.msi` через `wixl` (msitools) — тоже **нативно на Linux**.

Результат — в `packaging/windows/dist/`:
`SimpleScreenshot.exe`, `SimpleScreenshot-Setup-1.3.0.exe`,
`SimpleScreenshot-1.3.0.msi`.

## Способ 3: сборка в облаке через GitHub Actions

Если не хочется ставить Wine/NSIS/msitools локально — то же самое
можно сделать на обычном `ubuntu-latest` раннере GitHub Actions
(никакой Windows-машины CI тоже не требуется):

1. Залейте содержимое этого архива в репозиторий на GitHub.
2. Вкладка **Actions** → запустите workflow **Build Windows Installer**
   вручную, либо запушьте тег `v*`.
3. Заберите готовые `.exe`/`.msi` из артефактов запуска
   (`SimpleScreenshot-Windows-Installers`).

## Способ 4 (альтернатива): по старинке, на настоящей Windows

Если всё же есть Windows-машина — можно собрать классическим способом
через **Inno Setup**:

```bat
cd packaging\windows
build.bat
```

Требует Python 3.9+ и Inno Setup 6 (https://jrsoftware.org/isdl.php),
использует `simple-screenshot.spec` и `installer.iss`.

## Как это собрано и проверено (для интересующихся)

- `SimpleScreenshot.exe` собран PyInstaller-ом (режим `--onefile`),
  запущенным под Wine поверх настоящего Windows-Python 3.12.14; итоговый
  файл подтверждён утилитой `file` как `PE32+ executable (GUI) x86-64,
  for MS Windows`.
- `SimpleScreenshot-Setup-1.3.0.exe` — самораспаковывающийся установщик
  NSIS с мастером (выбор пути, ярлык на рабочем столе, галочка
  автозапуска, деинсталлятор, запись в «Установка и удаление программ»).
  Проверен реальной тихой установкой `wine SimpleScreenshot-Setup...exe
  /S` в чистом Wine-префиксе — файлы, ярлыки и ключи реестра создаются
  корректно.
- `SimpleScreenshot-1.3.0.msi` — настоящий MSI (подтверждён `file` как
  `MSI Installer`, у него корректные таблицы `File`, `Registry`,
  `Shortcut`, `Feature` и т.д.). Проверен установкой через
  `wine msiexec /i ... /qn` — тоже успешно.

## Что делает установщик

- Ставит приложение в `%LOCALAPPDATA%\SimpleScreenshot` — **без прав
  администратора** (per-user);
- создаёт ярлык в меню «Пуск» и (по желанию/всегда, в зависимости от
  установщика) на рабочем столе;
- NSIS-версия предлагает галочку «Запускать автоматически при входе в
  Windows» прямо в мастере установки;
- пишет запись в «Установка и удаление программ» с корректным
  деинсталлятором.

Автозапуск и все остальные настройки (папка сохранения, горячая клавиша,
формат, качество) в любой момент можно поменять из самого приложения —
через пункт «Настройки…» в меню значка в трее.

## Особенности Windows-версии приложения

- Захват экрана — через Qt (`QScreen.grabWindow`), работает "из коробки".
- Горячая клавиша — глобальный перехват через `RegisterHotKey` (WinAPI),
  без сторонних библиотек и без прав администратора.
- Автозапуск — через `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.
- Иконка в трее — тот же дизайн, что и в Linux-версии (см. `src/assets`).

