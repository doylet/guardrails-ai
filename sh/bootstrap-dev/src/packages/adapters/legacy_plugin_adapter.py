"""
Legacy Plugin Adapter for AI Guardrails Bootstrap System

This module provides backward compatibility with the legacy plugin format
by automatically converting legacy plugin manifests to the enhanced format.
This ensures all existing plugins continue to work without modification.

Features:
- Automatic conversion of legacy file_patterns to FileOperation objects
- Mapping of legacy component definitions to enhanced format
- Default value provision for new fields
- Warning system for deprecated features
- Migration assistance utilities
"""

import warnings
from typing import Dict, List, Any

from ..domain.plugin_models import (
    PluginManifest, LegacyPluginManifest, ComponentDefinition, FileOperation,
    PluginDependency
)


class LegacyPluginAdapter:
    """Adapter for converting legacy plugins to enhanced format."""

    def __init__(self, warn_deprecated: bool = True):
        self.warn_deprecated = warn_deprecated
        self.conversion_warnings = []

    def convert_legacy_manifest(self, legacy_data: Dict[str, Any]) -> PluginManifest:
        """
        Convert legacy plugin manifest to enhanced format.

        Args:
            legacy_data: Legacy plugin manifest data

        Returns:
            Enhanced plugin manifest
        """
        # Reset warnings for this conversion
        self.conversion_warnings = []

        # Create legacy manifest object
        legacy_manifest = self._create_legacy_manifest(legacy_data)

        # Convert to enhanced format
        enhanced_manifest = self._convert_to_enhanced(legacy_manifest)

        # Issue deprecation warnings if enabled
        if self.warn_deprecated and self.conversion_warnings:
            for warning_msg in self.conversion_warnings:
                warnings.warn(warning_msg, DeprecationWarning, stacklevel=2)

        return enhanced_manifest

    def is_legacy_format(self, manifest_data: Dict[str, Any]) -> bool:
        """
        Check if manifest data uses legacy format.

        Args:
            manifest_data: Plugin manifest data

        Returns:
            True if legacy format detected
        """
        # Check for legacy indicators
        legacy_indicators = [
            # Legacy has simple string dependencies
            isinstance(manifest_data.get('dependencies', []), list) and
            len(manifest_data.get('dependencies', [])) > 0 and
            isinstance(manifest_data['dependencies'][0], str),

            # Legacy components use file_patterns
            any(
                'file_patterns' in component
                for component in manifest_data.get('components', {}).values()
                if isinstance(component, dict)
            ),

            # Missing enhanced fields
            'api_version' not in manifest_data,
            'environment' not in manifest_data,
        ]

        return any(legacy_indicators)

    def suggest_migration_improvements(self, manifest: PluginManifest) -> List[str]:
        """
        Suggest improvements for migrated legacy plugins.

        Args:
            manifest: Converted plugin manifest

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Suggest adding metadata
        if not manifest.author:
            suggestions.append("Consider adding 'author' field for better plugin attribution")

        if not manifest.license:
            suggestions.append("Consider adding 'license' field (e.g., 'MIT', 'Apache-2.0')")

        if not manifest.homepage:
            suggestions.append("Consider adding 'homepage' field with repository URL")

        # Suggest environment requirements
        if not manifest.environment:
            suggestions.append("Consider adding 'environment' section with platform requirements")

        # Suggest profiles
        if not manifest.profiles:
            suggestions.append("Consider adding installation 'profiles' for different use cases")

        # Suggest enhanced file operations
        for component_name, component in manifest.components.items():
            for file_op in component.files:
                if file_op.action == "copy" and not file_op.mode:
                    suggestions.append(
                        f"Component '{component_name}': consider specifying file permissions"
                    )

                if file_op.action == "copy" and self._could_be_template(file_op.pattern):
                    suggestions.append(
                        f"Component '{component_name}': file '{file_op.pattern}' "
                        f"might benefit from template processing"
                    )

        # Suggest lifecycle hooks
        for component_name, component in manifest.components.items():
            if not component.hooks:
                suggestions.append(
                    f"Component '{component_name}': consider adding lifecycle hooks "
                    f"for validation or setup"
                )

        return suggestions

    def generate_migration_report(self, legacy_data: Dict[str, Any],
                                enhanced_manifest: PluginManifest) -> Dict[str, Any]:
        """
        Generate a detailed migration report.

        Args:
            legacy_data: Original legacy data
            enhanced_manifest: Converted enhanced manifest

        Returns:
            Migration report with changes and suggestions
        """
        report = {
            "plugin_name": enhanced_manifest.name,
            "conversion_status": "success",
            "changes_made": [],
            "warnings": self.conversion_warnings.copy(),
            "suggestions": self.suggest_migration_improvements(enhanced_manifest),
            "compatibility": "backward_compatible",
            "enhanced_features": []
        }

        # Document changes made during conversion
        if "api_version" not in legacy_data:
            report["changes_made"].append("Added api_version field (set to 'v1' for compatibility)")

        if isinstance(legacy_data.get('dependencies', []), list):
            report["changes_made"].append("Converted string dependencies to PluginDependency objects")

        for component_name, component_data in legacy_data.get('components', {}).items():
            if 'file_patterns' in component_data:
                report["changes_made"].append(
                    f"Converted file_patterns to FileOperation objects in component '{component_name}'"
                )

        # Document available enhanced features
        report["enhanced_features"] = [
            "Template processing with Jinja2",
            "YAML/JSON file merging",
            "Conditional file operations",
            "Lifecycle hooks (pre/post install, validation)",
            "Configuration schema validation",
            "Environment requirements specification",
            "Installation profiles",
            "Enhanced dependency management"
        ]

        return report

    def _create_legacy_manifest(self, legacy_data: Dict[str, Any]) -> LegacyPluginManifest:
        """Create LegacyPluginManifest from raw data."""
        return LegacyPluginManifest(
            name=legacy_data.get('name', ''),
            version=legacy_data.get('version', '1.0.0'),
            description=legacy_data.get('description', ''),
            dependencies=legacy_data.get('dependencies', []),
            components=legacy_data.get('components', {})
        )

    def _convert_to_enhanced(self, legacy_manifest: LegacyPluginManifest) -> PluginManifest:
        """Convert legacy manifest to enhanced format."""
        # Convert dependencies
        enhanced_dependencies = []
        for dep in legacy_manifest.dependencies:
            if isinstance(dep, str):
                enhanced_dependencies.append(PluginDependency(plugin=dep))
                self.conversion_warnings.append(
                    f"Converted string dependency '{dep}' to PluginDependency object"
                )
            elif isinstance(dep, dict):
                # Already in enhanced format
                enhanced_dependencies.append(PluginDependency(**dep))

        # Convert components
        enhanced_components = {}
        for component_name, component_data in legacy_manifest.components.items():
            enhanced_components[component_name] = self._convert_component(
                component_name, component_data
            )

        # Create enhanced manifest with legacy compatibility
        enhanced_manifest = PluginManifest(
            name=legacy_manifest.name,
            version=legacy_manifest.version,
            description=legacy_manifest.description,
            api_version="v1",  # Mark as legacy for compatibility
            dependencies=enhanced_dependencies,
            components=enhanced_components
        )

        return enhanced_manifest

    def _convert_component(self, component_name: str, component_data: Dict[str, Any]) -> ComponentDefinition:
        """Convert legacy component to enhanced format."""
        file_operations = []

        # Convert file_patterns to FileOperation objects
        if 'file_patterns' in component_data:
            for pattern in component_data['file_patterns']:
                # Determine target based on pattern
                target = self._infer_target_from_pattern(pattern)

                file_operations.append(FileOperation(
                    pattern=pattern,
                    action="copy",  # Default action for legacy patterns
                    target=target
                ))

            self.conversion_warnings.append(
                f"Component '{component_name}': converted file_patterns to FileOperation objects"
            )

        # Convert any existing files field (if present)
        if 'files' in component_data:
            for file_data in component_data['files']:
                if isinstance(file_data, dict):
                    file_operations.append(FileOperation(**file_data))
                elif isinstance(file_data, str):
                    # Convert string to FileOperation
                    target = self._infer_target_from_pattern(file_data)
                    file_operations.append(FileOperation(
                        pattern=file_data,
                        action="copy",
                        target=target
                    ))

        return ComponentDefinition(
            name=component_name,
            description=component_data.get('description', f'Legacy component {component_name}'),
            priority=component_data.get('priority', 100),
            files=file_operations,
            dependencies=component_data.get('dependencies', [])
        )

    def _infer_target_from_pattern(self, pattern: str) -> str:
        """Infer target directory from file pattern."""
        # Common pattern mappings for legacy plugins
        pattern_mappings = {
            '.github/**/*': '.github/',
            '.ai/**/*': '.ai/',
            'scripts/**/*': 'scripts/',
            'config/**/*': '.ai/',
            'templates/**/*': '.ai/',
            'docs/**/*': 'docs/',
        }

        for pattern_key, target in pattern_mappings.items():
            if pattern.startswith(pattern_key.split('**')[0]):
                return target

        # Default target based on file extension or location
        if pattern.startswith('.github/'):
            return '.github/'
        elif pattern.startswith('.ai/'):
            return '.ai/'
        elif pattern.endswith('.yml') or pattern.endswith('.yaml'):
            return '.ai/'
        elif pattern.endswith('.md'):
            return 'docs/'
        else:
            return '.'  # Root directory

    def _could_be_template(self, pattern: str) -> bool:
        """Check if a file pattern suggests it could benefit from templating."""
        template_indicators = [
            'config' in pattern.lower(),
            'template' in pattern.lower(),
            '.yml' in pattern or '.yaml' in pattern,
            '.json' in pattern,
            '.md' in pattern,
            'README' in pattern
        ]

        return any(template_indicators)


class LegacyPluginWarning(UserWarning):
    """Warning issued for legacy plugin features."""
    pass


def warn_legacy_feature(message: str) -> None:
    """Issue a warning for legacy plugin features."""
    warnings.warn(message, LegacyPluginWarning, stacklevel=3)
