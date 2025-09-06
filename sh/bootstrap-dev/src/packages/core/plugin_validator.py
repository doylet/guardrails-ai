"""
Plugin Validator for AI Guardrails Bootstrap System

This module provides comprehensive validation for plugin manifests, dependencies,
and file operations. It ensures plugins are secure, well-formed, and compatible
with the bootstrap system.

Validation Features:
- Plugin manifest schema validation
- Dependency resolution and version checking
- File pattern validation and conflict detection
- Component configuration schema validation
- Environment requirement validation
- Security validation for file operations
"""

import re
import jsonschema
from pathlib import Path
from typing import Dict, List, Any, Set

from ..domain.plugin_models import (
    PluginManifest, PluginDependency, ComponentDefinition, FileOperation,
    PluginEnvironment
)


class PluginValidator:
    """Comprehensive plugin validation with security checks."""

    def __init__(self):
        self.manifest_schema = self._load_manifest_schema()
        self.valid_platforms = {"linux", "macos", "windows"}
        self.forbidden_paths = {
            "/etc", "/usr", "/bin", "/sbin", "/lib", "/lib64",
            "/boot", "/dev", "/proc", "/sys", "/run"
        }

    def validate_plugin_manifest(self, manifest: PluginManifest) -> List[str]:
        """
        Validate plugin manifest comprehensively.

        Args:
            manifest: Plugin manifest to validate

        Returns:
            List of validation error messages
        """
        errors = []

        try:
            # Basic field validation
            errors.extend(self._validate_basic_fields(manifest))

            # Version validation
            errors.extend(self._validate_versions(manifest))

            # Environment validation
            if manifest.environment:
                errors.extend(self._validate_environment(manifest.environment))

            # Dependencies validation
            errors.extend(self._validate_dependencies(manifest.dependencies))

            # Components validation
            errors.extend(self._validate_components(manifest.components))

            # Profiles validation
            errors.extend(self._validate_profiles(manifest))

            # Cross-component validation
            errors.extend(self._validate_component_relationships(manifest))

        except Exception as e:
            errors.append(f"Unexpected validation error: {e}")

        return errors

    def validate_plugin_security(self, manifest: PluginManifest, plugin_path: Path) -> List[str]:
        """
        Validate plugin security aspects.

        Args:
            manifest: Plugin manifest to validate
            plugin_path: Path to plugin directory

        Returns:
            List of security violation messages
        """
        errors = []

        try:
            # Validate file operations security
            for component in manifest.components.values():
                for file_op in component.files:
                    errors.extend(self._validate_file_operation_security(file_op, plugin_path))

            # Validate hook scripts security
            for component in manifest.components.values():
                if component.hooks:
                    errors.extend(self._validate_hooks_security(component.hooks, plugin_path))

            # Validate plugin directory structure
            errors.extend(self._validate_directory_security(plugin_path))

        except Exception as e:
            errors.append(f"Security validation error: {e}")

        return errors

    def validate_dependencies(self, dependencies: List[PluginDependency],
                            available_plugins: Dict[str, PluginManifest]) -> List[str]:
        """
        Validate plugin dependencies can be resolved.

        Args:
            dependencies: List of plugin dependencies
            available_plugins: Available plugins by name

        Returns:
            List of dependency resolution errors
        """
        errors = []

        for dep in dependencies:
            if dep.plugin not in available_plugins:
                if not dep.optional:
                    errors.append(f"Required dependency '{dep.plugin}' not found")
                continue

            available_plugin = available_plugins[dep.plugin]
            if not self._check_version_constraint(available_plugin.version, dep.version):
                errors.append(
                    f"Dependency '{dep.plugin}' version {available_plugin.version} "
                    f"does not satisfy constraint {dep.version}"
                )

        return errors

    def validate_file_conflicts(self, manifests: List[PluginManifest]) -> List[str]:
        """
        Validate that plugins don't have conflicting file operations.

        Args:
            manifests: List of plugin manifests to check

        Returns:
            List of file conflict errors
        """
        errors = []
        file_targets = {}

        for manifest in manifests:
            for component_name, component in manifest.components.items():
                for file_op in component.files:
                    target_pattern = file_op.target

                    if target_pattern in file_targets:
                        existing = file_targets[target_pattern]
                        errors.append(
                            f"File conflict: {manifest.name}.{component_name} and "
                            f"{existing['plugin']}.{existing['component']} both target '{target_pattern}'"
                        )
                    else:
                        file_targets[target_pattern] = {
                            'plugin': manifest.name,
                            'component': component_name,
                            'operation': file_op.action
                        }

        return errors

    def _validate_basic_fields(self, manifest: PluginManifest) -> List[str]:
        """Validate basic required fields."""
        errors = []

        if not manifest.name:
            errors.append("Plugin name is required")
        elif not self._is_valid_plugin_name(manifest.name):
            errors.append(f"Invalid plugin name: {manifest.name}")

        if not manifest.version:
            errors.append("Plugin version is required")
        elif not self._is_valid_semver(manifest.version):
            errors.append(f"Invalid version format: {manifest.version}")

        if not manifest.description:
            errors.append("Plugin description is required")

        if not manifest.components:
            errors.append("Plugin must have at least one component")

        return errors

    def _validate_versions(self, manifest: PluginManifest) -> List[str]:
        """Validate version fields."""
        errors = []

        if not self._is_valid_semver(manifest.version):
            errors.append(f"Invalid plugin version: {manifest.version}")

        if not self._is_valid_version_constraint(manifest.min_bootstrap_version):
            errors.append(f"Invalid bootstrap version constraint: {manifest.min_bootstrap_version}")

        return errors

    def _validate_environment(self, environment: PluginEnvironment) -> List[str]:
        """Validate environment requirements."""
        errors = []

        # Validate platforms
        for platform in environment.platforms:
            if platform not in self.valid_platforms:
                errors.append(f"Invalid platform: {platform}")

        # Validate tool names
        invalid_chars = re.compile(r'[^a-zA-Z0-9\-_]')
        for tool in environment.requires + environment.detects:
            if invalid_chars.search(tool):
                errors.append(f"Invalid tool name: {tool}")

        # Validate version constraints
        for tool, version in environment.min_versions.items():
            if tool not in environment.requires + environment.detects:
                errors.append(f"Version specified for undeclared tool: {tool}")
            if not self._is_valid_version_constraint(version):
                errors.append(f"Invalid version constraint for {tool}: {version}")

        return errors

    def _validate_dependencies(self, dependencies: List[PluginDependency]) -> List[str]:
        """Validate plugin dependencies."""
        errors = []
        seen_plugins = set()

        for dep in dependencies:
            if not dep.plugin:
                errors.append("Dependency must have a plugin name")
                continue

            if dep.plugin in seen_plugins:
                errors.append(f"Duplicate dependency: {dep.plugin}")
            seen_plugins.add(dep.plugin)

            if not self._is_valid_plugin_name(dep.plugin):
                errors.append(f"Invalid dependency plugin name: {dep.plugin}")

            if not self._is_valid_version_constraint(dep.version):
                errors.append(f"Invalid version constraint for {dep.plugin}: {dep.version}")

        return errors

    def _validate_components(self, components: Dict[str, ComponentDefinition]) -> List[str]:
        """Validate plugin components."""
        errors = []

        for name, component in components.items():
            if not self._is_valid_component_name(name):
                errors.append(f"Invalid component name: {name}")

            if component.priority < 0:
                errors.append(f"Component {name} priority must be non-negative")

            # Validate file operations
            for file_op in component.files:
                errors.extend(self._validate_file_operation(file_op, name))

            # Validate configuration schema
            if component.config_schema:
                errors.extend(self._validate_config_schema(component.config_schema, name))

        return errors

    def _validate_profiles(self, manifest: PluginManifest) -> List[str]:
        """Validate plugin profiles."""
        errors = []
        component_names = set(manifest.components.keys())

        for profile_name, profile in manifest.profiles.items():
            if not self._is_valid_profile_name(profile_name):
                errors.append(f"Invalid profile name: {profile_name}")

            for component_name in profile.components:
                if component_name not in component_names:
                    errors.append(
                        f"Profile {profile_name} references unknown component: {component_name}"
                    )

        return errors

    def _validate_component_relationships(self, manifest: PluginManifest) -> List[str]:
        """Validate component dependency relationships."""
        errors = []
        component_names = set(manifest.components.keys())

        # Check component dependencies
        for component_name, component in manifest.components.items():
            for dep_name in component.dependencies:
                if dep_name not in component_names:
                    errors.append(
                        f"Component {component_name} depends on unknown component: {dep_name}"
                    )

        # Check for circular dependencies
        errors.extend(self._detect_circular_dependencies(manifest.components))

        return errors

    def _validate_file_operation(self, file_op: FileOperation, component_name: str) -> List[str]:
        """Validate a single file operation."""
        errors = []

        if not file_op.pattern:
            errors.append(f"Component {component_name}: file operation missing pattern")

        if not file_op.target:
            errors.append(f"Component {component_name}: file operation missing target")

        if file_op.action not in ["copy", "template", "merge"]:
            errors.append(f"Component {component_name}: invalid action {file_op.action}")

        # Validate target path safety
        if self._is_dangerous_target_path(file_op.target):
            errors.append(f"Component {component_name}: dangerous target path {file_op.target}")

        # Validate merge strategy
        if file_op.action == "merge" and file_op.strategy:
            if file_op.strategy not in ["deep", "replace", "append"]:
                errors.append(f"Component {component_name}: invalid merge strategy {file_op.strategy}")

        return errors

    def _validate_config_schema(self, schema: Dict[str, Any], component_name: str) -> List[str]:
        """Validate JSON schema for component configuration."""
        errors = []

        try:
            # Validate that it's a valid JSON schema
            jsonschema.Draft7Validator.check_schema(schema)
        except jsonschema.SchemaError as e:
            errors.append(f"Component {component_name}: invalid config schema: {e}")

        return errors

    def _validate_file_operation_security(self, file_op: FileOperation, plugin_path: Path) -> List[str]:
        """Validate security aspects of file operations."""
        errors = []

        # Check for path traversal in patterns
        if ".." in file_op.pattern:
            errors.append(f"Dangerous path traversal in pattern: {file_op.pattern}")

        # Check for dangerous target paths
        if self._is_dangerous_target_path(file_op.target):
            errors.append(f"Dangerous target path: {file_op.target}")

        # Validate source files exist within plugin directory
        try:
            source_files = list(plugin_path.glob(file_op.pattern))
            for source_file in source_files:
                source_file.resolve().relative_to(plugin_path.resolve())
        except ValueError:
            errors.append(f"Pattern accesses files outside plugin directory: {file_op.pattern}")
        except Exception:
            # Pattern might be invalid, but that's caught elsewhere
            pass

        return errors

    def _validate_hooks_security(self, hooks, plugin_path: Path) -> List[str]:
        """Validate security of lifecycle hooks."""
        errors = []

        for hook_name, hook_script in hooks.get_hooks().items():
            if not hook_script:
                continue

            hook_path = plugin_path / hook_script

            # Check that hook script is within plugin directory
            try:
                hook_path.resolve().relative_to(plugin_path.resolve())
            except ValueError:
                errors.append(f"Hook {hook_name} script outside plugin directory: {hook_script}")

            # Check that hook script exists
            if not hook_path.exists():
                errors.append(f"Hook {hook_name} script not found: {hook_script}")

            # Check that hook script is executable
            elif not hook_path.is_file():
                errors.append(f"Hook {hook_name} script is not a file: {hook_script}")

        return errors

    def _validate_directory_security(self, plugin_path: Path) -> List[str]:
        """Validate plugin directory structure for security."""
        errors = []

        try:
            # Check for suspicious files
            for file_path in plugin_path.rglob("*"):
                if file_path.is_file():
                    # Check for executable files in suspicious locations
                    if file_path.suffix in ['.exe', '.bat', '.com', '.scr']:
                        errors.append(f"Suspicious executable file: {file_path}")

                    # Check file size
                    try:
                        if file_path.stat().st_size > 100 * 1024 * 1024:  # 100MB
                            errors.append(f"Unusually large file: {file_path}")
                    except OSError:
                        pass

        except Exception as e:
            errors.append(f"Error validating directory structure: {e}")

        return errors

    def _detect_circular_dependencies(self, components: Dict[str, ComponentDefinition]) -> List[str]:
        """Detect circular dependencies between components."""
        errors = []

        def visit(component_name: str, path: List[str], visited: Set[str]) -> None:
            if component_name in path:
                cycle = " -> ".join(path[path.index(component_name):] + [component_name])
                errors.append(f"Circular dependency detected: {cycle}")
                return

            if component_name in visited:
                return

            visited.add(component_name)

            if component_name in components:
                component = components[component_name]
                for dep in component.dependencies:
                    visit(dep, path + [component_name], visited)

        visited = set()
        for component_name in components:
            if component_name not in visited:
                visit(component_name, [], visited)

        return errors

    def _is_valid_plugin_name(self, name: str) -> bool:
        """Check if plugin name is valid."""
        return bool(re.match(r'^[a-z0-9\-]+$', name))

    def _is_valid_component_name(self, name: str) -> bool:
        """Check if component name is valid."""
        return bool(re.match(r'^[a-z0-9\-_]+$', name))

    def _is_valid_profile_name(self, name: str) -> bool:
        """Check if profile name is valid."""
        return bool(re.match(r'^[a-z0-9\-_]+$', name))

    def _is_valid_semver(self, version: str) -> bool:
        """Check if version follows semantic versioning."""
        pattern = r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
        return bool(re.match(pattern, version))

    def _is_valid_version_constraint(self, constraint: str) -> bool:
        """Check if version constraint is valid."""
        # Simple validation for now - could be enhanced with proper semver parsing
        pattern = r'^(>=|>|<=|<|==|~|^)?([0-9]+\.[0-9]+\.[0-9]+.*)$'
        return bool(re.match(pattern, constraint))

    def _check_version_constraint(self, version: str, constraint: str) -> bool:
        """Check if version satisfies constraint."""
        # Simplified version checking - in production would use proper semver library
        if constraint.startswith('>='):
            return version >= constraint[2:]
        elif constraint.startswith('>'):
            return version > constraint[1:]
        elif constraint.startswith('<='):
            return version <= constraint[2:]
        elif constraint.startswith('<'):
            return version < constraint[1:]
        elif constraint.startswith('=='):
            return version == constraint[2:]
        else:
            return version >= constraint

    def _is_dangerous_target_path(self, target: str) -> bool:
        """Check if target path is potentially dangerous."""
        # Normalize path
        normalized = str(Path(target).resolve())

        # Check for dangerous system paths
        for forbidden in self.forbidden_paths:
            if normalized.startswith(forbidden):
                return True

        # Check for path traversal
        if ".." in target or target.startswith("/"):
            return True

        return False

    def _load_manifest_schema(self) -> Dict[str, Any]:
        """Load the JSON schema for plugin manifests."""
        # This would load from a schema file in production
        return {
            "type": "object",
            "required": ["name", "version", "description", "components"],
            "properties": {
                "name": {"type": "string", "pattern": "^[a-z0-9\\-]+$"},
                "version": {"type": "string"},
                "description": {"type": "string"},
                "components": {"type": "object"}
            }
        }
