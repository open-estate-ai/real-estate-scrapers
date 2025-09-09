#!/usr/bin/env bash
set -euo pipefail

ENV="${1:-dev}"
PARAM_FILE="cdk/envs/${ENV}.params.json"
OUT_DIR="cdk/output/${ENV}"

if [ ! -f "$PARAM_FILE" ]; then
  echo "Param file not found: $PARAM_FILE"
  exit 1
fi

if [ ! -f "cdk/.cdk-venv/bin/activate" ]; then
  echo "CDK venv not found, run: make cdk-env"
  exit 1
fi

# Build --parameters flags from JSON
PARAMS=()
while IFS= read -r line; do
  PARAMS+=("$line")
done < <(jq -r '
  to_entries[] |
  if .value|type=="string"
    then "--parameters \(.key)=\(.value)"
    else "--parameters \(.key)=\(.value|@json)"
  end
' "$PARAM_FILE")

mkdir -p "$OUT_DIR"

echo "Running: cdk synth for env=$ENV -> $OUT_DIR"
(
  cd cdk
  source .cdk-venv/bin/activate
  cdk synth "${PARAMS[@]}" -o "output/$ENV"
)
