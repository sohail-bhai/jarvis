#!/bin/bash
echo "=========================================="
echo " Building JARVIS Standalone Android APK   "
echo "=========================================="

MOBILE_DIR=$(pwd)
cd "$MOBILE_DIR"

echo -e "\n1. Running Expo Prebuild..."
npx expo prebuild --platform android

echo -e "\n2. Compiling Standalone Android APK via Gradle..."
export ANDROID_HOME="$MOBILE_DIR/.android-sdk"
export JAVA_HOME="$MOBILE_DIR/.jdk"
export PATH="$JAVA_HOME/bin:$PATH"

cd "$MOBILE_DIR/android" || exit 1
chmod +x gradlew
./gradlew assembleDebug

BUILT_APK="$MOBILE_DIR/android/app/build/outputs/apk/debug/app-debug.apk"
OUTPUT_APK="$MOBILE_DIR/JARVIS.apk"

if [ -f "$BUILT_APK" ]; then
    cp "$BUILT_APK" "$OUTPUT_APK"
    echo -e "\n=========================================="
    echo -e "\033[32m SUCCESS! Standalone APK built successfully!\033[0m"
    echo -e "\033[32m APK File Path: $OUTPUT_APK\033[0m"
    echo "=========================================="
    echo -e "\nYou can copy 'JARVIS.apk' to ANY Android phone (via WhatsApp, Google Drive, USB, or Bluetooth) and install it directly."
else
    echo -e "\n\033[31m[ERROR] APK build failed or output file not found.\033[0m"
    exit 1
fi
