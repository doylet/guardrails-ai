#!/usr/bin/env python3
"""
YAML Extension Standardization Script
Converts all .yml files to .yaml and updates references
"""
from pathlib import Path
import sys
import shutil
from typing import List, Dict

def find_yml_files(root_dir: Path) -> List[Path]:
    """Find all .yml files in the directory tree"""
    yml_files = []
    for yml_file in root_dir.rglob("*.yml"):
        # Skip node_modules and other ignored directories
        if any(part in yml_file.parts for part in ['.git', 'node_modules', '__pycache__']):
            continue
        yml_files.append(yml_file)
    return yml_files

def rename_files(yml_files: List[Path]) -> Dict[str, str]:
    """Rename .yml files to .yaml and return mapping of old->new paths"""
    renamed_mapping = {}

    for yml_file in yml_files:
        yaml_file = yml_file.with_suffix('.yaml')
        print(f"Renaming: {yml_file} -> {yaml_file}")

        # Create backup
        backup_file = yml_file.with_suffix('.yml.backup')
        shutil.copy2(yml_file, backup_file)

        # Rename
        yml_file.rename(yaml_file)

        # Store mapping for reference updates
        renamed_mapping[str(yml_file)] = str(yaml_file)

        # Remove backup after successful rename
        backup_file.unlink()

    return renamed_mapping

def find_reference_files(root_dir: Path) -> List[Path]:
    """Find files that might contain references to .yml files"""
    reference_files = []

    # File types that commonly reference other files
    patterns = ["*.py", "*.sh", "*.md", "*.yaml", "*.json", "*.txt"]

    for pattern in patterns:
        for file_path in root_dir.rglob(pattern):
            if any(part in file_path.parts for part in ['.git', 'node_modules', '__pycache__']):
                continue
            reference_files.append(file_path)

    return reference_files

def update_references(reference_files: List[Path], renamed_mapping: Dict[str, str]):
    """Update references to renamed files in other files"""
    # Create patterns to match file references
    updates_made = []

    for ref_file in reference_files:
        try:
            content = ref_file.read_text(encoding='utf-8')
            original_content = content

            # Update references based on the renamed files
            for old_path, new_path in renamed_mapping.items():
                old_name = Path(old_path).name
                new_name = Path(new_path).name

                # Pattern to match file references with .yml extension
                patterns = [
                    # Direct filename references
                    (old_name, new_name),
                    # Path references (relative)
                    (old_path.replace(str(Path.cwd()) + '/', ''), new_path.replace(str(Path.cwd()) + '/', '')),
                    # Workflow file references in .github/workflows/
                    (f"workflows/{old_name}", f"workflows/{new_name}"),
                    # Template references
                    (f"templates/.github/workflows/{old_name}", f"templates/.github/workflows/{new_name}"),
                ]

                for old_ref, new_ref in patterns:
                    if old_ref in content:
                        content = content.replace(old_ref, new_ref)
                        if content != original_content:
                            print(f"  Updated reference in {ref_file}: {old_ref} -> {new_ref}")

            # Write back if changes were made
            if content != original_content:
                ref_file.write_text(content, encoding='utf-8')
                updates_made.append(str(ref_file))

        except Exception as e:
            print(f"Warning: Could not process {ref_file}: {e}")

    return updates_made

def update_workflow_gate_script(root_dir: Path):
    """Update the workflow gate script to handle both extensions during transition"""
    script_path = root_dir / "src/infra/scripts/update_workflow_gate.py"

    if not script_path.exists():
        print(f"Warning: Workflow gate script not found at {script_path}")
        return

    print("Updating workflow gate script to prefer .yaml extension...")

    content = script_path.read_text(encoding='utf-8')

    # Update the plugin search patterns to prioritize .yaml
    old_patterns = '''    plugin_patterns = [
        "src/plugins/*/.github/workflows/*.yml",
        "src/plugins/*/.github/workflows/*.yaml",
        "src/plugins/*/templates/.github/workflows/*.yml",
        "src/plugins/*/templates/.github/workflows/*.yaml"
    ]'''

    new_patterns = '''    plugin_patterns = [
        "src/plugins/*/.github/workflows/*.yaml",
        "src/plugins/*/.github/workflows/*.yml",
        "src/plugins/*/templates/.github/workflows/*.yaml",
        "src/plugins/*/templates/.github/workflows/*.yml"
    ]'''

    if old_patterns in content:
        content = content.replace(old_patterns, new_patterns)
        script_path.write_text(content, encoding='utf-8')
        print("  Updated workflow gate script to prioritize .yaml extension")

def main():
    root_dir = Path.cwd()

    print("🔧 YAML Extension Standardization")
    print("=" * 50)

    # Step 1: Find all .yml files
    yml_files = find_yml_files(root_dir)

    if not yml_files:
        print("✅ No .yml files found - already standardized!")
        return 0

    print(f"Found {len(yml_files)} .yml files to rename:")
    for yml_file in yml_files:
        print(f"  - {yml_file}")

    # Step 2: Rename files
    print("\n📝 Renaming files...")
    renamed_mapping = rename_files(yml_files)

    # Step 3: Find and update references
    print("\n🔍 Finding and updating references...")
    reference_files = find_reference_files(root_dir)
    updated_files = update_references(reference_files, renamed_mapping)

    # Step 4: Update workflow gate script
    print("\n⚙️ Updating workflow gate script...")
    update_workflow_gate_script(root_dir)

    # Summary
    print("\n✅ Standardization Complete!")
    print(f"  - Renamed {len(renamed_mapping)} files to .yaml")
    print(f"  - Updated references in {len(updated_files)} files")

    if updated_files:
        print("\nFiles with updated references:")
        for file_path in updated_files:
            print(f"  - {file_path}")

    print("\n💡 Recommendation: Run tests to ensure everything still works correctly!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
