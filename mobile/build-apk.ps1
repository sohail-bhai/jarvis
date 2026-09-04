# Builds a standalone JARVIS APK on Windows.
#
# Release, not debug. The debug variant is listed in `debuggableVariants`, so
# Gradle does not bundle the JavaScript into it and the app looks for a Metro
# dev server when it starts. The release variant embeds the bundle, so the file
# below runs on any phone with nothing else running.
#
# It is signed with the debug keystore that ships with the Android project, so
# there is nothing to generate. That is fine for sideloading and for a demo; it
# is not the key to publish to Play with.

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Building JARVIS Standalone Android APK   " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$MobileDir = $PSScriptRoot
Set-Location $MobileDir

Write-Host "`n1. Running Expo Prebuild..." -ForegroundColor Yellow
# Native modules are added in JS but need native code generated for them, so
# this has to run whenever a dependency with a native part changes.
npx expo prebuild --platform android

Write-Host "`n2. Compiling Standalone Android APK via Gradle..." -ForegroundColor Yellow
Set-Location "$MobileDir\android"
.\gradlew.bat assembleRelease

$BuiltApk = "$MobileDir\android\app\build\outputs\apk\release\app-release.apk"
$OutputApk = "$MobileDir\JARVIS.apk"

if (Test-Path $BuiltApk) {
    Copy-Item -Path $BuiltApk -Destination $OutputApk -Force
    Write-Host "`n==========================================" -ForegroundColor Green
    Write-Host " SUCCESS! Standalone APK built." -ForegroundColor Green
    Write-Host " APK: $OutputApk" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "`nCopy JARVIS.apk to any Android phone and install it. No USB" -ForegroundColor White
    Write-Host "debugging, no Expo Go, no dev server. The phone only needs to reach" -ForegroundColor White
    Write-Host "your computer's address on the same Wi-Fi." -ForegroundColor White
} else {
    Write-Host "`n[ERROR] Build finished but no APK at $BuiltApk" -ForegroundColor Red
    exit 1
}
