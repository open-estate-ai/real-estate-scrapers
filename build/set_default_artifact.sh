#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <scraper_name> <arch:x86_64|arm64>"
  exit 2
fi

SCRAPER="$1"
ARCH="$2"
ROOT="$(cd "$(dirname "$(dirname "${BASH_SOURCE[0]}")")" && pwd)"
SRC="$ROOT/scrapers/$SCRAPER/build/deployment-${ARCH}.zip"
DST="$ROOT/scrapers/$SCRAPER/build/deployment.zip"

if [ ! -f "$SRC" ]; then
  echo "Artifact not found: $SRC"
  exit 3
fi

cp -f "$SRC" "$DST"
echo "Set $DST -> $SRC"
