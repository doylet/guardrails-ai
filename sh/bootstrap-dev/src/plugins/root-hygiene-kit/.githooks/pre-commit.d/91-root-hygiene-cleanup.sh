#!/usr/bin/env bash
# Prevent new files being added directly to the repo root unless allowlisted.
# Reads patterns from .guardrails/root-allowlist.txt

set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
allow_file="$repo_root/.guardrails/root-allowlist.txt"

if [ ! -f "$allow_file" ]; then
  echo "(!) Missing $allow_file; skipping root check."
  exit 0
fi

mapfile -t added < <(git diff --cached --name-only --diff-filter=A)
if [ "${#added[@]}" -eq 0 ]; then
  exit 0
fi

# Read allowlist (strip comments/blank lines)
mapfile -t allow < <(sed -E 's/#.*$//' "$allow_file" | sed '/^\s*$/d')

shopt -s nullglob dotglob extglob

violations=()

for path in "${added[@]}"; do
  # Only care about files added at repository root (no slash in path)
  if [[ "$path" == */* ]]; then
    continue
  fi

  allowed=false
  for pat in "${allow[@]}"; do
    # Glob match at root: compare the filename against each pattern
    if [[ "$path" == $pat ]]; then
      allowed=true
      break
    fi
  done

  if [ "$allowed" = false ]; then
    violations+=("$path")
  fi
done

if [ "${#violations[@]}" -gt 0 ]; then
  echo "✖ Root hygiene check failed:"
  for v in "${violations[@]}"; do
    echo "  - $v (new file at repo root not in allowlist)"
  done
  echo
  echo "→ Options:"
  echo "  1) Move these files into an appropriate subdirectory (e.g., docs/, scripts/, src/, etc.)"
  echo "  2) If you really intend to keep a file at root, add a matching pattern to .guardrails/root-allowlist.txt"
  echo
  echo "Aborting commit."
  exit 1
fi

exit 0
