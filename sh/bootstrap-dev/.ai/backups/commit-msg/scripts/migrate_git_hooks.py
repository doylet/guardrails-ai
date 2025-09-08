#!/usr/bin/env python3
"""
Git Hook Migration Tool
Migrates existing numbered git hooks to semantic priority system (ADR-005).

Usage:
  python scripts/migrate_git_hooks.py [--dry-run] [--plugin PLUGIN_NAME]
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# Add src packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from packages.core.hook_ordering import (
    SemanticHookOrdering, 
    HookDefinition, 
    HookCategory,
    migrate_existing_hook
)

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

def discover_existing_hooks(plugins_dir: Path) -> Dict[str, List[Path]]:
    """Discover existing git hook files in plugins."""
    hook_files = {}
    
    for plugin_path in plugins_dir.iterdir():
        if not plugin_path.is_dir():
            continue
            
        plugin_name = plugin_path.name
        githooks_dir = plugin_path / ".githooks"
        
        if not githooks_dir.exists():
            continue
            
        # Find all hook script files
        hooks = []
        for hook_type_dir in githooks_dir.iterdir():
            if hook_type_dir.is_dir() and hook_type_dir.name.endswith('.d'):
                hook_type = hook_type_dir.name[:-2]  # Remove .d suffix
                
                for hook_file in hook_type_dir.iterdir():
                    if hook_file.is_file() and hook_file.suffix == '.sh':
                        hooks.append(hook_file)
        
        if hooks:
            hook_files[plugin_name] = hooks
    
    return hook_files

def migrate_hook_file(hook_file: Path, plugin_name: str, dry_run: bool = False) -> Optional[HookDefinition]:
    """Migrate a single hook file to semantic naming."""
    old_filename = hook_file.name
    hook_type = hook_file.parent.name[:-2]  # Remove .d suffix
    
    # Parse existing hook to determine semantic category
    hook_def = migrate_existing_hook(old_filename, plugin_name, hook_type)
    if not hook_def:
        print(f"  ⚠️  Could not migrate {old_filename}")
        return None
    
    # Generate new semantic filename
    new_filename = SemanticHookOrdering.generate_hook_filename(hook_def)
    new_path = hook_file.parent / new_filename
    
    print(f"  📁 {old_filename} → {new_filename}")
    print(f"     Category: {hook_def.category.value} (priority {hook_def.priority})")
    
    if not dry_run:
        if new_path.exists():
            print(f"     ⚠️  Target file already exists: {new_filename}")
            return None
            
        try:
            hook_file.rename(new_path)
            print(f"     ✅ Migrated successfully")
        except Exception as e:
            print(f"     ❌ Migration failed: {e}")
            return None
    else:
        print(f"     🔍 Dry run - no changes made")
    
    return hook_def

def update_plugin_manifest_hooks(plugin_path: Path, migrated_hooks: List[HookDefinition], dry_run: bool = False):
    """Update plugin manifest with semantic hook definitions."""
    manifest_path = plugin_path / "plugin-manifest.yaml"
    
    if not manifest_path.exists():
        print(f"  ⚠️  No manifest found at {manifest_path}")
        return
    
    manifest = load_yaml(manifest_path)
    if not manifest:
        return
    
    # Group hooks by type (pre_commit, commit_msg, post_commit)
    hooks_by_type = {}
    for hook_def in migrated_hooks:
        # Infer hook type from directory structure
        # This is a simplified approach - you might need more logic here
        if 'pre-commit' in str(hook_def.script_name):
            hook_type = 'pre_commit'
        elif 'commit-msg' in str(hook_def.script_name):
            hook_type = 'commit_msg'
        elif 'post-commit' in str(hook_def.script_name):
            hook_type = 'post_commit'
        else:
            hook_type = 'pre_commit'  # Default
        
        if hook_type not in hooks_by_type:
            hooks_by_type[hook_type] = []
        hooks_by_type[hook_type].append(hook_def)
    
    # Add hooks section to manifest
    if 'hooks' not in manifest:
        manifest['hooks'] = {}
    
    for hook_type, hooks in hooks_by_type.items():
        if len(hooks) == 1:
            # Single hook - use simplified format
            hook_def = hooks[0]
            manifest['hooks'][hook_type] = {
                'category': hook_def.category.value,
                'priority': hook_def.priority,
                'script': SemanticHookOrdering.generate_hook_filename(hook_def),
                'description': hook_def.description or f"{hook_def.category.value} hook"
            }
        else:
            # Multiple hooks - use array format
            manifest['hooks'][hook_type] = []
            for hook_def in hooks:
                manifest['hooks'][hook_type].append({
                    'category': hook_def.category.value,
                    'priority': hook_def.priority,
                    'script': SemanticHookOrdering.generate_hook_filename(hook_def),
                    'description': hook_def.description or f"{hook_def.category.value} hook"
                })
    
    if not dry_run:
        if save_yaml(manifest_path, manifest):
            print(f"  📝 Updated manifest: {manifest_path}")
        else:
            print(f"  ❌ Failed to update manifest: {manifest_path}")
    else:
        print(f"  🔍 Dry run - manifest not updated")

def main():
    parser = argparse.ArgumentParser(description='Migrate git hooks to semantic priority system')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--plugin', help='Migrate only specified plugin')
    parser.add_argument('--plugins-dir', default='src/plugins', help='Path to plugins directory')
    
    args = parser.parse_args()
    
    plugins_dir = Path(args.plugins_dir)
    if not plugins_dir.exists():
        print(f"❌ Plugins directory not found: {plugins_dir}")
        return 1
    
    print("🔧 Git Hook Migration Tool")
    print("=" * 50)
    print(f"Migrating to ADR-005 Semantic Priority System")
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
    print()
    
    # Discover existing hooks
    existing_hooks = discover_existing_hooks(plugins_dir)
    
    if not existing_hooks:
        print("✅ No git hooks found to migrate")
        return 0
    
    total_migrated = 0
    
    for plugin_name, hook_files in existing_hooks.items():
        if args.plugin and plugin_name != args.plugin:
            continue
            
        print(f"🔍 Processing plugin: {plugin_name}")
        plugin_path = plugins_dir / plugin_name
        migrated_hooks = []
        
        for hook_file in hook_files:
            hook_def = migrate_hook_file(hook_file, plugin_name, args.dry_run)
            if hook_def:
                migrated_hooks.append(hook_def)
                total_migrated += 1
        
        if migrated_hooks:
            update_plugin_manifest_hooks(plugin_path, migrated_hooks, args.dry_run)
        
        print()
    
    print("=" * 50)
    print(f"🎯 Migration {'simulated' if args.dry_run else 'completed'}: {total_migrated} hooks processed")
    
    if args.dry_run:
        print("\nTo apply changes, run without --dry-run flag")
    else:
        print("\n📋 Next steps:")
        print("  1. Verify hook execution order with: python src/packages/core/hook_ordering.py")
        print("  2. Test hook execution in a test repository")
        print("  3. Update plugin documentation")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
