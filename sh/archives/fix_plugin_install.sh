#!/usr/bin/env bash
set -euo pipefail
repo="${1:-.}"

if [ -d "$repo/src/plugins" ] && [ ! -d "$repo/src/packages/plugins" ]; then
  mkdir -p "$repo/src/packages"
  git mv "$repo/src/plugins" "$repo/src/packages/plugins" || mv "$repo/src/plugins" "$repo/src/packages/plugins"
  echo "Moved src/plugins -> src/packages/plugins"
fi

if [ ! -f "$repo/src/packages/plugins/__init__.py" ]; then
  mkdir -p "$repo/src/packages/plugins"
  echo '# plugin data package' > "$repo/src/packages/plugins/__init__.py"
  echo "Created src/packages/plugins/__init__.py"
fi

echo "Apply the pyproject.toml patch:"
echo "  git apply fix_plugin_install.patch || patch -p0 < fix_plugin_install.patch"
