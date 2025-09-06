#!/usr/bin/env bash
# Sweep stray working files in repo root into .work/ (dry-run by default).
set -euo pipefail
repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

DRY_RUN="${DRY_RUN:-1}"
dest="${WORK_DIR:-.work}"
mkdir -p "$dest"

# Patterns considered "working files" at root
patterns=(
  "*.tmp" "*.temp" "*.bak" "*~"
  "*.log" "log.txt"
  "draft*.md" "notes*.md" "scratch*.md" "report*.md"
  "*.swp" "*.swo"
)

moved=0
for pat in "${patterns[@]}"; do
  for f in $pat; do
    [ -e "$f" ] || continue
    # only root-level files
    [[ "$f" == */* ]] && continue
    if [ "$DRY_RUN" = "1" ]; then
      echo "Would move: $f -> $dest/$f"
    else
      echo "Moving: $f -> $dest/$f"
      mv -n -- "$f" "$dest/$f"
      moved=$((moved+1))
    fi
  done
done

if [ "$DRY_RUN" = "1" ]; then
  echo "Dry-run complete. Set DRY_RUN=0 to apply."
else
  echo "Moved $moved file(s) to $dest"
fi
