#!/usr/bin/env python3
"""
Enhanced Plugin Discovery System
Integrates schema composition with plugin discovery and dependency resolution.

Part of Sprint 007: Plugin Schema Decoupling
Task 2.2: Composer integration with plugin discovery
"""

import yaml
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any

from ..utils import Colors


class PluginDependencyResolver:
    """Resolves plugin dependencies based on structure requirements."""
    
    def __init__(self, plugins: Dict[str, Dict]):
        self.plugins = plugins
        self.plugin_structures = self._load_plugin_structures()
    
    def _load_plugin_structures(self) -> Dict[str, Dict]:
        """Load structure schemas for all plugins."""
        structures = {}
        
        for plugin_name, plugin_data in self.plugins.items():
            plugin_dir = plugin_data['path']
            structure_file = plugin_dir / "plugin-structure.schema.yaml"
            
            if structure_file.exists():
                try:
                    with open(structure_file, 'r') as f:
                        structure = yaml.safe_load(f)
                        structures[plugin_name] = structure
                except Exception as e:
                    print(f"{Colors.warn('[WARN]')} Failed to load structure for {plugin_name}: {e}")
        
        return structures
    
    def get_plugin_dependencies(self, plugin_name: str) -> List[str]:
        """Get dependencies for a specific plugin."""
        if plugin_name not in self.plugin_structures:
            return []
        
        structure = self.plugin_structures[plugin_name]
        
        # Get explicit dependencies
        explicit_deps = structure.get('dependencies', [])
        
        # Get structure-based dependencies
        structure_deps = self._resolve_structure_dependencies(plugin_name)
        
        # Combine and deduplicate
        all_deps = list(set(explicit_deps + structure_deps))
        return all_deps
    
    def _resolve_structure_dependencies(self, plugin_name: str) -> List[str]:
        """Resolve dependencies based on structure requirements."""
        if plugin_name not in self.plugin_structures:
            return []
        
        structure = self.plugin_structures[plugin_name]
        requires = structure.get('requires_structure', [])
        dependencies = []
        
        for required_path in requires:
            # Find plugins that provide this structure
            providers = self._find_structure_providers(required_path)
            dependencies.extend(providers)
        
        return dependencies
    
    def _find_structure_providers(self, required_path: str) -> List[str]:
        """Find plugins that provide a specific structure path."""
        providers = []
        
        for plugin_name, structure in self.plugin_structures.items():
            provides = structure.get('provides_structure', {})
            
            # Check if plugin provides this path or a parent path
            if self._path_matches_provides(required_path, provides):
                providers.append(plugin_name)
        
        return providers
    
    def _path_matches_provides(self, required_path: str, provides: Dict) -> bool:
        """Check if a required path matches what a plugin provides."""
        # Normalize paths
        required_norm = required_path.rstrip('/')
        
        for provided_path in provides.keys():
            provided_norm = provided_path.rstrip('/')
            
            # Exact match or required is under provided directory
            if required_norm == provided_norm:
                return True
            if required_norm.startswith(provided_norm + '/'):
                return True
            if provided_path.endswith('/') and required_norm.startswith(provided_norm):
                return True
        
        return False
    
    def resolve_dependency_order(self, requested_plugins: List[str]) -> List[str]:
        """Resolve dependency order for a list of plugins."""
        resolved = []
        visiting = set()
        visited = set()
        
        def visit(plugin_name: str):
            if plugin_name in visiting:
                # Circular dependency detected
                print(f"{Colors.warn('[WARN]')} Circular dependency detected involving {plugin_name}")
                return
            
            if plugin_name in visited:
                return
            
            visiting.add(plugin_name)
            
            # Visit dependencies first
            deps = self.get_plugin_dependencies(plugin_name)
            for dep in deps:
                if dep in self.plugins:  # Only process known plugins
                    visit(dep)
            
            visiting.remove(plugin_name)
            visited.add(plugin_name)
            
            if plugin_name not in resolved:
                resolved.append(plugin_name)
        
        # Process all requested plugins
        for plugin_name in requested_plugins:
            if plugin_name in self.plugins:
                visit(plugin_name)
        
        return resolved
    
    def detect_conflicts(self, plugins: List[str]) -> List[Dict[str, Any]]:
        """Detect conflicts between plugins."""
        conflicts = []
        
        for i, plugin1 in enumerate(plugins):
            for plugin2 in plugins[i+1:]:
                conflict = self._check_plugin_conflict(plugin1, plugin2)
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts
    
    def _check_plugin_conflict(self, plugin1: str, plugin2: str) -> Optional[Dict[str, Any]]:
        """Check if two plugins conflict."""
        if plugin1 not in self.plugin_structures or plugin2 not in self.plugin_structures:
            return None
        
        structure1 = self.plugin_structures[plugin1]
        structure2 = self.plugin_structures[plugin2]
        
        # Check explicit conflicts
        conflicts1 = structure1.get('conflicts_with', [])
        conflicts2 = structure2.get('conflicts_with', [])
        
        if plugin2 in conflicts1 or plugin1 in conflicts2:
            return {
                'type': 'explicit_conflict',
                'plugin1': plugin1,
                'plugin2': plugin2,
                'reason': 'Explicitly declared conflict'
            }
        
        # Check structure conflicts (overlapping provides)
        provides1 = set(structure1.get('provides_structure', {}).keys())
        provides2 = set(structure2.get('provides_structure', {}).keys())
        
        overlapping = provides1.intersection(provides2)
        if overlapping:
            return {
                'type': 'structure_conflict',
                'plugin1': plugin1,
                'plugin2': plugin2,
                'reason': f'Both provide: {", ".join(overlapping)}',
                'overlapping_paths': list(overlapping)
            }
        
        return None
    
    def get_plugin_structure_summary(self, plugin_name: str) -> Dict[str, Any]:
        """Get summary of plugin's structure requirements and provisions."""
        if plugin_name not in self.plugin_structures:
            return {}
        
        structure = self.plugin_structures[plugin_name]
        
        return {
            'plugin_name': plugin_name,
            'provides': list(structure.get('provides_structure', {}).keys()),
            'requires': structure.get('requires_structure', []),
            'conflicts_with': structure.get('conflicts_with', []),
            'dependencies': self.get_plugin_dependencies(plugin_name)
        }


