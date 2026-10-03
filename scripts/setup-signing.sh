#!/usr/bin/env bash
# One-time setup: creates this app's signing key on your Mac and stores it as
# GitHub Actions secrets, so CI produces properly signed builds.
#
# Run it yourself from the repo root:   ./scripts/setup-signing.sh
# It asks for a password; nothing is printed, logged or committed.
#
# BACK UP the .jks file it creates (and the password) somewhere safe.
# Losing it means installed copies can't be updated - users would have to
# uninstall and reinstall.
set -euo pipefail

# macOS ships /usr/bin/keytool as a stub that only says "Unable to locate a
# Java Runtime", so "is keytool on PATH" proves nothing - check it RUNS, and
# fall back to Homebrew's JDK. Done before any password prompt.
if ! keytool -help >/dev/null 2>&1; then
  for jdk in /opt/homebrew/opt/openjdk@21 /opt/homebrew/opt/openjdk /usr/local/opt/openjdk@21 /usr/local/opt/openjdk; do
    if [ -x "$jdk/bin/keytool" ]; then export PATH="$jdk/bin:$PATH"; break; fi
  done
fi
keytool -help >/dev/null 2>&1 || { echo "No working Java found. Install it with:  brew install openjdk@21   then run this again."; exit 1; }
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
KEYDIR="$HOME/Documents/android-signing-keys"
KS="$KEYDIR/nifty-heatmap-sideload.jks"
ALIAS="nifty-heatmap-sideload"

if [ -e "$KS" ]; then
  echo "$KS already exists - not overwriting it. Delete it first only if you are sure."
  exit 1
fi
mkdir -p "$KEYDIR" && chmod 700 "$KEYDIR"

read -rsp "Choose a password for the key (6+ characters): " KS_PW; echo
read -rsp "Type it again: " KS_PW2; echo
[ "$KS_PW" = "$KS_PW2" ] || { echo "Passwords don't match."; exit 1; }
[ ${#KS_PW} -ge 6 ] || { echo "Too short."; exit 1; }
export KS_PW

keytool -genkeypair -keystore "$KS" -alias "$ALIAS" \
  -keyalg RSA -keysize 4096 -validity 10000 \
  -storepass:env KS_PW -keypass:env KS_PW \
  -dname "CN=Nifty Heatmap, O=Nifty Heatmap, C=IN"
chmod 600 "$KS"

base64 -i "$KS" | gh secret set KEYSTORE_BASE64 -R "$REPO"
printf %s "$KS_PW" | gh secret set SIGNING_STORE_PASSWORD -R "$REPO"
printf %s "$KS_PW" | gh secret set SIGNING_KEY_PASSWORD -R "$REPO"
printf %s "$ALIAS" | gh secret set SIGNING_KEY_ALIAS -R "$REPO"

echo
echo "Done. Key saved at: $KS  <- back this up."
echo "Secrets set on $REPO. Re-run the latest build in the Actions tab to get a signed APK."
