; NSIS-скрипт установщика Simple Screenshot.
; Компилируется НАТИВНО на Linux (без Wine) командой:
;   makensis installer.nsi
; так и на Windows точно так же, если установлен NSIS (https://nsis.sourceforge.io/).
;
; Ожидается, что PyInstaller уже собрал приложение в dist\SimpleScreenshot.exe
; (см. build-linux.sh / build.bat).

!define APP_NAME "Simple Screenshot"
!define APP_VERSION "1.3.2"
!define APP_PUBLISHER "Simple Screenshot Project"
!define APP_EXE "SimpleScreenshot.exe"
!define REG_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\SimpleScreenshot"
!define REG_RUN_KEY "Software\Microsoft\Windows\CurrentVersion\Run"

Name "${APP_NAME}"
OutFile "dist\SimpleScreenshot-Setup-${APP_VERSION}.exe"
InstallDir "$LOCALAPPDATA\SimpleScreenshot"
InstallDirRegKey HKCU "Software\SimpleScreenshot" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma

!include "MUI2.nsh"

!define MUI_ABORTWARNING
!define MUI_ICON "..\..\src\assets\simple-screenshot.ico"
!define MUI_UNICON "..\..\src\assets\simple-screenshot.ico"
; ^ пути к иконке верны относительно packaging\windows: src лежит на уровень выше

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
Page custom TasksPageCreate TasksPageLeave
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "Russian"
!insertmacro MUI_LANGUAGE "English"

; ---- Простая страница выбора задач (ярлык на рабочем столе / автозапуск) ----
Var Dialog
Var CheckboxDesktop
Var CheckboxAutostart
Var DesktopIconState
Var AutostartState

Function TasksPageCreate
    !insertmacro MUI_HEADER_TEXT "Дополнительные параметры" "Выберите нужные опции"
    nsDialogs::Create 1018
    Pop $Dialog
    ${If} $Dialog == error
        Abort
    ${EndIf}

    ${NSD_CreateCheckbox} 0 20u 100% 12u "Создать ярлык на рабочем столе"
    Pop $CheckboxDesktop
    ${NSD_SetState} $CheckboxDesktop 1

    ${NSD_CreateCheckbox} 0 40u 100% 12u "Запускать автоматически при входе в Windows"
    Pop $CheckboxAutostart
    ${NSD_SetState} $CheckboxAutostart 0

    nsDialogs::Show
FunctionEnd

Function TasksPageLeave
    ${NSD_GetState} $CheckboxDesktop $DesktopIconState
    ${NSD_GetState} $CheckboxAutostart $AutostartState
FunctionEnd

; ---- Установка ----
Section "Simple Screenshot" SecMain
    SectionIn RO
    SetOutPath "$INSTDIR"
    File "dist\SimpleScreenshot.exe"

    WriteRegStr HKCU "Software\SimpleScreenshot" "InstallDir" "$INSTDIR"

    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\Удалить ${APP_NAME}.lnk" "$INSTDIR\uninstall.exe"

    ${If} $DesktopIconState == ${BST_CHECKED}
        CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
    ${EndIf}

    ${If} $AutostartState == ${BST_CHECKED}
        WriteRegStr HKCU "${REG_RUN_KEY}" "SimpleScreenshot" '"$INSTDIR\${APP_EXE}"'
    ${EndIf}

    ; Запись в "Установка и удаление программ"
    WriteRegStr HKCU "${REG_UNINST_KEY}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKCU "${REG_UNINST_KEY}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKCU "${REG_UNINST_KEY}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKCU "${REG_UNINST_KEY}" "DisplayIcon" "$INSTDIR\${APP_EXE}"
    WriteRegStr HKCU "${REG_UNINST_KEY}" "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegDWORD HKCU "${REG_UNINST_KEY}" "NoModify" 1
    WriteRegDWORD HKCU "${REG_UNINST_KEY}" "NoRepair" 1

    WriteUninstaller "$INSTDIR\uninstall.exe"

    Exec '"$INSTDIR\${APP_EXE}"'
SectionEnd

; ---- Удаление ----
Section "Uninstall"
    RMDir /r "$INSTDIR"
    RMDir "$SMPROGRAMS\${APP_NAME}"
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\Удалить ${APP_NAME}.lnk"
    Delete "$DESKTOP\${APP_NAME}.lnk"
    DeleteRegKey HKCU "${REG_UNINST_KEY}"
    DeleteRegValue HKCU "${REG_RUN_KEY}" "SimpleScreenshot"
    DeleteRegKey HKCU "Software\SimpleScreenshot"
SectionEnd
