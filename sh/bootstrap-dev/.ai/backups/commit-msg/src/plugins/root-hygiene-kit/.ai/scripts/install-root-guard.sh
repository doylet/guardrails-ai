#!/usr/bin/env bash
set -euo pipefail

# Ensure hooks are versioned
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit

echo "✓ core.hooksPath set to .githooks"
echo "✓ pre-commit hook installed"
echo "You can tweak allowed root files in .guardrails/root-allowlist.txt"

echo "Optional: add root hygiene ignore snippet to your .gitignore"
echo "  cat snippets/gitignore-root-hygiene.snippet >> .gitignore"
