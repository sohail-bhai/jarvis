@echo off
REM Builds a standalone JARVIS APK on Windows.
REM
REM Release, not debug: the debug variant has no JavaScript bundled into it and
REM looks for a Metro dev server at startup. The release variant embeds the
REM bundle, so the APK runs on any phone with nothing else running. It is
REM signed with the debug keystore that ships with the Android project, which
REM is fine for sideloading but not for publishing to Play.

echo ==========================================
echo  Building JARVIS Standalone Android APK
echo ==========================================

set "MOBILE_DIR=%~dp0"
cd /d "%MOBILE_DIR%"
call npx expo prebuild --platform android
if errorlevel 1 goto :failed

cd /d "%MOBILE_DIR%android"
call gradlew.bat assembleRelease
if errorlevel 1 goto :failed

if exist "app\build\outputs\apk\release\app-release.apk" (
    copy /y "app\build\outputs\apk\release\app-release.apk" "%MOBILE_DIR%JARVIS.apk"
    echo.
    echo ==========================================
    echo  SUCCESS! Standalone APK built at:
    echo  %MOBILE_DIR%JARVIS.apk
    echo ==========================================
    echo.
    echo Copy JARVIS.apk to any Android phone and install it. No USB debugging,
    echo no Expo Go, no dev server. The phone only needs to reach your
    echo computer's address on the same Wi-Fi.
    pause
    exit /b 0
)

:failed
echo.
echo [ERROR] APK build failed.
pause
exit /b 1
