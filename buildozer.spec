[app]
title           = Nifty Heatmap
package.name    = niftyheatmap
package.domain  = com.nse
source.dir      = .
source.include_exts = py
version         = 1.2

requirements    = python3,kivy==2.2.1,requests,urllib3,certifi,charset-normalizer,idna

orientation     = portrait
fullscreen      = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE

android.api     = 34
android.minapi  = 21
android.ndk     = 25b
android.archs   = arm64-v8a

android.manifest.extra_tags = android:usesCleartextTraffic="false" android:hardwareAccelerated="false"

[buildozer]
log_level = 2
warn_on_root = 1
