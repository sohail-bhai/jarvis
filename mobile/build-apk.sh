#!/bin/bash
# Builds a standalone VAVE APK.
#
# Release, not debug, and that is the whole point: the debug variant is listed
# in `debuggableVariants`, so Gradle skips bundling the JavaScript into it and
# the app looks for a Metro dev server on your laptop when it starts. That APK
# works only while your computer is serving it. The release variant embeds the
# bundle, so the file below runs on any phone with nothing else running.
#
# It is signed with the debug keystore that ships with the Android project, so
# there is nothing to generate. That is fine for sideloading and for a demo; it
# is not the key to publish to Play with.
set -euo pipefail

echo "=========================================="
echo " Building VAVE Standalone Android APK   "
echo "=========================================="

MOBILE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$MOBILE_DIR"

echo -e "\n1. Running Expo Prebuild..."
# Native modules are added in JS but need native code generated for them, so
# this has to run whenever a dependency with a native part changes.
npx expo prebuild --platform android

echo -e "\n2. Compiling Standalone Android APK via Gradle..."
export ANDROID_HOME="$MOBILE_DIR/.android-sdk"
export JAVA_HOME="$MOBILE_DIR/.jdk"
export PATH="$JAVA_HOME/bin:$PATH"

cd "$MOBILE_DIR/android"
chmod +x gradlew
./gradlew assembleRelease

BUILT_APK="$MOBILE_DIR/android/app/build/outputs/apk/release/app-release.apk"
OUTPUT_APK="$MOBILE_DIR/VAVE.apk"

if [ -f "$BUILT_APK" ]; then
    cp "$BUILT_APK" "$OUTPUT_APK"
    echo -e "\n=========================================="
    echo -e "\033[32m SUCCESS! Standalone APK built.\033[0m"
    echo -e "\033[32m APK: $OUTPUT_APK\033[0m"
    echo "=========================================="
    echo -e "\nCopy VAVE.apk to any Android phone and install it. No USB"
    echo "debugging, no Expo Go, no dev server. The phone only needs to reach"
    echo "your computer's address on the same Wi-Fi."
else
    echo -e "\n\033[31m[ERROR] Build finished but no APK at $BUILT_APK\033[0m"
    exit 1
fi
