#!/usr/bin/env bash
set -euo pipefail
if [ -f ".githooks/_run_hook" ]; then
  echo "✓ Detected dispatcher; ACL step placed in pre-commit.d/"
else
  echo "ℹ To run ACL locally, add to your .githooks/pre-commit:"
  echo "   python ai/scripts/policy/acl_check.py --staged || true"
fi
echo "✓ ACL policy at .ai/guardrails/acl.yml (edit to match your org)"
