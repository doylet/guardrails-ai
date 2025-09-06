#!/usr/bin/env python3
"""
Debug script for language exclusion issues
Run this in your other project to debug why language exclusions aren't working
"""
import yaml
from pathlib import Path

def debug_language_exclusions():
    print("🔍 Debugging Language Exclusions")
    print("=" * 50)

    # Check guardrails.yaml
    guardrails_path = Path(".ai/guardrails.yaml")
    if guardrails_path.exists():
        print("✅ Found guardrails.yaml")
        try:
            with open(guardrails_path) as f:
                guardrails = yaml.safe_load(f)

            disabled_languages = guardrails.get('precommit', {}).get('disabled_languages', [])
            print(f"📋 Disabled languages: {disabled_languages}")

            if not disabled_languages:
                print("⚠️  No disabled languages found - this could be the issue!")

        except Exception as e:
            print(f"❌ Error reading guardrails.yaml: {e}")
    else:
        print(f"❌ No guardrails.yaml found at {guardrails_path}")

    # Check pre-commit config
    precommit_path = Path(".pre-commit-config.yaml")
    if precommit_path.exists():
        print("\n✅ Found .pre-commit-config.yaml")
        try:
            with open(precommit_path) as f:
                precommit = yaml.safe_load(f)

            # Find lang-lint hook
            for repo in precommit.get('repos', []):
                if repo.get('repo') == 'local':
                    for hook in repo.get('hooks', []):
                        if hook.get('id') == 'lang-lint':
                            exclude_pattern = hook.get('exclude', 'NOT_SET')
                            print(f"🎯 Current exclude pattern: {exclude_pattern}")

                            # Check if pattern looks corrupted
                            if exclude_pattern.count('(') > 5:
                                print("❌ Pattern looks corrupted (too many parentheses)")
                            elif exclude_pattern == 'NOT_SET':
                                print("❌ No exclude pattern set")
                            else:
                                print("✅ Pattern looks reasonable")
                            break
                    break

        except Exception as e:
            print(f"❌ Error reading .pre-commit-config.yaml: {e}")
    else:
        print("❌ No .pre-commit-config.yaml found")

    print("\n💡 To fix, try running: ai-guardrails component precommit")

if __name__ == "__main__":
    debug_language_exclusions()
