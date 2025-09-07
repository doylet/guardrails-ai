#!/usr/bin/env python3
"""
Target Structure Manager
Handles target structure composition and validation using plugin schemas.

Part of Sprint 007: Plugin Schema Decoupling
Task 2.1: Bootstrap integration points
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any

from .schema_composer import SchemaComposer
from ..utils import Colors


class TargetStructureManager:
    """Manages target structure composition and validation."""
    
    def __init__(self, target_dir: Path, plugins_dir: Path):
        """Initialize target structure manager."""
        self.target_dir = target_dir
        self.plugins_dir = plugins_dir
        
        # Path to base target structure schema
        self.base_schema_path = plugins_dir.parent / "target-structure.schema.yaml"
        
        # Initialize schema composer with paths
        self.schema_composer = SchemaComposer(self.base_schema_path, plugins_dir)
        
        # Cache for composed schema
        self._composed_schema_cache = None
        self._cache_invalidated = True
    
    def load_base_target_schema(self) -> Dict[str, Any]:
        """Load the base target structure schema."""
        try:
            with open(self.base_schema_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"{Colors.warn('[WARN]')} Base target schema not found: {self.base_schema_path}")
            return self._create_minimal_base_schema()
        except yaml.YAMLError as e:
            print(f"{Colors.error('[ERROR]')} Invalid YAML in base target schema: {e}")
            return self._create_minimal_base_schema()
    
    def _create_minimal_base_schema(self) -> Dict[str, Any]:
        """Create a minimal base schema for bootstrapping."""
        return {
            "schema_version": "1.2.0",
            "name": "ai-guardrails-target-structure",
            "expected_structure": {
                ".ai/": {
                    "required": True,
                    "description": "Core AI guardrails configuration directory",
                    "files": {
                        "guardrails.yaml": {
                            "required": True,
                            "description": "Language-specific lint/test commands"
                        }
                    }
                }
            }
        }
    
    def discover_plugin_structures(self) -> List[Dict[str, Any]]:
        """Discover all plugin structure schemas."""
        plugin_structures = []
        
        if not self.plugins_dir.exists():
            return plugin_structures
        
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir():
                structure_file = plugin_dir / "plugin-structure.schema.yaml"
                if structure_file.exists():
                    try:
                        with open(structure_file, 'r') as f:
                            structure = yaml.safe_load(f)
                            plugin_structures.append(structure)
                    except Exception as e:
                        print(f"{Colors.warn('[WARN]')} Failed to load plugin structure {structure_file}: {e}")
        
        return plugin_structures
    
    def get_composed_target_schema(self, enabled_plugins: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get the composed target structure schema.
        
        Args:
            enabled_plugins: List of plugin names to include. If None, includes all.
        
        Returns:
            Composed target structure schema
        """
        if not self._cache_invalidated and self._composed_schema_cache:
            return self._composed_schema_cache
        
        # Load base schema
        base_schema = self.load_base_target_schema()
        
        # Load plugin structures
        plugin_structures = self.discover_plugin_structures()
        
        # Filter by enabled plugins if specified
        if enabled_plugins is not None:
            filtered_structures = []
            for structure in plugin_structures:
                plugin_name = structure.get('plugin_name', '')
                if plugin_name in enabled_plugins:
                    filtered_structures.append(structure)
            plugin_structures = filtered_structures
        
        # Compose the schema
        try:
            result = self.schema_composer.compose_target_schema(
                base_schema, plugin_structures
            )
            
            # Extract the composed schema from the result
            if hasattr(result, 'composed_schema'):
                composed_schema = result.composed_schema
            else:
                # Fallback if result is already the schema
                composed_schema = result
            
            # Cache the result
            self._composed_schema_cache = composed_schema
            self._cache_invalidated = False
            
            return composed_schema
            
        except Exception as e:
            print(f"{Colors.error('[ERROR]')} Failed to compose target schema: {e}")
            return base_schema
    
    def validate_target_structure(self, target_path: Path = None) -> Dict[str, Any]:
        """
        Validate the target directory structure against the composed schema.
        
        Args:
            target_path: Path to validate. If None, uses self.target_dir.
        
        Returns:
            Validation result with status and details
        """
        if target_path is None:
            target_path = self.target_dir
        
        composed_schema = self.get_composed_target_schema()
        
        # Extract expected structure from schema
        expected_structure = composed_schema.get('expected_structure', {})
        
        validation_result = {
            'valid': True,
            'missing_required': [],
            'unexpected_files': [],
            'validation_details': {}
        }
        
        # Validate structure recursively
        self._validate_structure_recursive(
            target_path, expected_structure, validation_result
        )
        
        return validation_result
    
    def _validate_structure_recursive(self, current_path: Path, expected: Dict, result: Dict):
        """Recursively validate directory structure."""
        for path_key, config in expected.items():
            if path_key.endswith('/'):
                # Directory
                dir_path = current_path / path_key.rstrip('/')
                if config.get('required', False) and not dir_path.exists():
                    result['missing_required'].append(str(dir_path))
                    result['valid'] = False
                elif dir_path.exists():
                    # Validate subdirectories and files
                    if 'subdirs' in config:
                        self._validate_structure_recursive(dir_path, config['subdirs'], result)
                    if 'files' in config:
                        self._validate_files(dir_path, config['files'], result)
            else:
                # File
                file_path = current_path / path_key
                if config.get('required', False) and not file_path.exists():
                    result['missing_required'].append(str(file_path))
                    result['valid'] = False
    
    def _validate_files(self, dir_path: Path, expected_files: Dict, result: Dict):
        """Validate files in a directory."""
        for filename, config in expected_files.items():
            file_path = dir_path / filename
            if config.get('required', False) and not file_path.exists():
                result['missing_required'].append(str(file_path))
                result['valid'] = False
    
    def get_plugin_dependencies(self, plugin_structures: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Analyze plugin dependencies based on structure requirements.
        
        Returns:
            Dictionary mapping plugin names to their dependencies
        """
        dependencies = {}
        
        for structure in plugin_structures:
            plugin_name = structure.get('plugin_name', '')
            deps = structure.get('dependencies', [])
            requires_structure = structure.get('requires_structure', [])
            
            # Convert structure requirements to plugin dependencies
            structure_deps = []
            for required_path in requires_structure:
                # Find which plugins provide this structure
                for other_structure in plugin_structures:
                    other_name = other_structure.get('plugin_name', '')
                    if other_name != plugin_name:
                        provides = other_structure.get('provides_structure', {})
                        if required_path in provides or required_path.rstrip('/') + '/' in provides:
                            structure_deps.append(other_name)
            
            # Combine explicit and inferred dependencies
            all_deps = list(set(deps + structure_deps))
            dependencies[plugin_name] = all_deps
        
        return dependencies
    
    def invalidate_cache(self):
        """Invalidate the composed schema cache."""
        self._cache_invalidated = True
        self._composed_schema_cache = None
    
    def generate_structure_report(self) -> Dict[str, Any]:
        """Generate a comprehensive structure report."""
        plugin_structures = self.discover_plugin_structures()
        composed_schema = self.get_composed_target_schema()
        validation_result = self.validate_target_structure()
        dependencies = self.get_plugin_dependencies(plugin_structures)
        
        return {
            'schema_version': composed_schema.get('schema_version', 'unknown'),
            'total_plugins': len(plugin_structures),
            'plugin_names': [s.get('plugin_name', 'unknown') for s in plugin_structures],
            'structure_valid': validation_result['valid'],
            'missing_required': validation_result['missing_required'],
            'plugin_dependencies': dependencies,
            'conflicts': []  # TODO: Implement conflict detection in schema composer
        }
