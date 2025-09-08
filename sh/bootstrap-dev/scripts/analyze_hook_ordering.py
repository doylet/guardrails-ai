#!/usr/bin/env python3
"""
Git Hook Ordering Strategy Analysis
Analyzes and recommends execution order strategies for modular git hooks.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class HookCategory(Enum):
    VALIDATION = "validation"    # Lint, format, syntax
    SECURITY = "security"        # ACL, secrets, permissions  
    QUALITY = "quality"          # Tests, coverage, metrics
    INTEGRATION = "integration"  # External services, notifications
    CLEANUP = "cleanup"          # Backup, housekeeping

@dataclass 
class HookDefinition:
    plugin_name: str
    script_name: str
    category: HookCategory
    priority: int  # Within category: 0 (first) to 100 (last)
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

# Current hook examples
CURRENT_HOOKS = [
    HookDefinition("acl-kit", "acl-check.sh", HookCategory.SECURITY, 50),
    HookDefinition("repo-safety", "backup.sh", HookCategory.CLEANUP, 10),
    HookDefinition("root-hygiene", "cleanup.sh", HookCategory.VALIDATION, 80),
    HookDefinition("commit-msg", "format.sh", HookCategory.VALIDATION, 10),
]

class HookOrderingStrategy:
    """Different strategies for ordering hook execution."""
    
    @staticmethod
    def alphabetical(hooks: List[HookDefinition]) -> List[Tuple[str, HookDefinition]]:
        """Current alphabetical ordering."""
        ordered = sorted(hooks, key=lambda h: f"{h.plugin_name}-{h.script_name}")
        return [(f"{h.plugin_name}-{h.script_name}.sh", h) for h in ordered]
    
    @staticmethod
    def semantic_priority(hooks: List[HookDefinition]) -> List[Tuple[str, HookDefinition]]:
        """Semantic category + priority ordering."""
        category_order = {
            HookCategory.VALIDATION: 10,
            HookCategory.SECURITY: 30, 
            HookCategory.QUALITY: 50,
            HookCategory.INTEGRATION: 70,
            HookCategory.CLEANUP: 90,
        }
        
        ordered = sorted(hooks, key=lambda h: (
            category_order[h.category],
            h.priority,
            h.plugin_name  # Tiebreaker
        ))
        
        filenames = []
        for h in ordered:
            base_priority = category_order[h.category]
            final_priority = base_priority + (h.priority // 10)
            filename = f"{final_priority:02d}-{h.plugin_name}-{h.script_name}.sh"
            filenames.append((filename, h))
            
        return filenames
    
    @staticmethod 
    def dependency_based(hooks: List[HookDefinition]) -> List[Tuple[str, HookDefinition]]:
        """Topological sort based on dependencies."""
        # Simplified - would need full dependency resolution
        ordered = sorted(hooks, key=lambda h: len(h.dependencies))
        return [(f"{h.plugin_name}-{h.script_name}.sh", h) for h in ordered]

def analyze_strategies():
    """Compare different ordering strategies."""
    print("🔍 Git Hook Ordering Strategy Analysis")
    print("=" * 60)
    
    strategies = [
        ("Alphabetical (Current)", HookOrderingStrategy.alphabetical),
        ("Semantic Priority", HookOrderingStrategy.semantic_priority),
        ("Dependency Based", HookOrderingStrategy.dependency_based),
    ]
    
    for name, strategy in strategies:
        print(f"\n📋 {name}:")
        ordered_hooks = strategy(CURRENT_HOOKS)
        for i, (filename, hook) in enumerate(ordered_hooks, 1):
            print(f"  {i}. {filename:<30} ({hook.category.value})")
    
    print(f"\n" + "=" * 60)
    print("🎯 RECOMMENDATIONS:")
    print("  1. ✅ SEMANTIC PRIORITY: Clear, predictable, extensible")
    print("  2. ⚠️  ALPHABETICAL: Simple but arbitrary") 
    print("  3. 🔄 DEPENDENCY: Complex, harder to debug")
    
    print(f"\n📖 Semantic Categories:")
    for category in HookCategory:
        print(f"  • {category.value.upper():<12}: {get_category_description(category)}")

def get_category_description(category: HookCategory) -> str:
    """Get description for hook category."""
    descriptions = {
        HookCategory.VALIDATION: "Code format, syntax, lint checks",
        HookCategory.SECURITY: "ACL, secrets, permission validation", 
        HookCategory.QUALITY: "Tests, coverage, quality gates",
        HookCategory.INTEGRATION: "External APIs, notifications",
        HookCategory.CLEANUP: "Backup, housekeeping, maintenance",
    }
    return descriptions.get(category, "Unknown category")

if __name__ == "__main__":
    analyze_strategies()
