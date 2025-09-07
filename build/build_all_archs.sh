#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$(dirname "${BASH_SOURCE[0]}")")" && pwd)

for d in "$ROOT"/scrapers/*/ ; do
  folder=$(basename "$d")
  echo "Building scraper $folder for x86_64"
  "$ROOT/build/build_scraper.sh" "$folder" --arch x86_64
  echo "Building scraper $folder for arm64"
  "$ROOT/build/build_scraper.sh" "$folder" --arch arm64
  "$ROOT/build/build_scraper.sh" "$folder" --arch x86_64 --set-default
done
