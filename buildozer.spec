[app]
title           = Nifty Heatmap
package.name    = niftyheatmap
package.domain  = com.nse
source.dir      = .
source.include_exts = py
version         = 1.3

# Keeping kivy 2.2.1 — proven to build successfully
requirements    = python3,kivy==2.2.1,requests,urllib3,certifi,charset-normalizer,idna

orientation     = portrait
fullscreen      = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE

# Targets Android 14 (API 34), minimum Android 8 (API 26)
android.api     = 34
android.minapi  = 26
android.ndk     = 25b
android.archs   = arm64-v8a

# Auto-accept SDK licenses — prevents build failure
android.accept_sdk_license = True

# Keeping proven working manifest tags from original
android.manifest.extra_tags = android:usesCleartextTraffic="false" android:hardwareAccelerated="false"

[buildozer]
log_level = 2
warn_on_root = 1
