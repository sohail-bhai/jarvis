@echo off
echo ==========================================
echo  Building JARVIS Standalone Android APK
echo ==========================================

cd /d d:\jarvis\mobile
call npx expo prebuild --platform android

cd /d d:\jarvis\mobile\android
call gradlew.bat assembleDebug

if exist "app\build\outputs\apk\debug\app-debug.apk" (
    copy /y "app\build\outputs\apk\debug\app-debug.apk" "..\JARVIS.apk"
    echo.
    echo ==========================================
    echo  SUCCESS! Standalone APK built at:
    echo  d:\jarvis\mobile\JARVIS.apk
    echo ==========================================
) else (
    echo.
    echo [ERROR] APK build failed.
)
pause
