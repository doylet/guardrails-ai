#!/usr/bin/env python3
"""
Plugin Standardization Script
Standardizes git hooks patterns and post-install methods across all plugins.
"""

import os
import sys
import yaml
import re
from pathlib import Path
from typing import Dict, Any, List

def load_yaml(path):
    """Load YAML file safely."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to load {path}: {e}")
        return None

def save_yaml(path, data):
    """Save YAML file safely."""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return True
    except Exception as e:
        print(f"ERROR: Failed to save {path}: {e}")
        return False

def standardize_githooks_pattern(plugin_path: Path):
    """Convert old git hook patterns to new modular .d/ pattern."""
    changes = []
    
    # Check for old pattern files
    githooks_dir = plugin_path / ".githooks"
    if not githooks_dir.exists():
        return changes
        
    old_hooks = ["pre-commit", "commit-msg", "post-commit"]
    for hook_name in old_hooks:
        old_hook_file = githooks_dir / hook_name
        if old_hook_file.exists() and not old_hook_file.is_symlink():
            # This is an old-style direct hook file
            new_dir = githooks_dir / f"{hook_name}.d"
            new_dir.mkdir(exist_ok=True)
            
            # Move the hook script to .d/ directory with number prefix
            new_script = new_dir / f"10-{plugin_path.name.replace('-kit', '')}.sh"
            
            print(f"  📁 Moving {old_hook_file} → {new_script}")
            old_hook_file.rename(new_script)
            changes.append(f"Moved {hook_name} to modular pattern")
    
    return changes

def standardize_post_install_format(manifest_path: Path):
    """Standardize post-install format to simple array of strings."""
    manifest = load_yaml(manifest_path)
    if not manifest:
        return []
    
    changes = []
    
    # Handle old hooks.post_install format
    if 'hooks' in manifest and 'post_install' in manifest['hooks']:
        commands = manifest['hooks']['post_install']
        # Move to component level if there's only one component
        if 'components' in manifest and len(manifest['components']) == 1:
            component_name = list(manifest['components'].keys())[0]
            manifest['components'][component_name]['post_install'] = commands
            del manifest['hooks']['post_install']
            if not manifest['hooks']:  # Remove empty hooks section
                del manifest['hooks']
            changes.append(f"Moved hooks.post_install to component level")
    
    # Handle new post_install_actions format  
    if 'configuration' in manifest and 'post_install_actions' in manifest['configuration']:
        actions = manifest['configuration']['post_install_actions']
        # Convert to simple string commands
        commands = []
        for action in actions:
            if action.get('action') == 'run_script':
                script = action.get('script', '')
                if script:
                    commands.append(f"bash {script}")
            else:
                # Try to extract a simple command
                if 'description' in action:
                    commands.append(f"echo '{action['description']}'")
        
        # Move to component level or create post_install section
        if commands:
            if 'post_install' not in manifest:
                manifest['post_install'] = commands
                changes.append(f"Converted post_install_actions to post_install")
            
        # Remove the old format
        del manifest['configuration']['post_install_actions']
        if not manifest['configuration'] or list(manifest['configuration'].keys()) == ['target_structure_extensions']:
            # Keep target_structure_extensions but remove empty rest
            pass
    
    if changes:
        if save_yaml(manifest_path, manifest):
            print(f"  📝 Updated {manifest_path}")
        else:
            changes = []  # Failed to save
    
    return changes

def update_plugin_manifest_patterns(manifest_path: Path, plugin_path: Path):
    """Update file patterns in plugin manifest to use new modular hooks."""
    manifest = load_yaml(manifest_path)
    if not manifest:
        return []
    
    changes = []
    
    if 'components' in manifest:
        for component_name, component in manifest['components'].items():
            if 'file_patterns' in component:
                updated_patterns = []
                pattern_changed = False
                
                for pattern in component['file_patterns']:
                    # Convert old direct hook patterns to new modular patterns
                    if pattern == ".githooks/pre-commit":
                        updated_patterns.append(".githooks/pre-commit.d/*.sh")
                        pattern_changed = True
                    elif pattern == ".githooks/commit-msg":
                        updated_patterns.append(".githooks/commit-msg.d/*.sh")  
                        pattern_changed = True
                    elif pattern == ".githooks/post-commit":
                        updated_patterns.append(".githooks/post-commit.d/*.sh")
                        pattern_changed = True
                    else:
                        updated_patterns.append(pattern)
                
                if pattern_changed:
                    component['file_patterns'] = updated_patterns
                    changes.append(f"Updated {component_name} file patterns to modular hooks")
    
    if changes:
        if save_yaml(manifest_path, manifest):
            print(f"  📝 Updated patterns in {manifest_path}")
        else:
            changes = []
    
    return changes

def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    plugins_dir = root_dir / "src" / "plugins"
    
    if not plugins_dir.exists():
        print("❌ Plugins directory not found")
        return 1
    
    print("🔧 Standardizing Plugin Patterns")
    print("=" * 50)
    
    total_changes = 0
    
    for plugin_path in plugins_dir.iterdir():
        if plugin_path.is_dir():
            print(f"\n🔍 Processing {plugin_path.name}")
            
            manifest_path = plugin_path / "plugin-manifest.yaml"
            if not manifest_path.exists():
                print(f"  ⚠️  No manifest found, skipping")
                continue
            
            # Standardize git hooks file structure
            githook_changes = standardize_githooks_pattern(plugin_path)
            
            # Standardize post-install format in manifest
            post_install_changes = standardize_post_install_format(manifest_path)
            
            # Update file patterns in manifest
            pattern_changes = update_plugin_manifest_patterns(manifest_path, plugin_path)
            
            all_changes = githook_changes + post_install_changes + pattern_changes
            if all_changes:
                print(f"  ✅ Applied {len(all_changes)} changes:")
                for change in all_changes:
                    print(f"     - {change}")
                total_changes += len(all_changes)
            else:
                print(f"  ✅ Already standardized")
    
    print(f"\n" + "=" * 50)
    print(f"🎯 Standardization complete: {total_changes} total changes applied")
    
    if total_changes > 0:
        print("\n📋 Summary of Standardizations:")
        print("  • Git hooks: Direct files → Modular .d/ pattern")
        print("  • Post-install: Various formats → Simple post_install array")
        print("  • File patterns: Updated to match new hook structure")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
