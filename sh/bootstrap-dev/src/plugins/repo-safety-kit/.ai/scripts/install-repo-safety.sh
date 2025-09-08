#!/usr/bin/env bash
set -euo pipefail
git config core.hooksPath .githooks
chmod +x .githooks/post-commit scripts/*.sh
echo "✓ core.hooksPath set to .githooks"
echo "✓ post-commit hook installed"
echo "→ Create a local mirror now:   scripts/make-local-mirror.sh"
echo "→ Create a backup bundle now:  scripts/backup-bundle.sh"
