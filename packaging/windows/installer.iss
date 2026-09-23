; Скрипт Inno Setup для Simple Screenshot.
; Сборка: iscc installer.iss   (требуется установленный Inno Setup 6, https://jrsoftware.org/isinfo.php)
; Ожидается, что PyInstaller уже собрал приложение в dist\SimpleScreenshot\
; (одноимённая папка рядом с этим .iss, на один уровень выше — см. build.bat).

#define MyAppName "Simple Screenshot"
#define MyAppVersion "1.3.0"
#define MyAppPublisher "Simple Screenshot Project"
#define MyAppExeName "SimpleScreenshot.exe"
#define MyDistDir "..\..\dist\SimpleScreenshot"

[Setup]
AppId={{B7B9B9D6-8B0E-4C7E-9B1B-7C2F1D9A0A11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\SimpleScreenshot
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\..\dist
OutputBaseFilename=SimpleScreenshot-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\..\src\assets\simple-screenshot.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
; Устанавливаем для Windows 10/11 (минимальная поддерживаемая версия сборки Windows 10)
MinVersion=10.0

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "autostart"; Description: "Запускать Simple Screenshot автоматически при входе в Windows"; GroupDescription: "Автозапуск:"; Flags: unchecked

[Files]
Source: "{#MyDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Автозапуск (опционально, ставится галочкой на странице выбора задач)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "SimpleScreenshot"; ValueData: """{app}\{#MyAppExeName}"""; Tasks: autostart; Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
