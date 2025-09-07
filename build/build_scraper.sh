#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF
Usage: $0 <scraper_folder_name> [--arch x86_64|arm64] [--set-default]
  --arch: target architecture, default x86_64 (allowed: x86_64, arm64)
  --set-default: after build, copy artifact to build/deployment.zip used by CDK
Examples:
  ./build_scraper.sh sample_scraper --arch x86_64 --set-default
EOF
  exit 2
}

if [ "$#" -lt 1 ]; then
  usage
fi

SCRAPER="$1"
shift || true

ARCH="x86_64"
SET_DEFAULT=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --arch)
      ARCH="$2"; shift 2;;
    --set-default)
      SET_DEFAULT=1; shift;;
    *)
      echo "Unknown arg: $1"; usage;;
  esac
done

if [ "$ARCH" != "x86_64" ] && [ "$ARCH" != "arm64" ]; then
  echo "Unsupported arch: $ARCH"
  exit 3
fi

ROOT="$(cd "$(dirname "$(dirname "${BASH_SOURCE[0]}")")" && pwd)"
SCRAPER_DIR="$ROOT/scrapers/$SCRAPER"
BUILD_DIR="$SCRAPER_DIR/build"
VENDOR_DIR="$SCRAPER_DIR/_vendor_${ARCH}"

echo "Root: $ROOT"
echo "Scraper dir: $SCRAPER_DIR"
echo "Build dir: $BUILD_DIR"
echo "Vendor dir: $VENDOR_DIR"
echo "Arch: $ARCH"

if [ ! -d "$SCRAPER_DIR" ]; then
  echo "ERROR: Scraper folder not found: $SCRAPER_DIR"
  exit 3
fi

# ensure clean build directories
rm -rf "$BUILD_DIR" "$VENDOR_DIR"
mkdir -p "$BUILD_DIR"
mkdir -p "$VENDOR_DIR"

REQ_FILE="$SCRAPER_DIR/requirements.txt"
if [ -f "$REQ_FILE" ] && [ -s "$REQ_FILE" ]; then
  echo "Installing scraper dependencies into $VENDOR_DIR using pip..."
  # use pip from current python
  python3 -m pip install -r "$REQ_FILE" --target "$VENDOR_DIR"
else
  echo "No requirements.txt or it's empty; skipping dependency install."
fi

# Copy source files into build dir.
# Include: all .py files, any package directories, plus optionally others.
echo "Copying source files into build dir..."
shopt -s nullglob
# copy python files
cp -v "$SCRAPER_DIR"/*.py "$BUILD_DIR" 2>/dev/null || true
# copy utils or package dirs (if present)
if [ -d "$SCRAPER_DIR"/package ]; then
  cp -rv "$SCRAPER_DIR"/package "$BUILD_DIR" || true
fi

# copy any non-code assets you want to include (optional)
if [ -d "$SCRAPER_DIR"/assets ]; then
  cp -rv "$SCRAPER_DIR"/assets "$BUILD_DIR" || true
fi

# vendor packages: copy into build root so imports work
echo "Copying vendored packages into build dir..."
if [ -d "$VENDOR_DIR" ]; then
  # copy hidden files too
  cp -rv "$VENDOR_DIR"/* "$BUILD_DIR" 2>/dev/null || true
fi

# Ensure the build dir is non-empty before zipping
echo "Contents of build dir:"
ls -la "$BUILD_DIR" || true

ARTIFACT="$SCRAPER_DIR/build/deployment-${ARCH}.zip"
echo "Creating artifact: $ARTIFACT"
pushd "$BUILD_DIR" > /dev/null
# zip silently but show final size
zip -r9 "./deployment-${ARCH}.zip" . || { echo "zip failed"; popd > /dev/null; exit 5; }
popd > /dev/null

if [ ! -f "$ARTIFACT" ]; then
  echo "ERROR: artifact not created: $ARTIFACT"
  exit 6
fi

echo "Artifact created: $ARTIFACT ($(stat -c%s "$ARTIFACT" 2>/dev/null || stat -f%z "$ARTIFACT")) bytes"

if [ "$SET_DEFAULT" -eq 1 ]; then
  mkdir -p "$SCRAPER_DIR/dist" 
  cp -f "$ARTIFACT" "$SCRAPER_DIR/dist/deployment.zip"
  echo "Set default deployment.zip to deployment-${ARCH}.zip"
fi


rm -rf "$BUILD_DIR" "$VENDOR_DIR"

echo "Build complete for $SCRAPER (arch=$ARCH)."
