"""Schema Composer for Plugin Structure Schemas.

This module implements the core schema composition system for ADR-006: 
Decouple Plugin Manifests from Target Structure Schema.

The SchemaComposer class provides functionality to:
- Load and validate plugin structure schemas
- Compose target schema from base + multiple plugin schemas  
- Detect conflicts between plugins
- Support dry-run mode for composition preview
- Handle schema versioning and compatibility
- Enhanced composition logic with sophisticated merge strategies
- Configurable conflict resolution policies
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass
from copy import deepcopy
from enum import Enum

from ..adapters.logging import get_logger


class MergeStrategy(Enum):
    """Merge strategies for handling conflicts during composition."""
    UNION = "union"           # Combine compatible elements, fail on conflicts
    OVERRIDE = "override"     # Later plugin wins conflicts
    STRICT = "strict"         # Fail on any conflict
    INTERACTIVE = "interactive"  # Ask user to resolve (future)


class ConflictResolutionPolicy:
    """Policy for resolving specific types of conflicts."""
    
    def __init__(self, 
                 file_strategy: MergeStrategy = MergeStrategy.UNION,
                 directory_strategy: MergeStrategy = MergeStrategy.UNION,
                 permission_strategy: MergeStrategy = MergeStrategy.OVERRIDE,
                 allow_overlapping_paths: bool = True,
                 priority_plugins: Optional[List[str]] = None):
        self.file_strategy = file_strategy
        self.directory_strategy = directory_strategy  
        self.permission_strategy = permission_strategy
        self.allow_overlapping_paths = allow_overlapping_paths
        self.priority_plugins = priority_plugins or []


@dataclass
class CompositionContext:
    """Context tracking state during composition."""
    merge_strategy: MergeStrategy
    conflict_policy: ConflictResolutionPolicy
    plugin_order: List[str]
    conflicts_encountered: List['PluginConflict']
    warnings_generated: List[str]
    merge_history: List[Tuple[str, str, str]]  # (plugin, path, action)


@dataclass
class CompositionResult:
    """Result of schema composition operation."""
    success: bool
    composed_schema: Optional[Dict[str, Any]]
    conflicts: List[str]
    warnings: List[str]
    plugin_count: int
    composition_time: float
    merge_strategy_used: Optional[MergeStrategy] = None
    composition_context: Optional[CompositionContext] = None


@dataclass
class PluginConflict:
    """Represents a conflict between plugins."""
    type: str  # 'file_overlap', 'dependency_cycle', 'version_incompatible', 'permission_conflict'
    plugins: List[str]
    path: Optional[str]
    message: str
    severity: str  # 'error', 'warning', 'info'
    resolution_suggestion: Optional[str] = None


class PathMerger:
    """Handles merging of specific path types with sophisticated conflict resolution."""
    
    def __init__(self, context: CompositionContext, interactive_resolver=None):
        self.context = context
        self.logger = get_logger(__name__)
        self.interactive_resolver = interactive_resolver
    
    def merge_path_definition(self, 
                             target: Dict[str, Any],
                             path: str,
                             definition: Dict[str, Any],
                             plugin_name: str) -> bool:
        """Merge a path definition using sophisticated strategies.
        
        Returns:
            True if merge succeeded, False if conflict couldn't be resolved
        """
        try:
            # Determine merge strategy for this path type
            path_type = self._determine_path_type(definition)
            strategy = self._get_strategy_for_path_type(path_type)
            
            # Record merge attempt
            self.context.merge_history.append((plugin_name, path, f"merge_{strategy.value}"))
            
            if path_type == "file":
                return self._merge_file_definition(target, path, definition, plugin_name, strategy)
            elif path_type == "directory":
                return self._merge_directory_definition(target, path, definition, plugin_name, strategy)
            else:
                return self._merge_generic_definition(target, path, definition, plugin_name, strategy)
                
        except Exception as e:
            self.logger.error(f"Failed to merge path {path} from {plugin_name}: {e}")
            self.context.warnings_generated.append(f"Merge failed for {path}: {e}")
            return False
    
    def _determine_path_type(self, definition: Dict[str, Any]) -> str:
        """Determine the type of path from its definition."""
        if not isinstance(definition, dict):
            # Handle non-dict definitions (like lists)
            return "generic"
        
        if 'files' in definition:
            return "directory"
        elif 'type' in definition and definition['type'] == 'file':
            return "file"
        elif 'content' in definition or 'template' in definition:
            return "file"
        else:
            return "directory"  # Default assumption
    
    def _get_strategy_for_path_type(self, path_type: str) -> MergeStrategy:
        """Get appropriate merge strategy for path type."""
        if path_type == "file":
            return self.context.conflict_policy.file_strategy
        elif path_type == "directory":
            return self.context.conflict_policy.directory_strategy
        else:
            return self.context.merge_strategy
    
    def _merge_file_definition(self, 
                              target: Dict[str, Any],
                              path: str,
                              definition: Dict[str, Any],
                              plugin_name: str,
                              strategy: MergeStrategy) -> bool:
        """Merge file definition with conflict resolution."""
        if path in target:
            # Conflict detected - apply resolution strategy
            existing = target[path]
            
            if strategy == MergeStrategy.STRICT:
                conflict = PluginConflict(
                    type='file_overlap',
                    plugins=[existing.get('_source_plugin', 'unknown'), plugin_name],
                    path=path,
                    message=f"Strict mode: File '{path}' defined by multiple plugins",
                    severity='error',
                    resolution_suggestion="Use UNION or OVERRIDE strategy"
                )
                self.context.conflicts_encountered.append(conflict)
                return False
                
            elif strategy == MergeStrategy.OVERRIDE:
                # Replace entirely, but warn about override
                target[path] = deepcopy(definition)
                target[path]['_source_plugin'] = plugin_name
                target[path]['_overrode_plugin'] = existing.get('_source_plugin', 'unknown')
                self.context.warnings_generated.append(
                    f"File '{path}' overridden by {plugin_name}"
                )
                return True
                
            elif strategy == MergeStrategy.UNION:
                # Merge compatible properties
                return self._union_merge_file(target, path, definition, plugin_name)
                
            elif strategy == MergeStrategy.INTERACTIVE:
                # Interactive conflict resolution
                if self.interactive_resolver:
                    conflict = PluginConflict(
                        type='file_overlap',
                        plugins=[existing.get('_source_plugin', 'unknown'), plugin_name],
                        path=path,
                        message=f"File '{path}' defined by multiple plugins",
                        severity='warning',
                        resolution_suggestion="User guidance required"
                    )
                    self.context.conflicts_encountered.append(conflict)
                    
                    resolution = self.interactive_resolver.resolve_conflict(
                        conflict, existing, definition
                    )
                    
                    return self._apply_conflict_resolution(
                        target, path, existing, definition, plugin_name, resolution
                    )
                else:
                    # Fallback to UNION if no interactive resolver
                    self.logger.warning(f"No interactive resolver available for {path}, using UNION")
                    return self._union_merge_file(target, path, definition, plugin_name)
                
        else:
            # No conflict - simple addition
            target[path] = deepcopy(definition)
            target[path]['_source_plugin'] = plugin_name
            return True
    
    def _merge_directory_definition(self,
                                   target: Dict[str, Any],
                                   path: str,
                                   definition: Dict[str, Any],
                                   plugin_name: str,
                                   strategy: MergeStrategy) -> bool:
        """Merge directory definition with file-level conflict resolution."""
        if path not in target:
            target[path] = {
                'type': 'directory',
                'files': {},
                '_source_plugins': [plugin_name]
            }
        else:
            # Add to existing directory's source plugins
            source_plugins = target[path].setdefault('_source_plugins', [])
            if plugin_name not in source_plugins:
                source_plugins.append(plugin_name)
        
        # Merge files within directory
        definition_files = definition.get('files', {})
        target_files = target[path].setdefault('files', {})
        
        for file_name, file_def in definition_files.items():
            file_path = f"{path.rstrip('/')}/{file_name}"
            
            if file_name in target_files:
                # File conflict within directory
                if strategy == MergeStrategy.STRICT:
                    conflict = PluginConflict(
                        type='file_overlap',
                        plugins=[target_files[file_name].get('_source_plugin', 'unknown'), plugin_name],
                        path=file_path,
                        message=f"Strict mode: File '{file_path}' defined by multiple plugins",
                        severity='error'
                    )
                    self.context.conflicts_encountered.append(conflict)
                    return False
                elif strategy == MergeStrategy.OVERRIDE:
                    target_files[file_name] = deepcopy(file_def)
                    target_files[file_name]['_source_plugin'] = plugin_name
                elif strategy == MergeStrategy.UNION:
                    if not self._union_merge_file_properties(target_files, file_name, file_def, plugin_name):
                        return False
                elif strategy == MergeStrategy.INTERACTIVE:
                    # Interactive resolution for file within directory
                    if self.interactive_resolver:
                        conflict = PluginConflict(
                            type='file_overlap',
                            plugins=[target_files[file_name].get('_source_plugin', 'unknown'), plugin_name],
                            path=file_path,
                            message=f"File '{file_path}' in directory defined by multiple plugins",
                            severity='warning',
                            resolution_suggestion="User guidance required"
                        )
                        self.context.conflicts_encountered.append(conflict)
                        
                        resolution = self.interactive_resolver.resolve_conflict(
                            conflict, target_files[file_name], file_def
                        )
                        
                        if resolution.strategy == "skip":
                            # Remove file from directory
                            if file_name in target_files:
                                del target_files[file_name]
                        elif resolution.strategy == "override":
                            if resolution.chosen_plugin == plugin_name:
                                target_files[file_name] = deepcopy(file_def)
                                target_files[file_name]['_source_plugin'] = plugin_name
                        else:
                            # Union or custom - use standard merge
                            if not self._union_merge_file_properties(target_files, file_name, file_def, plugin_name):
                                return False
                    else:
                        # Fallback to union
                        if not self._union_merge_file_properties(target_files, file_name, file_def, plugin_name):
                            return False
            else:
                target_files[file_name] = deepcopy(file_def)
                target_files[file_name]['_source_plugin'] = plugin_name
        
        # Merge directory-level properties (permissions, etc.)
        for key, value in definition.items():
            if key not in ['files', 'type']:
                if key in target[path] and target[path][key] != value:
                    if strategy == MergeStrategy.OVERRIDE:
                        target[path][key] = value
                    elif strategy == MergeStrategy.UNION:
                        # For permissions and similar, try to combine
                        target[path][key] = self._merge_property_values(target[path][key], value)
                else:
                    target[path][key] = value
        
        return True
    
    def _merge_generic_definition(self,
                                 target: Dict[str, Any],
                                 path: str,
                                 definition: Dict[str, Any],
                                 plugin_name: str,
                                 strategy: MergeStrategy) -> bool:
        """Fallback merge for generic definitions."""
        # Handle non-dict definitions
        if not isinstance(definition, dict):
            if path in target:
                if strategy == MergeStrategy.OVERRIDE:
                    target[path] = definition
                elif strategy == MergeStrategy.STRICT:
                    conflict = PluginConflict(
                        type='value_conflict',
                        plugins=['unknown', plugin_name],
                        path=path,
                        message=f"Strict mode: Non-dict value conflict for path '{path}'",
                        severity='error'
                    )
                    self.context.conflicts_encountered.append(conflict)
                    return False
                # For UNION with non-dict, keep existing unless overriding
            else:
                target[path] = definition
            return True
        
        if path in target:
            if strategy == MergeStrategy.OVERRIDE:
                target[path] = deepcopy(definition)
                target[path]['_source_plugin'] = plugin_name
            elif strategy == MergeStrategy.UNION:
                # Deep merge dictionaries
                target[path] = self._deep_merge_dicts(target[path], definition)
                source_plugins = target[path].setdefault('_source_plugins', [])
                if plugin_name not in source_plugins:
                    source_plugins.append(plugin_name)
        else:
            target[path] = deepcopy(definition)
            target[path]['_source_plugin'] = plugin_name
        
        return True
    
    def _union_merge_file(self,
                         target: Dict[str, Any],
                         path: str,
                         definition: Dict[str, Any],
                         plugin_name: str) -> bool:
        """Merge file definitions using union strategy."""
        existing = target[path]
        
        # Check for incompatible properties
        incompatible_props = ['type', 'content', 'template']
        for prop in incompatible_props:
            if prop in existing and prop in definition and existing[prop] != definition[prop]:
                conflict = PluginConflict(
                    type='property_conflict',
                    plugins=[existing.get('_source_plugin', 'unknown'), plugin_name],
                    path=path,
                    message=f"Incompatible '{prop}' values for file '{path}'",
                    severity='error',
                    resolution_suggestion="Use OVERRIDE strategy to resolve"
                )
                self.context.conflicts_encountered.append(conflict)
                return False
        
        # Merge compatible properties
        merged = deepcopy(existing)
        for key, value in definition.items():
            if key not in merged:
                merged[key] = value
            elif key in ['required', 'optional']:
                # Boolean properties - use OR logic
                merged[key] = merged[key] or value
            elif key == 'description':
                # Combine descriptions
                if merged[key] != value:
                    merged[key] = f"{merged[key]}; {value}"
        
        # Track sources
        source_plugins = merged.setdefault('_source_plugins', [existing.get('_source_plugin', 'unknown')])
        if plugin_name not in source_plugins:
            source_plugins.append(plugin_name)
        
        target[path] = merged
        return True
    
    def _union_merge_file_properties(self,
                                    target_files: Dict[str, Any],
                                    file_name: str,
                                    file_def: Dict[str, Any],
                                    plugin_name: str) -> bool:
        """Merge file properties within a directory using union strategy."""
        existing = target_files[file_name]
        
        # Similar logic to _union_merge_file but for files within directories
        incompatible_props = ['type', 'content', 'template']
        for prop in incompatible_props:
            if prop in existing and prop in file_def and existing[prop] != file_def[prop]:
                conflict = PluginConflict(
                    type='property_conflict',
                    plugins=[existing.get('_source_plugin', 'unknown'), plugin_name],
                    path=file_name,
                    message=f"Incompatible '{prop}' values for file '{file_name}'",
                    severity='error'
                )
                self.context.conflicts_encountered.append(conflict)
                return False
        
        # Merge compatible properties
        for key, value in file_def.items():
            if key not in existing:
                existing[key] = value
            elif key in ['required', 'optional']:
                existing[key] = existing[key] or value
            elif key == 'description':
                if existing[key] != value:
                    existing[key] = f"{existing[key]}; {value}"
        
        # Track sources
        source_plugins = existing.setdefault('_source_plugins', [existing.get('_source_plugin', 'unknown')])
        if plugin_name not in source_plugins:
            source_plugins.append(plugin_name)
        
        return True
    
    def _merge_property_values(self, existing: Any, new: Any) -> Any:
        """Merge two property values intelligently."""
        if isinstance(existing, bool) and isinstance(new, bool):
            return existing or new  # OR logic for booleans
        elif isinstance(existing, (int, float)) and isinstance(new, (int, float)):
            return max(existing, new)  # Take maximum for numbers
        elif isinstance(existing, str) and isinstance(new, str):
            if existing == new:
                return existing
            else:
                return f"{existing},{new}"  # Combine strings
        elif isinstance(existing, list) and isinstance(new, list):
            return list(set(existing + new))  # Union for lists
        else:
            return new  # Fallback to new value
    
    def _apply_conflict_resolution(self, target: Dict[str, Any], path: str,
                                  existing: Dict[str, Any], new_definition: Dict[str, Any], 
                                  plugin_name: str, resolution) -> bool:
        """Apply interactive conflict resolution to target schema."""
        from .interactive_conflict_resolver import ConflictResolution
        
        if resolution.strategy == "skip":
            # Remove path from target entirely
            if path in target:
                del target[path]
            return True
            
        elif resolution.strategy == "override":
            if resolution.chosen_plugin == plugin_name:
                # Use new plugin's definition
                target[path] = deepcopy(new_definition)
                target[path]['_source_plugin'] = plugin_name
                target[path]['_overrode_plugin'] = existing.get('_source_plugin', 'unknown')
            else:
                # Keep existing (first plugin wins)
                pass  # No change needed
            return True
            
        elif resolution.strategy == "union":
            # Use standard union merge
            return self._union_merge_file(target, path, new_definition, plugin_name)
            
        elif resolution.strategy == "custom":
            # Use custom user-provided value
            custom_definition = {
                'type': 'file',
                '_source_plugin': f"custom_resolution_{plugin_name}",
                '_resolved_from': [existing.get('_source_plugin', 'unknown'), plugin_name]
            }
            if isinstance(resolution.custom_value, dict):
                custom_definition.update(resolution.custom_value)
            else:
                custom_definition['content'] = resolution.custom_value
            target[path] = custom_definition
            return True
            
        else:
            # Fallback to union
            self.logger.warning(f"Unknown resolution strategy {resolution.strategy}, using union")
            return self._union_merge_file(target, path, new_definition, plugin_name)
    
    def _deep_merge_dicts(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        if not isinstance(dict1, dict):
            dict1 = {}
        if not isinstance(dict2, dict):
            return dict1
            
        result = deepcopy(dict1)
        
        for key, value in dict2.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._deep_merge_dicts(result[key], value)
                else:
                    result[key] = value
            else:
                result[key] = value
        
        return result


class SchemaComposer:
    """Core schema composition system for plugin independence.
    
    Implements ADR-006 plugin schema decoupling by composing a target 
    schema from base schema + enabled plugin structure schemas.
    
    Enhanced with sophisticated merge strategies and conflict resolution.
    """
    
    def __init__(self, 
                 base_schema_path: Path,
                 plugin_directory: Path,
                 cache_enabled: bool = True,
                 default_merge_strategy: MergeStrategy = MergeStrategy.UNION,
                 interactive_resolver=None):
        """Initialize schema composer.
        
        Args:
            base_schema_path: Path to base target structure schema
            plugin_directory: Directory containing plugin subdirectories
            cache_enabled: Whether to cache composition results
            default_merge_strategy: Default strategy for conflict resolution
            interactive_resolver: InteractiveConflictResolver for INTERACTIVE strategy
        """
        self.base_schema_path = base_schema_path
        self.plugin_directory = plugin_directory
        self.cache_enabled = cache_enabled
        self.default_merge_strategy = default_merge_strategy
        self.interactive_resolver = interactive_resolver
        self.logger = get_logger(__name__)
        
        # Composition cache
        self._composition_cache: Dict[str, CompositionResult] = {}
        self._plugin_schema_cache: Dict[str, Dict[str, Any]] = {}
        
    def compose_target_schema(self, 
                            enabled_plugins: List[str],
                            dry_run: bool = False,
                            merge_strategy: Optional[MergeStrategy] = None,
                            conflict_policy: Optional[ConflictResolutionPolicy] = None,
                            plugin_dependencies: Optional[Dict[str, List[str]]] = None) -> CompositionResult:
        """Compose target schema from base + enabled plugin schemas.
        
        Args:
            enabled_plugins: List of plugin names to include
            dry_run: If True, only validate composition without caching
            merge_strategy: Strategy for handling conflicts
            conflict_policy: Detailed conflict resolution policy
            plugin_dependencies: Plugin dependency information for ordering
            
        Returns:
            CompositionResult with composed schema and any conflicts
        """
        import time
        start_time = time.time()
        
        # Use defaults if not provided
        merge_strategy = merge_strategy or self.default_merge_strategy
        conflict_policy = conflict_policy or ConflictResolutionPolicy()
        
        # Generate cache key including strategy and policy
        cache_key = f"{sorted(enabled_plugins)}:{merge_strategy.value}:{dry_run}:{hash(str(conflict_policy.__dict__))}"
        if self.cache_enabled and cache_key in self._composition_cache:
            self.logger.debug(f"Using cached composition for {len(enabled_plugins)} plugins")
            return self._composition_cache[cache_key]
        
        try:
            # Load base schema
            base_schema = self._load_base_schema()
            self.logger.debug(f"Loaded base schema from {self.base_schema_path}")
            
            # Determine plugin order based on dependencies
            plugin_order = self._calculate_plugin_order(enabled_plugins, plugin_dependencies)
            self.logger.debug(f"Plugin composition order: {plugin_order}")
            
            # Create composition context
            context = CompositionContext(
                merge_strategy=merge_strategy,
                conflict_policy=conflict_policy,
                plugin_order=plugin_order,
                conflicts_encountered=[],
                warnings_generated=[],
                merge_history=[]
            )
            
            # Load and validate plugin schemas in dependency order
            plugin_schemas = {}
            for plugin_name in plugin_order:
                schema = self.load_plugin_schema(plugin_name)
                if schema:
                    plugin_schemas[plugin_name] = schema
                else:
                    context.warnings_generated.append(f"Failed to load schema for plugin: {plugin_name}")
            
            # Detect initial conflicts before composition
            initial_conflicts = self._detect_conflicts(plugin_schemas)
            
            # Only add non-overlapping path conflicts to context initially
            # Path overlaps will be handled by merge strategies
            non_path_conflicts = [c for c in initial_conflicts if c.type != 'file_overlap']
            context.conflicts_encountered.extend(non_path_conflicts)
            
            # If there are error-level non-path conflicts and strict mode, fail composition
            error_conflicts = [c for c in non_path_conflicts if c.severity == 'error']
            if error_conflicts and merge_strategy == MergeStrategy.STRICT:
                return CompositionResult(
                    success=False,
                    composed_schema=None,
                    conflicts=[c.message for c in error_conflicts],
                    warnings=[c.message for c in context.conflicts_encountered if c.severity == 'warning'] + context.warnings_generated,
                    plugin_count=len(enabled_plugins),
                    composition_time=time.time() - start_time,
                    merge_strategy_used=merge_strategy,
                    composition_context=context
                )
            
            # Compose schemas using enhanced merge logic
            composed_schema = self._merge_schemas_enhanced(base_schema, plugin_schemas, context)
            
            # Final conflicts after composition
            all_conflicts = context.conflicts_encountered
            final_error_conflicts = [c for c in all_conflicts if c.severity == 'error']
            
            # Check if composition failed due to unresolvable conflicts
            if final_error_conflicts:
                return CompositionResult(
                    success=False,
                    composed_schema=None,
                    conflicts=[c.message for c in final_error_conflicts],
                    warnings=[c.message for c in all_conflicts if c.severity == 'warning'] + context.warnings_generated,
                    plugin_count=len(enabled_plugins),
                    composition_time=time.time() - start_time,
                    merge_strategy_used=merge_strategy,
                    composition_context=context
                )
            
            # Validate final composition
            validation_result = self.validate_composition(composed_schema)
            if not validation_result:
                return CompositionResult(
                    success=False,
                    composed_schema=None,
                    conflicts=["Composed schema failed validation"],
                    warnings=[c.message for c in all_conflicts if c.severity == 'warning'] + context.warnings_generated,
                    plugin_count=len(enabled_plugins),
                    composition_time=time.time() - start_time,
                    merge_strategy_used=merge_strategy,
                    composition_context=context
                )
            
            result = CompositionResult(
                success=True,
                composed_schema=composed_schema,
                conflicts=[],
                warnings=[c.message for c in all_conflicts if c.severity == 'warning'] + context.warnings_generated,
                plugin_count=len(enabled_plugins),
                composition_time=time.time() - start_time,
                merge_strategy_used=merge_strategy,
                composition_context=context
            )
            
            # Cache result if not dry run
            if self.cache_enabled and not dry_run:
                self._composition_cache[cache_key] = result
                
            self.logger.info(f"Successfully composed schema with {len(enabled_plugins)} plugins "
                           f"using {merge_strategy.value} strategy in {result.composition_time:.3f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Schema composition failed: {e}")
            return CompositionResult(
                success=False,
                composed_schema=None,
                conflicts=[f"Composition error: {str(e)}"],
                warnings=[],
                plugin_count=len(enabled_plugins),
                composition_time=time.time() - start_time,
                merge_strategy_used=merge_strategy
            )
    
    def _calculate_plugin_order(self, 
                               enabled_plugins: List[str],
                               plugin_dependencies: Optional[Dict[str, List[str]]] = None) -> List[str]:
        """Calculate optimal plugin order based on dependencies and priorities."""
        if not plugin_dependencies:
            # Simple alphabetical order if no dependencies
            return sorted(enabled_plugins)
        
        # Topological sort based on dependencies
        from collections import defaultdict, deque
        
        # Build graph
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        # Initialize all enabled plugins
        for plugin in enabled_plugins:
            in_degree[plugin] = 0
        
        # Build dependency edges
        for plugin in enabled_plugins:
            deps = plugin_dependencies.get(plugin, [])
            for dep in deps:
                if dep in enabled_plugins:
                    graph[dep].append(plugin)
                    in_degree[plugin] += 1
        
        # Topological sort using Kahn's algorithm
        queue = deque([plugin for plugin in enabled_plugins if in_degree[plugin] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cycles
        if len(result) != len(enabled_plugins):
            self.logger.warning("Circular dependencies detected in plugin order, using partial order")
            # Add remaining plugins in alphabetical order
            remaining = sorted(set(enabled_plugins) - set(result))
            result.extend(remaining)
        
        return result
    
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
    
    def _merge_schemas_enhanced(self, 
                               base_schema: Dict[str, Any],
                               plugin_schemas: Dict[str, Dict[str, Any]],
                               context: CompositionContext) -> Dict[str, Any]:
        """Enhanced merge with sophisticated conflict resolution.
        
        Args:
            base_schema: Base target structure schema
            plugin_schemas: Dict of plugin_name -> plugin_schema (in dependency order)
            context: Composition context with merge strategies
            
        Returns:
            Merged schema with all plugin structures integrated
        """
        composed = deepcopy(base_schema)
        path_merger = PathMerger(context, self.interactive_resolver)
        
        # Ensure expected_structure exists
        expected_structure = composed.setdefault('expected_structure', {})
        
        # Process plugins in dependency order
        for plugin_name in context.plugin_order:
            if plugin_name not in plugin_schemas:
                continue
                
            plugin_schema = plugin_schemas[plugin_name]
            self.logger.debug(f"Merging plugin schema: {plugin_name} using {context.merge_strategy.value} strategy")
            
            provides_structure = plugin_schema.get('provides_structure', {})
            
            # Merge each path from plugin into composed schema
            for path, definition in provides_structure.items():
                success = path_merger.merge_path_definition(expected_structure, path, definition, plugin_name)
                if not success:
                    self.logger.warning(f"Failed to merge path '{path}' from plugin '{plugin_name}'")
        
        # Add composition metadata
        composed['_composition_metadata'] = {
            'plugins_applied': context.plugin_order,
            'merge_strategy': context.merge_strategy.value,
            'conflicts_resolved': len([c for c in context.conflicts_encountered if c.severity != 'error']),
            'merge_operations': len(context.merge_history)
        }
        
        return composed
    
    def _merge_path_definition(self, 
                              composed_schema: Dict[str, Any],
                              path: str,
                              definition: Dict[str, Any],
                              plugin_name: str) -> None:
        """Legacy merge method - delegates to enhanced PathMerger.
        
        Maintained for backward compatibility.
        """
        # Create minimal context for legacy support
        context = CompositionContext(
            merge_strategy=self.default_merge_strategy,
            conflict_policy=ConflictResolutionPolicy(),
            plugin_order=[plugin_name],
            conflicts_encountered=[],
            warnings_generated=[],
            merge_history=[]
        )
        
        path_merger = PathMerger(context, self.interactive_resolver)
        expected_structure = composed_schema.setdefault('expected_structure', {})
        
        success = path_merger.merge_path_definition(expected_structure, path, definition, plugin_name)
        if not success:
            self.logger.warning(f"Legacy merge failed for path '{path}' from plugin '{plugin_name}'")
            # Fallback to simple merge for backward compatibility
            self._simple_merge_fallback(expected_structure, path, definition, plugin_name)
    
    def _simple_merge_fallback(self,
                              expected_structure: Dict[str, Any],
                              path: str,
                              definition: Dict[str, Any],
                              plugin_name: str) -> None:
        """Simple fallback merge for legacy compatibility."""
        if path not in expected_structure:
            expected_structure[path] = {}
        
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
