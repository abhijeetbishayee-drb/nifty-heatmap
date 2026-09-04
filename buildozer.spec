[app]
title           = Nifty Heatmap
package.name    = niftyheatmap
package.domain  = com.nse
source.dir      = .
source.include_exts = py,png
version         = 1.4
icon.filename   = %(source.dir)s/icon.png

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

# Pin python-for-android to a release that still builds CPython 3.11 for its
# hostpython/target Python. p4a's unpinned master (and even its latest tag)
# now hardcodes Python 3.14.2 in the python3 recipe, and the old Cython
# version pulled in transitively to build Kivy's C extensions crashes on
# 3.13+ (its bundled Tempita template engine does `import cgi`, which was
# removed from the stdlib in 3.13). v2024.01.21 last targeted Python 3.11.5.
p4a.branch = v2024.01.21

# Auto-accept SDK licenses — prevents build failure
android.accept_sdk_license = True

# Keeping proven working manifest tags from original
android.manifest.extra_tags = android:usesCleartextTraffic="false" android:hardwareAccelerated="false"

[buildozer]
log_level = 2
warn_on_root = 1
