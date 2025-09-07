#!/usr/bin/env bash
[ "${DISABLE_AUTO_BUNDLE:-0}" = "1" ] && exit 0
scripts/backup-bundle.sh >/dev/null 2>&1 || true
if git remote get-url mirror >/dev/null 2>&1; then
  git push mirror --all >/dev/null 2>&1 || true
  git push mirror --tags >/dev/null 2>&1 || true
fi
