[app]
title           = Nifty Heatmap
package.name    = niftyheatmap
package.domain  = com.nse
source.dir      = .
source.include_exts = py
version         = 1.0
requirements    = python3,kivy==2.2.1,yfinance,pytz,pandas,numpy,plyer,requests,urllib3,multitasking,frozendict,beautifulsoup4,lxml
orientation     = portrait
fullscreen      = 0
android.permissions = INTERNET
android.api     = 33
android.minapi  = 21
android.ndk     = 23b
android.archs   = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
