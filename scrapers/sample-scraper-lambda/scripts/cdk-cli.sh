#!/usr/bin/env bash
set -euo pipefail

# usage: cdk-cli.sh [synth|deploy|destroy] [env] [extra args...]
OP="${1:-synth}"
ENV="${2:-dev}"
# shift 2 but tolerate when fewer args provided
if [ "$#" -ge 2 ]; then
  shift 2
else
  # consume whatever is present and leave $@ empty
  shift "$#"
fi

# Always initialize arrays to avoid unbound-variable with set -u
EXTRA_ARGS=()
PARAMS=()

# populate EXTRA_ARGS from remaining CLI args (if any)
if [ "$#" -gt 0 ]; then
  # copy remaining args into EXTRA_ARGS
  for a in "$@"; do EXTRA_ARGS+=("$a"); done
fi

CDK_DIR="${CDK_DIR:-cdk}"
PARAM_FILE="envs/${ENV}.params.json"
OUT_DIR="${CDK_DIR}/output/${ENV}"
VENV_ACTIVATE="${CDK_DIR}/.cdk-venv/bin/activate"
SYNTH_OUTPUT="${OUT_DIR}/scraper.template.yaml"

if [ ! -d "$CDK_DIR" ]; then
  echo "CDK dir not found: $CDK_DIR"
  exit 1
fi

if [ ! -f "$PARAM_FILE" ]; then
  echo "Param file not found: $PARAM_FILE"
  exit 1
fi

if [ ! -f "$VENV_ACTIVATE" ]; then
  echo "CDK venv not found, run: make cdk-env"
  exit 1
fi

# Build --parameters flags from JSON (strings raw; arrays/objects as compact JSON)
PARAMS=()
while IFS= read -r line; do
  PARAMS+=(--parameters "$line")
done < <(jq -r '
  to_entries[] |
  if (.value | type) == "string" then
    "\(.key)=\(.value)"
  else
    "\(.key)=\(.value | @json)"
  end
' "$PARAM_FILE")

mkdir -p "$OUT_DIR"

echo "CDK op: $OP   env: $ENV"
(
  cd "$CDK_DIR"
  # shellcheck disable=SC1090
  source ".cdk-venv/bin/activate"

  case "$OP" in
    synth)
      echo "Running: cdk synth -> output/$ENV"
      
      CMD=(cdk synth "${PARAMS[@]}")
      if [ "${#EXTRA_ARGS[@]}" -gt 0 ]; then
        CMD+=("${EXTRA_ARGS[@]}")
      fi
      "${CMD[@]}"
      ;;
    deploy)
      echo "Running: cdk deploy"

      CMD=(cdk deploy "${PARAMS[@]}")
      
      if [ "${#EXTRA_ARGS[@]}" -gt 0 ]; then
        CMD+=("${EXTRA_ARGS[@]}")
      fi
      "${CMD[@]}"
      ;;
    destroy)
      echo "Running: cdk destroy (non-interactive)"
      CMD=(cdk destroy --force)
      if [ "${#EXTRA_ARGS[@]}" -gt 0 ]; then
        CMD+=("${EXTRA_ARGS[@]}")
      fi
      echo "${CMD[@]}"
      "${CMD[@]}"
      ;;
    *)
      echo "Unknown op: $OP"
      echo "Usage: $0 [synth|deploy|destroy] [env] [extra args...]"
      exit 2
      ;;
  esac
)