class EnhancedPluginDiscovery:
    """Enhanced plugin discovery with schema composition integration."""
    
    def __init__(self, plugins_dir: Path, target_dir: Path):
        self.plugins_dir = plugins_dir
        self.target_dir = target_dir
        self.plugins = {}
        self.dependency_resolver = None
        
        # Configuration for plugin enablement
        self.config_file = target_dir / ".ai" / "plugin_config.yaml"
        self.enabled_plugins = self._load_plugin_config()
        
        # Discover plugins
        self.plugins = self._discover_plugins()
        
        # Initialize dependency resolver
        self.dependency_resolver = PluginDependencyResolver(self.plugins)
    
    def _discover_plugins(self) -> Dict[str, Dict]:
        """Discover all available plugins."""
        plugins = {}
        
        if not self.plugins_dir.exists():
            return plugins
        
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir():
                manifest_file = plugin_dir / "plugin-manifest.yaml"
                structure_file = plugin_dir / "plugin-structure.schema.yaml"
                
                if manifest_file.exists():
                    try:
                        with open(manifest_file, 'r') as f:
                            manifest = yaml.safe_load(f)
                        
                        plugin_name = manifest.get('name', plugin_dir.name)
                        
                        # Check if structure schema exists
                        has_structure_schema = structure_file.exists()
                        
                        plugins[plugin_name] = {
                            'path': plugin_dir,
                            'manifest': manifest,
                            'has_structure_schema': has_structure_schema,
                            'enabled': plugin_name in self.enabled_plugins
                        }
                        
                    except Exception as e:
                        print(f"{Colors.warn('[WARN]')} Failed to load plugin {plugin_dir.name}: {e}")
        
        return plugins
    
    def _load_plugin_config(self) -> Set[str]:
        """Load plugin enablement configuration."""
        if not self.config_file.exists():
            # Default: enable all plugins
            return set()  # Empty means all enabled
        
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
                return set(config.get('enabled_plugins', []))
        except Exception as e:
            print(f"{Colors.warn('[WARN]')} Failed to load plugin config: {e}")
            return set()
    
    def save_plugin_config(self):
        """Save current plugin configuration."""
        config = {
            'enabled_plugins': list(self.enabled_plugins)
        }
        
        # Ensure directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
        except Exception as e:
            print(f"{Colors.error('[ERROR]')} Failed to save plugin config: {e}")
    
    def get_enabled_plugins(self) -> List[str]:
        """Get list of enabled plugin names."""
        if not self.enabled_plugins:  # Empty means all enabled
            return list(self.plugins.keys())
        return [name for name in self.enabled_plugins if name in self.plugins]
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a specific plugin."""
        if plugin_name not in self.plugins:
            print(f"{Colors.error('[ERROR]')} Plugin not found: {plugin_name}")
            return False
        
        if not self.enabled_plugins:  # All currently enabled
            self.enabled_plugins = set(self.plugins.keys())
        
        self.enabled_plugins.add(plugin_name)
        self.plugins[plugin_name]['enabled'] = True
        return True
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a specific plugin."""
        if plugin_name not in self.plugins:
            print(f"{Colors.error('[ERROR]')} Plugin not found: {plugin_name}")
            return False
        
        if not self.enabled_plugins:  # All currently enabled
            self.enabled_plugins = set(self.plugins.keys())
        
        self.enabled_plugins.discard(plugin_name)
        self.plugins[plugin_name]['enabled'] = False
        return True
    
    def get_plugin_installation_order(self, requested_plugins: List[str] = None) -> List[str]:
        """Get plugins in dependency-resolved installation order."""
        if requested_plugins is None:
            requested_plugins = self.get_enabled_plugins()
        
        return self.dependency_resolver.resolve_dependency_order(requested_plugins)
    
    def validate_plugin_selection(self, plugins: List[str]) -> Dict[str, Any]:
        """Validate a selection of plugins for conflicts and missing dependencies."""
        # Resolve dependencies
        ordered_plugins = self.dependency_resolver.resolve_dependency_order(plugins)
        
        # Check for conflicts
        conflicts = self.dependency_resolver.detect_conflicts(ordered_plugins)
        
        # Check for missing dependencies
        missing_deps = []
        for plugin in plugins:
            deps = self.dependency_resolver.get_plugin_dependencies(plugin)
            for dep in deps:
                if dep not in self.plugins:
                    missing_deps.append({'plugin': plugin, 'missing_dependency': dep})
        
        return {
            'valid': len(conflicts) == 0 and len(missing_deps) == 0,
            'installation_order': ordered_plugins,
            'conflicts': conflicts,
            'missing_dependencies': missing_deps,
            'additional_plugins': [p for p in ordered_plugins if p not in plugins]
        }
    
    def get_plugin_analysis(self) -> Dict[str, Any]:
        """Get comprehensive plugin analysis."""
        enabled = self.get_enabled_plugins()
        
        return {
            'total_plugins': len(self.plugins),
            'enabled_plugins': len(enabled),
            'plugins_with_structure_schema': sum(1 for p in self.plugins.values() if p['has_structure_schema']),
            'enabled_plugin_names': enabled,
            'plugin_dependencies': {name: self.dependency_resolver.get_plugin_dependencies(name) for name in enabled},
            'structure_summaries': {name: self.dependency_resolver.get_plugin_structure_summary(name) for name in enabled}
        }
