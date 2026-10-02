# Nifty Heatmap — Android (sideload APK)

Builds the **APK** for direct installs. The Google Play build (AAB) lives in the
private `nifty-heatmap-play` repo; both are built from the shared
[`nifty-heatmap-android-shell`](https://github.com/abhijeetbishayee-drb/nifty-heatmap-android-shell)
submodule, so the two apps can't drift.

The app shows the live web boards — Nifty 50, F&O Sectors, RRG (Beta), plus the
Rollover / PCR / 44 EMA boards — from
https://abhijeetbishayee-drb.github.io/nifty-heatmap-web/. A change to the website
reaches the app without a new release.

| | |
|---|---|
| Application ID | `io.github.abhijeetbishayee.niftyheatmap.sideload` |
| Min / target SDK | 26 (Android 8) / 36 (Android 16) |
| Version | `2.0.<CI run number>` |

## Getting the APK

Every push to `main` runs **Build APK** in the Actions tab; the APK is the
`nifty-heatmap-apk` artifact.

Until signing is set up, CI produces a **debug-signed** APK. It installs fine,
but every build has a different key, so each update needs an uninstall first.
Fix that once by running, on your Mac:

```bash
./scripts/setup-signing.sh
```

It creates the signing key under `~/Documents/android-signing-keys/` (back it
up) and stores it as GitHub Actions secrets.

## History

Versions up to 1.4 were a Kivy (Python) app that re-implemented the heatmap
natively. It was retired on 2026-10-03: it had drifted from the web version
before, it could not get the Sectors/RRG boards without a second copy of them,
and its toolchain could not meet Google Play's API 36 / 16 KB page-size rules.
The Kivy code is in git history (last Kivy commit: `9dda9f0`).

## Local build

```bash
git clone --recurse-submodules https://github.com/abhijeetbishayee-drb/nifty-heatmap.git
cd nifty-heatmap && ./gradlew :app:assembleDebug     # needs JDK 17+ and the Android SDK
```
