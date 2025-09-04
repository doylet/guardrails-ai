#!/usr/bin/env bash
set -euo pipefail
q="${1:-pptx}"
root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
echo "== Grepping for ${q} =="
if command -v rg >/dev/null 2>&1; then
  rg -n --hidden --glob "!**/node_modules/**" --glob "!**/.venv/**" "${q}" "${root}" | head -n 200
else
  grep -RIn --exclude-dir=node_modules --exclude-dir=.venv "${q}" "${root}" | head -n 200
fi
echo "== Known capabilities =="
if [ -f "${root}/ai/capabilities.md" ]; then
  grep -n "^## " "${root}/ai/capabilities.md" | sed "s/^/  /" || true
fi
