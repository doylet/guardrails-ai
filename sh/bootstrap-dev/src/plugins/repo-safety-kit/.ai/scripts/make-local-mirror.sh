#!/usr/bin/env bash
set -euo pipefail
repo_root="$(git rev-parse --show-toplevel)"
repo_name="$(basename "$repo_root")"
dest="${1:-$HOME/GitMirrors/$repo_name.git}"
mkdir -p "$(dirname "$dest")"
if [ -d "$dest" ]; then
  echo "✓ Mirror exists at: $dest"
else
  git init --bare "$dest"
  echo "✓ Created bare mirror at: $dest"
fi
url="file://$dest"
if git remote get-url mirror >/dev/null 2>&1; then
  git remote set-url mirror "$url"
else
  git remote add mirror "$url"
fi
git push -u mirror --all
git push mirror --tags
echo "✓ Pushed all branches and tags to mirror"
