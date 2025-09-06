#!/usr/bin/env bash
set -euo pipefail
git config core.hooksPath .githooks
chmod +x .githooks/* ai/scripts/policy/*.sh || true
echo "✓ hooksPath set and hooks exec"
