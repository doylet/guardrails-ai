#!/usr/bin/env bash
set -euo pipefail
repo_root="$(git rev-parse --show-toplevel)"
repo_name="$(basename "$repo_root")"
out="${1:-$HOME/GitBundles/$repo_name}"
mkdir -p "$out"
ts="$(date +%Y-%m-%d_%H-%M-%S)"
bundle="$out/$repo_name-$ts.bundle"
git bundle create "$bundle" --all
echo "✓ Bundle created: $bundle"
ls -1t "$out"/*.bundle 2>/dev/null | tail -n +8 | xargs -r rm -f || true
