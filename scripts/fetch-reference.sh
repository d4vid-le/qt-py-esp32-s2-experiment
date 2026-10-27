#!/usr/bin/env bash
# Fetch the authoritative Adafruit reference material into reference/.
#
# Everything here is gitignored and never redistributed. The Eagle design is
# (c) Adafruit, CC BY-SA 3.0. This script only downloads it locally.
#
# Usage: scripts/fetch-reference.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REF="$ROOT/reference"
EAGLE="$REF/eagle"
ASSETS="$REF/assets"

REPO="https://github.com/adafruit/Adafruit-QT-Py-ESP32-S2-PCB.git"
COMMIT="7df4eac2c0b9a73ba966766ae6027b0a4d8a6901"

mkdir -p "$REF" "$ASSETS"

echo "==> Eagle source @ $COMMIT"
if [ ! -d "$EAGLE/.git" ]; then
  git clone "$REPO" "$EAGLE"
fi
CURRENT="$(git -C "$EAGLE" rev-parse HEAD 2>/dev/null || true)"
if [ "$CURRENT" != "$COMMIT" ]; then
  # The checkout may be file-locked read-only from a previous run.
  chmod -R u+w "$EAGLE" 2>/dev/null || true
  git -C "$EAGLE" fetch --quiet origin "$COMMIT" 2>/dev/null || true
  git -C "$EAGLE" checkout --quiet "$COMMIT"
fi
echo "    HEAD: $(git -C "$EAGLE" rev-parse HEAD)"

echo "==> Verifying checksums"
if command -v sha256sum >/dev/null 2>&1; then
  (cd "$EAGLE" && sha256sum -c "$ROOT/design/SHA256SUMS")
else
  (cd "$EAGLE" && shasum -a 256 -c "$ROOT/design/SHA256SUMS")
fi

echo "==> Reference images (Rev C)"
curl -fsSL -o "$ASSETS/revc-schematic.png" \
  "https://cdn-learn.adafruit.com/assets/assets/000/110/384/original/adafruit_products_QT_Py_rev_C_sch.png"
curl -fsSL -o "$ASSETS/revc-fabprint.png" \
  "https://cdn-learn.adafruit.com/assets/assets/000/110/385/original/adafruit_products_QT_Py_rev_C_fab_print.png"
file "$ASSETS"/*.png

echo "==> Done. Reference material is local-only and gitignored."
