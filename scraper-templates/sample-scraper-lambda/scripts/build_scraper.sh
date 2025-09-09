#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./build.sh                -> uses default ARCH x86_64
#   ./build.sh arm64         -> shorthand: set ARCH to arm64
#   ./build.sh --arch arm64  -> explicit form

ARCH="x86_64"

# parse single optional arg: either "--arch <value>" or just "<value>"
if [ "$#" -gt 0 ]; then
  if [ "$1" = "--arch" ]; then
    if [ "${2-}" = "" ]; then
      echo "usage: $0 [--arch x86_64|arm64] or $0 [x86_64|arm64]"
      exit 2
    fi
    ARCH="$2"
  else
    ARCH="$1"
  fi
fi

# validate ARCH
case "$ARCH" in
  x86_64|arm64) ;;
  *)
    echo "unsupported arch: $ARCH. supported: x86_64, arm64"
    exit 2
    ;;
esac

SCRAPER_DIR="app"
BUILD_DIR="$SCRAPER_DIR/build"
VENDOR_DIR="${SCRAPER_DIR}/_vendor_${ARCH}"

[ -d "$SCRAPER_DIR" ] || { echo "Scraper directory not found: $SCRAPER_DIR"; exit 3; }

rm -rf "$BUILD_DIR" "$VENDOR_DIR"
mkdir -p "$BUILD_DIR" "$VENDOR_DIR"

REQ_FILE="$SCRAPER_DIR/requirements.txt"
if [ -s "$REQ_FILE" ]; then
  python3 -m pip install --upgrade pip setuptools wheel
  python3 -m pip install -r "$REQ_FILE" --target "$VENDOR_DIR"
fi

# copy python files and vendored packages into build dir
cp -v "$SCRAPER_DIR"/*.py "$BUILD_DIR" 2>/dev/null || true
cp -rv "$VENDOR_DIR"/* "$BUILD_DIR" 2>/dev/null || true

ARTIFACT="$BUILD_DIR/deployment-${ARCH}.zip"
echo "Creating artifact: $ARTIFACT"
pushd "$BUILD_DIR" > /dev/null
zip -r9 "./deployment-${ARCH}.zip" . || { echo "zip failed"; popd > /dev/null; exit 5; }
popd > /dev/null

mkdir -p "cdk/dist"
cp -f "$ARTIFACT" "cdk/dist/deployment.zip"

rm -rf "$BUILD_DIR" "$VENDOR_DIR"
echo "Built: cdk/dist/deployment.zip"
