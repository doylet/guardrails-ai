#!/usr/bin/env python3
"""
YAML Extension Validator
Checks for consistency in YAML file extensions
"""
from pathlib import Path
import sys

def validate_yaml_extensions(root_dir: Path) -> bool:
    """Validate that all YAML files use .yaml extension"""
    yml_files = list(root_dir.rglob("*.yml"))
    yaml_files = list(root_dir.rglob("*.yaml"))

    # Filter out excluded directories
    excluded_dirs = {'.git', 'node_modules', '__pycache__'}

    yml_files = [f for f in yml_files if not any(part in excluded_dirs for part in f.parts)]
    yaml_files = [f for f in yaml_files if not any(part in excluded_dirs for part in f.parts)]

    print("🔍 YAML Extension Validation")
    print("=" * 40)
    print(f"Found {len(yaml_files)} .yaml files")
    print(f"Found {len(yml_files)} .yml files")

    if yml_files:
        print("\n❌ Inconsistent extensions found!")
        print("The following files use .yml instead of .yaml:")
        for yml_file in yml_files:
            print(f"  - {yml_file}")
        print("\nRecommendation: Rename these files to use .yaml extension")
        return False
    else:
        print("\n✅ All YAML files use consistent .yaml extension!")
        return True

def main():
    root_dir = Path.cwd()
    is_consistent = validate_yaml_extensions(root_dir)
    return 0 if is_consistent else 1

if __name__ == "__main__":
    sys.exit(main())
