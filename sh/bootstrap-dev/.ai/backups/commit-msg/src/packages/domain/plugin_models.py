"""
Enhanced Plugin Domain Models for AI Guardrails Bootstrap System

This module defines the enhanced plugin architecture with support for:
- Enhanced metadata and dependency management
- Advanced file operations (copy, template, merge)
- Lifecycle hooks for plugin customization
- Configuration schema validation
- Environment requirements and platform detection
- Backward compatibility with legacy plugin format

Design Philosophy:
- Evolution over revolution - enhance existing architecture
- Backward compatibility - all existing plugins continue working
- Progressive enhancement - optional adoption of new features
- Security first - validation and sandboxing
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal, Union, Any
from enum import Enum


class PluginAPIVersion(Enum):
    """Supported plugin API versions."""
    V1 = "v1"  # Legacy format
    V2 = "v2"  # Enhanced format


class FileActionType(Enum):
    """Supported file operation types."""
    COPY = "copy"
    TEMPLATE = "template"
    MERGE = "merge"


class MergeStrategy(Enum):
    """YAML/JSON merge strategies."""
    DEEP = "deep"
    REPLACE = "replace"
    APPEND = "append"


@dataclass
class PluginEnvironment:
    """Plugin environment requirements and detection."""
    requires: List[str] = field(default_factory=list)
    """Required tools/commands that must be available."""

    detects: List[str] = field(default_factory=list)
    """Tools/languages the plugin can detect and work with."""

    platforms: List[str] = field(default_factory=list)
    """Supported platforms: linux, macos, windows."""

    min_versions: Dict[str, str] = field(default_factory=dict)
    """Minimum required versions for tools."""

    def __post_init__(self):
        """Validate environment configuration."""
        valid_platforms = {"linux", "macos", "windows"}
        for platform in self.platforms:
            if platform not in valid_platforms:
                raise ValueError(f"Invalid platform: {platform}. Must be one of {valid_platforms}")


@dataclass
class PluginDependency:
    """Plugin dependency specification with version constraints."""
    plugin: str
    """Name of the required plugin."""

    version: str = ">=0.0.0"
    """Version constraint (semver compatible)."""

    optional: bool = False
    """Whether this dependency is optional."""

    reason: Optional[str] = None
    """Human-readable reason for this dependency."""

    def __post_init__(self):
        """Validate dependency specification."""
        if not self.plugin:
            raise ValueError("Plugin dependency must have a name")
        if not self.version:
            raise ValueError("Plugin dependency must have a version constraint")


@dataclass
class FileOperation:
    """Enhanced file operation with action types and conditions."""
    pattern: str
    """Glob pattern for source files."""

    action: Literal["copy", "template", "merge"]
    """Type of operation to perform."""

    target: str
    """Target path for the operation."""

    mode: Optional[int] = None
    """File permissions (octal, e.g., 0o644)."""

    owner: Optional[str] = None
    """File owner (username)."""

    backup: bool = False
    """Whether to backup existing files before operation."""

    variables: Dict[str, str] = field(default_factory=dict)
    """Template variables for template operations."""

    condition: Optional[str] = None
    """Jinja2 condition expression for conditional operations."""

    strategy: Optional[str] = None
    """Merge strategy for merge operations."""

    def __post_init__(self):
        """Validate file operation configuration."""
        if not self.pattern:
            raise ValueError("File operation must have a pattern")
        if not self.target:
            raise ValueError("File operation must have a target")
        if self.action not in ["copy", "template", "merge"]:
            raise ValueError(f"Invalid action: {self.action}")
        if self.action == "merge" and not self.strategy:
            self.strategy = "deep"  # Default merge strategy


@dataclass
class LifecycleHooks:
    """Plugin lifecycle hook scripts."""
    pre_install: Optional[str] = None
    """Script to run before plugin installation."""

    post_install: Optional[str] = None
    """Script to run after plugin installation."""

    validate: Optional[str] = None
    """Script to validate plugin installation."""

    cleanup: Optional[str] = None
    """Script to cleanup plugin resources."""

    def get_hooks(self) -> Dict[str, str]:
        """Get all defined hooks as a dictionary."""
        hooks = {}
        for hook_name in ["pre_install", "post_install", "validate", "cleanup"]:
            hook_script = getattr(self, hook_name)
            if hook_script:
                hooks[hook_name] = hook_script
        return hooks


@dataclass
class ComponentDefinition:
    """Enhanced component definition with priority and schema."""
    name: str
    """Component name."""

    description: str
    """Human-readable component description."""

    priority: int = 100
    """Installation priority (higher numbers install first)."""

    files: List[FileOperation] = field(default_factory=list)
    """File operations for this component."""

    hooks: Optional[LifecycleHooks] = None
    """Lifecycle hooks for this component."""

    config_schema: Optional[Dict[str, Any]] = None
    """JSON Schema for component configuration."""

    dependencies: List[str] = field(default_factory=list)
    """Other components this component depends on."""

    def __post_init__(self):
        """Validate component definition."""
        if not self.name:
            raise ValueError("Component must have a name")
        if not self.description:
            raise ValueError("Component must have a description")
        if self.priority < 0:
            raise ValueError("Component priority must be non-negative")


@dataclass
class PluginProfile:
    """Plugin installation profile."""
    name: str
    """Profile name."""

    description: str
    """Human-readable profile description."""

    components: List[str]
    """Components included in this profile."""

    def __post_init__(self):
        """Validate profile definition."""
        if not self.name:
            raise ValueError("Profile must have a name")
        if not self.components:
            raise ValueError("Profile must include at least one component")


@dataclass
class PluginManifest:
    """Enhanced plugin manifest with full metadata support."""
    name: str
    """Plugin name (must be unique)."""

    version: str
    """Plugin version (semver compatible)."""

    description: str
    """Human-readable plugin description."""

    author: Optional[str] = None
    """Plugin author/organization."""

    license: Optional[str] = None
    """Plugin license (SPDX identifier preferred)."""

    homepage: Optional[str] = None
    """Plugin homepage/repository URL."""

    api_version: str = "v1"
    """Plugin API version."""

    min_bootstrap_version: str = ">=1.0.0"
    """Minimum required bootstrap system version."""

    dependencies: List[PluginDependency] = field(default_factory=list)
    """Plugin dependencies."""

    environment: Optional[PluginEnvironment] = None
    """Environment requirements."""

    components: Dict[str, ComponentDefinition] = field(default_factory=dict)
    """Plugin components."""

    configuration: Dict[str, Union[str, bool, int, float]] = field(default_factory=dict)
    """Plugin-level configuration."""

    profiles: Dict[str, PluginProfile] = field(default_factory=dict)
    """Installation profiles."""

    def __post_init__(self):
        """Validate plugin manifest."""
        if not self.name:
            raise ValueError("Plugin must have a name")
        if not self.version:
            raise ValueError("Plugin must have a version")
        if not self.description:
            raise ValueError("Plugin must have a description")
        if not self.components:
            raise ValueError("Plugin must have at least one component")

        # Validate API version
        try:
            PluginAPIVersion(self.api_version)
        except ValueError:
            raise ValueError(f"Invalid API version: {self.api_version}")

    def get_default_profile(self) -> Optional[PluginProfile]:
        """Get the default installation profile."""
        if "standard" in self.profiles:
            return self.profiles["standard"]
        elif "minimal" in self.profiles:
            return self.profiles["minimal"]
        elif self.profiles:
            return next(iter(self.profiles.values()))
        else:
            # Create default profile with all components
            return PluginProfile(
                name="default",
                description="Default installation with all components",
                components=list(self.components.keys())
            )

    def is_legacy_format(self) -> bool:
        """Check if this uses the legacy plugin format."""
        return self.api_version == "v1"

    def get_component_by_name(self, name: str) -> Optional[ComponentDefinition]:
        """Get a component by name."""
        return self.components.get(name)

    def validate_component_dependencies(self) -> List[str]:
        """Validate component dependencies and return any errors."""
        errors = []
        component_names = set(self.components.keys())

        for component_name, component in self.components.items():
            for dependency in component.dependencies:
                if dependency not in component_names:
                    errors.append(
                        f"Component '{component_name}' depends on unknown component '{dependency}'"
                    )

        return errors


@dataclass
class LegacyPluginManifest:
    """Legacy plugin manifest format for backward compatibility."""
    name: str
    version: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    components: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_enhanced_manifest(self) -> PluginManifest:
        """Convert legacy manifest to enhanced format."""
        enhanced_components = {}

        for component_name, component_data in self.components.items():
            # Convert legacy file_patterns to FileOperation objects
            file_operations = []
            if "file_patterns" in component_data:
                for pattern in component_data["file_patterns"]:
                    file_operations.append(FileOperation(
                        pattern=pattern,
                        action="copy",
                        target="."  # Default target
                    ))

            enhanced_components[component_name] = ComponentDefinition(
                name=component_name,
                description=component_data.get("description", f"Legacy component {component_name}"),
                files=file_operations
            )

        # Convert legacy dependencies to enhanced format
        enhanced_dependencies = [
            PluginDependency(plugin=dep) for dep in self.dependencies
        ]

        return PluginManifest(
            name=self.name,
            version=self.version,
            description=self.description,
            api_version="v1",  # Mark as legacy
            dependencies=enhanced_dependencies,
            components=enhanced_components
        )


class PluginValidationError(Exception):
    """Exception raised when plugin validation fails."""

    def __init__(self, message: str, errors: List[str] = None):
        super().__init__(message)
        self.errors = errors or []


class PluginSecurityError(Exception):
    """Exception raised when plugin security validation fails."""
    pass


class PluginDependencyError(Exception):
    """Exception raised when plugin dependency resolution fails."""
    pass
