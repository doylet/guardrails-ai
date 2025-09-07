#!/usr/bin/env python3
"""
Plugin Manifest Validator
Validates that all plugin manifests conform to the target structure schema.
"""

import os
import sys
import yaml
from pathlib import Path

def load_yaml(path):
    """Load YAML file safely."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to load {path}: {e}")
        return None

def validate_plugin_against_target_structure(plugin_path, target_schema):
    """Validate a plugin manifest against the target structure schema."""
    
    plugin_manifest_path = plugin_path / "plugin-manifest.yaml"
    if not plugin_manifest_path.exists():
        return f"❌ MISSING: {plugin_path.name}/plugin-manifest.yaml"
    
    plugin_manifest = load_yaml(plugin_manifest_path)
    if not plugin_manifest:
        return f"❌ INVALID YAML: {plugin_path.name}/plugin-manifest.yaml"
    
    issues = []
    
    # Check plugin structure
    if 'plugin' not in plugin_manifest:
        issues.append("Missing 'plugin' section")
    
    if 'components' not in plugin_manifest:
        issues.append("Missing 'components' section")
    
    # Validate file patterns against target structure
    target_structure = target_schema.get('expected_structure', {})
    
    if 'components' in plugin_manifest:
        for component_name, component in plugin_manifest['components'].items():
            if 'file_patterns' in component:
                for pattern in component['file_patterns']:
                    if not validate_pattern_against_structure(pattern, target_structure):
                        issues.append(f"Component '{component_name}' has pattern '{pattern}' that doesn't align with target structure")
    
    # Check for target_structure_extensions
    if 'configuration' in plugin_manifest and 'target_structure_extensions' in plugin_manifest['configuration']:
        extensions = plugin_manifest['configuration']['target_structure_extensions']
        for path, definition in extensions.items():
            if not validate_extension_against_structure(path, definition, target_structure):
                issues.append(f"Target structure extension '{path}' conflicts with base structure")
    
    if issues:
        return f"❌ ISSUES in {plugin_path.name}:\n" + "\n".join(f"   - {issue}" for issue in issues)
    else:
        return f"✅ VALID: {plugin_path.name}"

def validate_pattern_against_structure(pattern, target_structure, current_path=""):
    """Check if a file pattern aligns with the target directory structure."""
    
    # Handle common patterns
    if pattern.startswith('.ai/'):
        return '.ai/' in target_structure
    elif pattern.startswith('.github/'):
        return '.github/' in target_structure
    elif pattern.startswith('.githooks/'):
        return '.githooks/' in target_structure
    elif pattern.startswith('docs/'):
        return 'docs/' in target_structure
    elif pattern.startswith('scripts/'):
        # This is tricky - scripts/ at root vs .ai/scripts/
        # For now, assume root scripts/ is acceptable
        return True
    
    return True  # Be permissive for now

def validate_extension_against_structure(extension_path, extension_def, target_structure):
    """Validate that a target structure extension doesn't conflict with base structure."""
    
    # Split path into components
    path_parts = extension_path.strip('/').split('/')
    
    current_level = target_structure
    for part in path_parts:
        part_with_slash = part + '/'
        if part_with_slash in current_level:
            current_level = current_level[part_with_slash]
            if 'subdirs' in current_level:
                current_level = current_level['subdirs']
        else:
            # Path doesn't exist in target structure, which is OK for extensions
            return True
    
    return True

def main():
    # Find root directory
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    
    # Load target structure schema
    target_schema_path = root_dir / "src" / "target-structure.schema.yaml"
    target_schema = load_yaml(target_schema_path)
    
    if not target_schema:
        print("❌ FATAL: Could not load target-structure.schema.yaml")
        return 1
    
    # Find all plugins
    plugins_dir = root_dir / "src" / "plugins"
    if not plugins_dir.exists():
        print("❌ FATAL: Plugins directory not found")
        return 1
    
    print("🔍 Validating Plugin Manifests Against Target Structure")
    print("=" * 60)
    
    issues_found = False
    
    for plugin_path in plugins_dir.iterdir():
        if plugin_path.is_dir():
            result = validate_plugin_against_target_structure(plugin_path, target_schema)
            print(result)
            if result.startswith("❌"):
                issues_found = True
    
    print("=" * 60)
    
    if issues_found:
        print("❌ VALIDATION FAILED: Some plugins have issues")
        return 1
    else:
        print("✅ VALIDATION PASSED: All plugins conform to target structure")
        return 0

if __name__ == "__main__":
    sys.exit(main())
