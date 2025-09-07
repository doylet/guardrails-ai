#!/usr/bin/env python3
"""
Git Hook Semantic Ordering System
Implements ADR-005: Git Hook Execution Ordering Strategy

Provides semantic categories for git hooks and automatic filename generation
to eliminate plugin coordination requirements.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import re

class HookCategory(Enum):
    """Semantic categories for git hooks with base priority ranges."""
    VALIDATION = "validation"    # 10-19: format, lint, syntax
    SECURITY = "security"        # 30-39: ACL, secrets, permissions  
    QUALITY = "quality"          # 50-59: tests, coverage, metrics
    INTEGRATION = "integration"  # 70-79: external APIs, notifications
    CLEANUP = "cleanup"          # 90-99: backup, housekeeping

@dataclass
class HookDefinition:
    """Definition of a git hook from a plugin manifest."""
    plugin_name: str
    script_name: str
    category: HookCategory
    priority: int  # 0-100 within category
    description: Optional[str] = None
    
    def __post_init__(self):
        if not (0 <= self.priority <= 100):
            raise ValueError(f"Priority must be 0-100, got {self.priority}")

class SemanticHookOrdering:
    """Implements semantic priority system for git hook execution ordering."""
    
    # Base priorities for each category (tens digit)
    CATEGORY_BASE_PRIORITIES = {
        HookCategory.VALIDATION: 10,
        HookCategory.SECURITY: 30,
        HookCategory.QUALITY: 50,
        HookCategory.INTEGRATION: 70,
        HookCategory.CLEANUP: 90,
    }
    
    @classmethod
    def generate_hook_filename(cls, hook_def: HookDefinition) -> str:
        """
        Generate semantic filename for a hook.
        
        Format: {base_priority + (priority/10):02d}-{plugin-name}-{script}.sh
        
        Examples:
        - ACL plugin (security, priority 50) → 35-acl-kit-check.sh
        - Repo safety (cleanup, priority 10) → 91-repo-safety-backup.sh
        - Lint checks (validation, priority 20) → 12-lint-kit-check.sh
        """
        base_priority = cls.CATEGORY_BASE_PRIORITIES[hook_def.category]
        final_priority = base_priority + (hook_def.priority // 10)
        
        # Clean plugin name and script name for filename
        plugin_clean = cls._clean_name(hook_def.plugin_name)
        script_clean = cls._clean_script_name(hook_def.script_name)
        
        return f"{final_priority:02d}-{plugin_clean}-{script_clean}.sh"
    
    @classmethod
    def _clean_name(cls, name: str) -> str:
        """Clean plugin name for use in filename."""
        # Remove common suffixes and normalize
        cleaned = name.replace('-kit', '').replace('-plugin', '')
        cleaned = re.sub(r'[^a-zA-Z0-9-]', '-', cleaned)
        cleaned = re.sub(r'-+', '-', cleaned).strip('-')
        return cleaned.lower()
    
    @classmethod
    def _clean_script_name(cls, script_name: str) -> str:
        """Clean script name for use in filename."""
        # Remove .sh extension if present
        cleaned = script_name.replace('.sh', '')
        cleaned = re.sub(r'[^a-zA-Z0-9-]', '-', cleaned)
        cleaned = re.sub(r'-+', '-', cleaned).strip('-')
        return cleaned.lower()
    
    @classmethod
    def parse_hook_manifest(cls, plugin_name: str, hook_config: Dict) -> HookDefinition:
        """
        Parse hook configuration from plugin manifest.
        
        Expected format:
        hooks:
          pre_commit:
            category: "security"
            priority: 50
            script: "acl-check.sh"
            description: "Access control validation"
        """
        category_str = hook_config.get('category', 'quality')
        priority = hook_config.get('priority', 50)
        script = hook_config.get('script', 'hook.sh')
        description = hook_config.get('description')
        
        # Convert category string to enum
        try:
            category = HookCategory(category_str.lower())
        except ValueError:
            # Default to quality if unknown category
            category = HookCategory.QUALITY
        
        return HookDefinition(
            plugin_name=plugin_name,
            script_name=script,
            category=category,
            priority=priority,
            description=description
        )
    
    @classmethod
    def order_hooks(cls, hook_definitions: List[HookDefinition]) -> List[Tuple[str, HookDefinition]]:
        """
        Order hooks by semantic priority and generate filenames.
        
        Returns list of (filename, hook_definition) tuples in execution order.
        """
        # Sort by category base priority, then by priority within category, then by plugin name
        def sort_key(hook_def: HookDefinition) -> Tuple[int, int, str]:
            base_priority = cls.CATEGORY_BASE_PRIORITIES[hook_def.category]
            return (base_priority, hook_def.priority, hook_def.plugin_name)
        
        ordered_hooks = sorted(hook_definitions, key=sort_key)
        
        return [(cls.generate_hook_filename(hook_def), hook_def) for hook_def in ordered_hooks]
    
    @classmethod
    def get_category_description(cls, category: HookCategory) -> str:
        """Get human-readable description of hook category."""
        descriptions = {
            HookCategory.VALIDATION: "Code format, syntax, lint checks",
            HookCategory.SECURITY: "ACL, secrets, permission validation",
            HookCategory.QUALITY: "Tests, coverage, quality gates", 
            HookCategory.INTEGRATION: "External APIs, notifications",
            HookCategory.CLEANUP: "Backup, housekeeping, maintenance",
        }
        return descriptions.get(category, "Unknown category")
    
    @classmethod
    def get_category_range(cls, category: HookCategory) -> str:
        """Get priority range description for category."""
        base = cls.CATEGORY_BASE_PRIORITIES[category]
        return f"{base}-{base+9}"

def migrate_existing_hook(old_filename: str, plugin_name: str, hook_type: str) -> Optional[HookDefinition]:
    """
    Migrate existing numbered hook to semantic system.
    
    Maps common patterns to appropriate categories and cleans filenames.
    """
    import re
    
    # Extract old priority number
    priority_match = re.match(r'(\d+)', old_filename)
    old_priority = int(priority_match.group(1)) if priority_match else 50
    
    # Clean script name - remove number prefix and normalize
    script_name = re.sub(r'^\d+-', '', old_filename)  # Remove leading numbers
    script_name = script_name.replace('.sh', '')      # Remove extension
    
    # Remove redundant plugin name from script if present
    plugin_base = plugin_name.replace('-kit', '').replace('_', '-')
    if script_name.startswith(plugin_base) or script_name.endswith(plugin_base):
        # Remove the plugin name part but keep descriptive part
        if script_name == plugin_base:
            # If it's just the plugin name, use a generic name based on category
            script_name = "main"
        else:
            # Remove plugin name prefix/suffix
            script_name = re.sub(f'^{re.escape(plugin_base)}-?', '', script_name)
            script_name = re.sub(f'-?{re.escape(plugin_base)}$', '', script_name)
            if not script_name:  # If nothing left, use generic name
                script_name = "main"
    
    # Infer category from filename and plugin name
    filename_lower = old_filename.lower()
    plugin_lower = plugin_name.lower()
    
    if any(keyword in filename_lower or keyword in plugin_lower 
           for keyword in ['acl', 'security', 'permission', 'secret']):
        category = HookCategory.SECURITY
        priority = 50
    elif any(keyword in filename_lower or keyword in plugin_lower
             for keyword in ['lint', 'format', 'validate', 'syntax', 'style']):
        category = HookCategory.VALIDATION
        priority = 20
    elif any(keyword in filename_lower or keyword in plugin_lower
             for keyword in ['test', 'coverage', 'quality', 'metric']):
        category = HookCategory.QUALITY  
        priority = 50
    elif any(keyword in filename_lower or keyword in plugin_lower
             for keyword in ['backup', 'safety', 'cleanup', 'mirror', 'hygiene']):
        category = HookCategory.CLEANUP
        priority = 10
        # For safety/hygiene plugins, use more descriptive name
        if 'safety' in plugin_lower:
            script_name = "backup"
        elif 'hygiene' in plugin_lower:
            script_name = "cleanup"
    elif any(keyword in filename_lower or keyword in plugin_lower
             for keyword in ['notify', 'integration', 'api', 'webhook']):
        category = HookCategory.INTEGRATION
        priority = 50
    elif 'commit-msg' in filename_lower or 'msg' in filename_lower:
        category = HookCategory.VALIDATION
        priority = 10
        script_name = "msg-validation"
    else:
        # Default to quality category
        category = HookCategory.QUALITY
        priority = 50
    
    return HookDefinition(
        plugin_name=plugin_name,
        script_name=script_name,
        category=category,
        priority=priority,
        description=f"Migrated from {old_filename}"
    )

if __name__ == "__main__":
    # Example usage and testing
    print("🔧 Git Hook Semantic Ordering System")
    print("=" * 50)
    
    # Example hook definitions
    hooks = [
        HookDefinition("acl-kit", "check.sh", HookCategory.SECURITY, 50, "ACL validation"),
        HookDefinition("repo-safety-kit", "backup.sh", HookCategory.CLEANUP, 10, "Repository backup"),
        HookDefinition("lint-kit", "format.sh", HookCategory.VALIDATION, 20, "Code formatting"),
        HookDefinition("test-kit", "coverage.sh", HookCategory.QUALITY, 60, "Coverage check"),
    ]
    
    # Generate ordered filenames
    ordered = SemanticHookOrdering.order_hooks(hooks)
    
    print("\n📋 Generated Hook Execution Order:")
    for i, (filename, hook_def) in enumerate(ordered, 1):
        print(f"  {i}. {filename:<30} ({hook_def.category.value}: {hook_def.description})")
    
    print(f"\n📖 Category Ranges:")
    for category in HookCategory:
        range_desc = SemanticHookOrdering.get_category_range(category)
        cat_desc = SemanticHookOrdering.get_category_description(category)
        print(f"  {category.value.upper():<12} ({range_desc}): {cat_desc}")
