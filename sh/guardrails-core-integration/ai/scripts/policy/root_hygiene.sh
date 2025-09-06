#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-pre-commit}"      # pre-commit | ci
RANGE="${2:-}"
ALLOWLIST="${ALLOWLIST:-.ai/guardrails/root-allowlist.txt}"
[ -f "$ALLOWLIST" ] || ALLOWLIST=".guardrails/root-allowlist.txt"

if [[ ! -f "$ALLOWLIST" ]]; then
  echo "(!) No $ALLOWLIST; skipping root hygiene."
  exit 0
fi

declare -a ADDED
if [[ "$MODE" == "pre-commit" ]]; then
  mapfile -t ADDED < <(git diff --cached --name-only --diff-filter=A)
elif [[ "$MODE" == "ci" ]]; then
  [[ -n "$RANGE" ]] || { echo "Range required in CI mode"; exit 2; }
  mapfile -t ADDED < <(git diff --name-only --diff-filter=A "$RANGE")
else
  echo "Unknown mode: $MODE"; exit 2
fi

mapfile -t ALLOW < <(sed -E 's/#.*$//' "$ALLOWLIST" | sed '/^\s*$/d')
shopt -s nullglob dotglob extglob

failed=0
for path in "${ADDED[@]}"; do
  if [[ "$path" == */* ]]; then
    continue
  fi
  ok=0
  for pat in "${ALLOW[@]}"; do
    if [[ "$path" == $pat ]]; then ok=1; break; fi
  done
  if (( ok == 0 )); then
    echo "✖ New root file not allowed: $path"
    failed=1
  fi
done

if (( failed )); then
  echo
  echo "→ Move into a subdir (src/, docs/, scripts/, .work/) or add a pattern to $ALLOWLIST"
  exit 1
fi
echo "Root hygiene OK."
