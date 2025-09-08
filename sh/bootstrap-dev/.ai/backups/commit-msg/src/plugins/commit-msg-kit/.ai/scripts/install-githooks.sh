#!/usr/bin/env bash
set -euo pipefail
# Use a versioned hooks directory so hooks are shared via VCS
git config core.hooksPath .githooks
chmod +x .githooks/commit-msg
echo "✓ core.hooksPath set to .githooks"
echo "✓ commit-msg hook installed and executable"
