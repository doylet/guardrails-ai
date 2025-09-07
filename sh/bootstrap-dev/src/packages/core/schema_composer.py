"""Schema Composer for Plugin Structure Schemas.

This module implements the core schema composition system for ADR-006: 
Decouple Plugin Manifests from Target Structure Schema.

The SchemaComposer class provides functionality to:
- Load and validate plugin structure schemas
- Compose target schema from base + multiple plugin schemas  
- Detect conflicts between plugins
- Support dry-run mode for composition preview
- Handle schema versioning and compatibility
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from copy import deepcopy

from ..adapters.logging import get_logger


@dataclass
class CompositionResult:
    """Result of schema composition operation."""
    success: bool
    composed_schema: Optional[Dict[str, Any]]
    conflicts: List[str]
    warnings: List[str]
    plugin_count: int
    composition_time: float


@dataclass
class PluginConflict:
    """Represents a conflict between plugins."""
    type: str  # 'file_overlap', 'dependency_cycle', 'version_incompatible'
    plugins: List[str]
    path: Optional[str]
    message: str
    severity: str  # 'error', 'warning', 'info'


class SchemaComposer:
    """Core schema composition system for plugin independence.
    
    Implements ADR-006 plugin schema decoupling by composing a target 
    schema from base schema + enabled plugin structure schemas.
    """
    
    def __init__(self, 
                 base_schema_path: Path,
                 plugin_directory: Path,
                 cache_enabled: bool = True):
        """Initialize schema composer.
        
        Args:
            base_schema_path: Path to base target structure schema
            plugin_directory: Directory containing plugin subdirectories
            cache_enabled: Whether to cache composition results
        """
        self.base_schema_path = base_schema_path
        self.plugin_directory = plugin_directory
        self.cache_enabled = cache_enabled
        self.logger = get_logger(__name__)
        
        # Composition cache
        self._composition_cache: Dict[str, CompositionResult] = {}
        self._plugin_schema_cache: Dict[str, Dict[str, Any]] = {}
        
    def compose_target_schema(self, 
                            enabled_plugins: List[str],
                            dry_run: bool = False) -> CompositionResult:
        """Compose target schema from base + enabled plugin schemas.
        
        Args:
            enabled_plugins: List of plugin names to include
            dry_run: If True, only validate composition without caching
            
        Returns:
            CompositionResult with composed schema and any conflicts
        """
        import time
        start_time = time.time()
        
        # Generate cache key
        cache_key = f"{sorted(enabled_plugins)}:{dry_run}"
        if self.cache_enabled and cache_key in self._composition_cache:
            self.logger.debug(f"Using cached composition for {len(enabled_plugins)} plugins")
            return self._composition_cache[cache_key]
        
        try:
            # Load base schema
            base_schema = self._load_base_schema()
            self.logger.debug(f"Loaded base schema from {self.base_schema_path}")
            
            # Load and validate plugin schemas
            plugin_schemas = {}
            for plugin_name in enabled_plugins:
                schema = self.load_plugin_schema(plugin_name)
                if schema:
                    plugin_schemas[plugin_name] = schema
                else:
                    self.logger.warning(f"Failed to load schema for plugin: {plugin_name}")
            
            # Detect conflicts before composition
            conflicts = self._detect_conflicts(plugin_schemas)
            
            # If there are error-level conflicts, fail composition
            error_conflicts = [c for c in conflicts if c.severity == 'error']
            if error_conflicts:
                return CompositionResult(
                    success=False,
                    composed_schema=None,
                    conflicts=[c.message for c in error_conflicts],
                    warnings=[c.message for c in conflicts if c.severity == 'warning'],
                    plugin_count=len(enabled_plugins),
                    composition_time=time.time() - start_time
                )
            
            # Compose schemas
            composed_schema = self._merge_schemas(base_schema, plugin_schemas)
            
            # Validate final composition
            validation_result = self.validate_composition(composed_schema)
            if not validation_result:
                return CompositionResult(
                    success=False,
                    composed_schema=None,
                    conflicts=["Composed schema failed validation"],
                    warnings=[c.message for c in conflicts if c.severity == 'warning'],
                    plugin_count=len(enabled_plugins),
                    composition_time=time.time() - start_time
                )
            
            result = CompositionResult(
                success=True,
                composed_schema=composed_schema,
                conflicts=[],
                warnings=[c.message for c in conflicts if c.severity == 'warning'],
                plugin_count=len(enabled_plugins),
                composition_time=time.time() - start_time
            )
            
            # Cache result if not dry run
            if self.cache_enabled and not dry_run:
                self._composition_cache[cache_key] = result
                
            self.logger.info(f"Successfully composed schema with {len(enabled_plugins)} plugins "
                           f"in {result.composition_time:.3f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Schema composition failed: {e}")
            return CompositionResult(
                success=False,
                composed_schema=None,
                conflicts=[f"Composition error: {str(e)}"],
                warnings=[],
                plugin_count=len(enabled_plugins),
                composition_time=time.time() - start_time
            )
    
    def load_plugin_schema(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Load and validate plugin structure schema.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Loaded and validated plugin schema, or None if failed
        """
        # Check cache first
        if plugin_name in self._plugin_schema_cache:
            return self._plugin_schema_cache[plugin_name]
        
        plugin_schema_path = self.plugin_directory / plugin_name / "plugin-structure.schema.yaml"
        
        # Try YAML first, then JSON
        if not plugin_schema_path.exists():
            plugin_schema_path = plugin_schema_path.with_suffix('.json')
            
        if not plugin_schema_path.exists():
            self.logger.warning(f"No plugin structure schema found for {plugin_name}")
            return None
            
        try:
            with open(plugin_schema_path, 'r') as f:
                if plugin_schema_path.suffix == '.yaml':
                    schema = yaml.safe_load(f)
                else:
                    schema = json.load(f)
            
            # Validate plugin schema format
            if not self._validate_plugin_schema_format(schema):
                self.logger.error(f"Invalid plugin schema format: {plugin_name}")
                return None
            
            # Cache the schema
            self._plugin_schema_cache[plugin_name] = schema
            
            self.logger.debug(f"Loaded plugin schema: {plugin_name}")
            return schema
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin schema {plugin_name}: {e}")
            return None
    
    def _load_base_schema(self) -> Dict[str, Any]:
        """Load base target structure schema."""
        with open(self.base_schema_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _merge_schemas(self, 
                      base_schema: Dict[str, Any],
                      plugin_schemas: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Merge base schema with plugin schemas using deep merge algorithm.
        
        Args:
            base_schema: Base target structure schema
            plugin_schemas: Dict of plugin_name -> plugin_schema
            
        Returns:
            Merged schema with all plugin structures integrated
        """
        composed = deepcopy(base_schema)
        
        for plugin_name, plugin_schema in plugin_schemas.items():
            self.logger.debug(f"Merging plugin schema: {plugin_name}")
            
            provides_structure = plugin_schema.get('provides_structure', {})
            
            # Merge each path from plugin into composed schema
            for path, definition in provides_structure.items():
                self._merge_path_definition(composed, path, definition, plugin_name)
        
        return composed
    
    def _merge_path_definition(self, 
                              composed_schema: Dict[str, Any],
                              path: str,
                              definition: Dict[str, Any],
                              plugin_name: str) -> None:
        """Merge a single path definition into the composed schema."""
        # Navigate to the correct location in the composed schema
        # This is a simplified implementation - would need to handle
        # the full target schema structure properly
        
        expected_structure = composed_schema.setdefault('expected_structure', {})
        
        if path not in expected_structure:
            expected_structure[path] = {}
        
        # Merge the definition
        target = expected_structure[path]
        
        # Handle files within directories
        if 'files' in definition:
            target.setdefault('files', {}).update(definition['files'])
        
        # Handle other properties
        for key, value in definition.items():
            if key != 'files':
                target[key] = value
    
    def _detect_conflicts(self, plugin_schemas: Dict[str, Dict[str, Any]]) -> List[PluginConflict]:
        """Detect conflicts between plugin schemas.
        
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        # Check for file path overlaps
        conflicts.extend(self._detect_file_conflicts(plugin_schemas))
        
        # Check for dependency conflicts  
        conflicts.extend(self._detect_dependency_conflicts(plugin_schemas))
        
        # Check for explicit plugin conflicts
        conflicts.extend(self._detect_explicit_conflicts(plugin_schemas))
        
        return conflicts
    
    def _detect_file_conflicts(self, plugin_schemas: Dict[str, Dict[str, Any]]) -> List[PluginConflict]:
        """Detect file path overlaps between plugins."""
        conflicts = []
        path_owners = {}  # path -> set of plugin names
        
        for plugin_name, schema in plugin_schemas.items():
            provides = schema.get('provides_structure', {})
            
            for path in provides.keys():
                if path not in path_owners:
                    path_owners[path] = set()
                path_owners[path].add(plugin_name)
        
        # Find paths with multiple owners
        for path, owners in path_owners.items():
            if len(owners) > 1:
                conflicts.append(PluginConflict(
                    type='file_overlap',
                    plugins=list(owners),
                    path=path,
                    message=f"Path '{path}' provided by multiple plugins: {', '.join(owners)}",
                    severity='error'
                ))
        
        return conflicts
    
    def _detect_dependency_conflicts(self, plugin_schemas: Dict[str, Dict[str, Any]]) -> List[PluginConflict]:
        """Detect circular dependencies between plugins."""
        # Build dependency graph
        dependencies = {}
        for plugin_name, schema in plugin_schemas.items():
            dependencies[plugin_name] = schema.get('dependencies', [])
        
        # Check for cycles using DFS
        def has_cycle(node, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in dependencies.get(node, []):
                if neighbor in plugin_schemas:  # Only check enabled plugins
                    if neighbor not in visited:
                        if has_cycle(neighbor, visited, rec_stack):
                            return True
                    elif neighbor in rec_stack:
                        return True
            
            rec_stack.remove(node)
            return False
        
        conflicts = []
        visited = set()
        
        for plugin in dependencies:
            if plugin not in visited:
                if has_cycle(plugin, visited, set()):
                    conflicts.append(PluginConflict(
                        type='dependency_cycle',
                        plugins=[plugin],
                        path=None,
                        message=f"Circular dependency detected involving plugin: {plugin}",
                        severity='error'
                    ))
        
        return conflicts
    
    def _detect_explicit_conflicts(self, plugin_schemas: Dict[str, Dict[str, Any]]) -> List[PluginConflict]:
        """Detect explicit plugin conflicts defined in schemas."""
        conflicts = []
        
        for plugin_name, schema in plugin_schemas.items():
            conflicts_with = schema.get('conflicts_with', [])
            
            for conflict_pattern in conflicts_with:
                # Check if any enabled plugin matches the conflict pattern
                for other_plugin in plugin_schemas:
                    if other_plugin != plugin_name:
                        if self._matches_pattern(other_plugin, conflict_pattern):
                            conflicts.append(PluginConflict(
                                type='explicit_conflict',
                                plugins=[plugin_name, other_plugin],
                                path=None,
                                message=f"Plugin '{plugin_name}' conflicts with '{other_plugin}' (pattern: {conflict_pattern})",
                                severity='error'
                            ))
        
        return conflicts
    
    def _matches_pattern(self, plugin_name: str, pattern: str) -> bool:
        """Check if plugin name matches conflict pattern."""
        if '*' not in pattern:
            return plugin_name == pattern
        
        # Simple wildcard matching
        import re
        regex_pattern = pattern.replace('*', '.*')
        return bool(re.match(f'^{regex_pattern}$', plugin_name))
    
    def _validate_plugin_schema_format(self, schema: Dict[str, Any]) -> bool:
        """Validate plugin schema against format requirements."""
        required_fields = ['schema_version', 'plugin_name', 'provides_structure']
        
        for field in required_fields:
            if field not in schema:
                return False
        
        # Additional format validation could be added here
        return True
    
    def validate_composition(self, composed_schema: Dict[str, Any]) -> bool:
        """Validate the final composed schema.
        
        Args:
            composed_schema: The composed target schema
            
        Returns:
            True if validation passes, False otherwise
        """
        # Basic validation - could be enhanced with JSON Schema validation
        if not isinstance(composed_schema, dict):
            return False
        
        # Check for required top-level structure
        if 'expected_structure' not in composed_schema:
            self.logger.warning("Composed schema missing 'expected_structure'")
            return False
        
        return True
    
    def clear_cache(self) -> None:
        """Clear all cached composition results and plugin schemas."""
        self._composition_cache.clear()
        self._plugin_schema_cache.clear()
        self.logger.debug("Schema composition cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics for monitoring."""
        return {
            'composition_cache_size': len(self._composition_cache),
            'plugin_schema_cache_size': len(self._plugin_schema_cache)
        }
