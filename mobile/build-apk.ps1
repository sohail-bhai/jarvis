# JARVIS Standalone APK Builder Script
# This builds a 100% standalone Android APK that does NOT require Expo Go, Metro dev server, or USB debugging.

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Building JARVIS Standalone Android APK   " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$MobileDir = "d:\jarvis\mobile"
Set-Location $MobileDir

Write-Host "`n1. Running Expo Prebuild..." -ForegroundColor Yellow
npx expo prebuild --platform android

Write-Host "`n2. Compiling Standalone Android APK via Gradle..." -ForegroundColor Yellow
Set-Location "$MobileDir\android"
.\gradlew.bat assembleDebug

$BuiltApk = "$MobileDir\android\app\build\outputs\apk\debug\app-debug.apk"
$OutputApk = "$MobileDir\JARVIS.apk"

if (Test-Path $BuiltApk) {
    Copy-Item -Path $BuiltApk -Destination $OutputApk -Force
    Write-Host "`n==========================================" -ForegroundColor Green
    Write-Host " SUCCESS! Standalone APK built successfully!" -ForegroundColor Green
    Write-Host " APK File Path: $OutputApk" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "`nYou can copy 'JARVIS.apk' to ANY Android phone (via WhatsApp, Google Drive, USB, or Bluetooth) and install it directly." -ForegroundColor White
} else {
    Write-Host "`n[ERROR] APK build failed or output file not found." -ForegroundColor Red
}
