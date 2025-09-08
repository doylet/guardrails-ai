Copilot ACL Kit

What's included
- .ai/guardrails/acl.yml            # policy file
- ai/scripts/policy/acl_check.py    # core checker
- .githooks/pre-commit.d/15-acl.sh  # local warn step
- .github/workflows/acl.yml         # reusable gate

Install:
  unzip ai-guardrails-acl-kit.zip -d .
  bash scripts/install-acl.sh

Use in main pipeline:
  jobs:
    gate_acl:
      uses: ./.github/workflows/acl.yml
      secrets: inherit
    other_job:
      needs: [gate_acl]
