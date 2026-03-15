[app]
title           = Nifty Heatmap
package.name    = niftyheatmap
package.domain  = com.nse
source.dir      = .
source.include_exts = py
version         = 1.1

# FIX: removed heavy unused packages (pandas, numpy, plyer)
# FIX: added certifi for proper SSL cert verification on Android
requirements    = python3,kivy==2.2.1,requests,urllib3,certifi,charset-normalizer,idna

orientation     = portrait
fullscreen      = 0

# FIX: added ACCESS_NETWORK_STATE for reliable connectivity detection
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# FIX: bumped api to 34 (required for Google Play + Android 14 sideload)
android.api     = 34
android.minapi  = 21
android.ndk     = 25b

android.archs   = arm64-v8a

# FIX: enable cleartext traffic fallback and disable hardware accel to prevent EGL crash
android.manifest.extra_tags = android:usesCleartextTraffic="false" android:hardwareAccelerated="false"

[buildozer]
log_level = 2
warn_on_root = 1
