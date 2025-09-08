#!/usr/bin/env python3
"""
Documentation Validation Script
Part of the doc-guardrails-kit plugin

Validates ADR, COE, and Sprint Plan documentation for compliance.
"""

import sys
from pathlib import Path


def validate_adr(file_path: Path) -> bool:
    """Validate an ADR (Architecture Decision Record) file"""
    try:
        with open(file_path) as f:
            content = f.read()

        # Basic ADR structure validation
        required_sections = ['Title', 'Status', 'Context', 'Decision', 'Consequences']
        for section in required_sections:
            if f"## {section}" not in content and f"# {section}" not in content:
                print(f"ERROR: Missing required section '{section}' in {file_path}")
                return False

        print(f"OK: ADR {file_path} is valid")
        return True
    except Exception as e:
        print(f"ERROR: Failed to validate ADR {file_path}: {e}")
        return False


def validate_coe(file_path: Path) -> bool:
    """Validate a COE (Centers of Excellence) file"""
    try:
        with open(file_path) as f:
            content = f.read()

        # Basic COE structure validation
        required_sections = ['Overview', 'Scope', 'Responsibilities', 'Success Metrics']
        for section in required_sections:
            if f"## {section}" not in content and f"# {section}" not in content:
                print(f"ERROR: Missing required section '{section}' in {file_path}")
                return False

        print(f"OK: COE {file_path} is valid")
        return True
    except Exception as e:
        print(f"ERROR: Failed to validate COE {file_path}: {e}")
        return False


def validate_sprint_plan(file_path: Path) -> bool:
    """Validate a Sprint Plan file"""
    try:
        with open(file_path) as f:
            content = f.read()

        # Basic Sprint Plan structure validation
        required_sections = ['Sprint Overview', 'Goals', 'Deliverables', 'Timeline']
        for section in required_sections:
            if f"## {section}" not in content and f"# {section}" not in content:
                print(f"ERROR: Missing required section '{section}' in {file_path}")
                return False

        print(f"OK: Sprint Plan {file_path} is valid")
        return True
    except Exception as e:
        print(f"ERROR: Failed to validate Sprint Plan {file_path}: {e}")
        return False


def main():
    """Main validation function"""
    if len(sys.argv) < 2:
        print("Usage: validate_docs.py <directory>")
        sys.exit(1)

    target_dir = Path(sys.argv[1])
    if not target_dir.exists():
        print(f"ERROR: Directory {target_dir} does not exist")
        sys.exit(1)

    all_valid = True

    # Find and validate ADR files
    adr_files = list(target_dir.rglob("**/decisions/ADR-*.md"))
    for adr_file in adr_files:
        if not validate_adr(adr_file):
            all_valid = False

    # Find and validate COE files
    coe_files = list(target_dir.rglob("**/coe/*.md"))
    for coe_file in coe_files:
        if not validate_coe(coe_file):
            all_valid = False

    # Find and validate Sprint Plan files
    sprint_files = list(target_dir.rglob("**/sprints/*Sprint*.md"))
    for sprint_file in sprint_files:
        if not validate_sprint_plan(sprint_file):
            all_valid = False

    if all_valid:
        print("All documentation files are valid!")
        sys.exit(0)
    else:
        print("Some documentation files have validation errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()
