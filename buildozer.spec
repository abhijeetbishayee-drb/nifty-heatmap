[app]
title           = Nifty Heatmap
package.name    = niftyheatmap
package.domain  = com.nse
source.dir      = .
source.include_exts = py
version         = 1.0
requirements    = python3,kivy==2.2.1,yfinance==0.2.38,pytz,pandas,numpy,plyer,requests,urllib3,multitasking,frozendict,beautifulsoup4
orientation     = portrait
fullscreen      = 0
android.permissions = INTERNET
android.api     = 33
android.minapi  = 21
android.ndk     = 25b
android.ndk_path = /home/runner/.buildozer/android/platform/android-ndk-r25b
android.sdk_path = /home/runner/.buildozer/android/platform/android-sdk
android.archs   = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
