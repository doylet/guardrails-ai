"""Dependency resolution and manifest loading for the AI Guardrails Bootstrap System.

This module provides pure dependency resolution logic, loading and validating
installation manifests and plugin manifests, computing installation order,
and detecting conflicts. All operations are side-effect free.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional

from ..domain.constants import (
    MANIFEST_FILENAME,
    PLUGIN_MANIFEST_FILENAME,
    PLUGINS_DIR,
    MAX_DEPENDENCY_DEPTH,
    MAX_COMPONENTS_PER_PROFILE,
    COMPONENT_PRIORITIES,
)
from ..domain.errors import DepError, ConflictError, ValidationError
from ..adapters.logging import get_logger

logger = get_logger(__name__)


class ResolvedSpec:
    """Represents a fully resolved specification ready for planning.

    Contains all components in dependency order with their file patterns,
    capabilities, and metadata needed for installation planning.
    """

    def __init__(
        self,
        components: List[Dict],
        plugins: Dict[str, Dict],
        manifest_digest: str,
    ):
        self.components = components
        self.plugins = plugins
        self.manifest_digest = manifest_digest

    @property
    def component_names(self) -> List[str]:
        """Get list of component names in dependency order."""
        return [comp["name"] for comp in self.components]

    def get_component(self, name: str) -> Optional[Dict]:
        """Get component configuration by name."""
        for comp in self.components:
            if comp["name"] == name:
                return comp
        return None


class Resolver:
    """Dependency resolution and manifest loading."""

    def __init__(self, template_repo: Path, plugins_dir: Optional[Path] = None):
        """Initialize resolver with template and plugin locations.

        Args:
            template_repo: Path to template repository
            plugins_dir: Path to plugins directory (optional)
        """
        self.template_repo = Path(template_repo)
        self.plugins_dir = Path(plugins_dir) if plugins_dir else self.template_repo.parent / PLUGINS_DIR
        self._manifest_cache: Dict[str, Dict] = {}
        self._plugin_cache: Dict[str, Dict] = {}

    def resolve(
        self,
        manifest_path: Optional[Path] = None,
        profile: str = "standard",
        target_components: Optional[List[str]] = None,
    ) -> ResolvedSpec:
        """Resolve dependencies and create installation specification.

        Args:
            manifest_path: Path to installation manifest (auto-detect if None)
            profile: Profile name to resolve
            target_components: Specific components to include (None for all in profile)

        Returns:
            ResolvedSpec ready for planning

        Raises:
            ValidationError: If manifests are invalid
            DepError: If dependencies cannot be satisfied
            ConflictError: If components have conflicts
        """
        logger.info(f"Resolving dependencies for profile '{profile}'")

        # Load and validate main manifest
        manifest = self._load_manifest(manifest_path)

        # Load and validate plugin manifests
        plugins = self._load_plugins()

        # Get components for profile (check both base and plugin profiles)
        profile_components = self._get_profile_components(manifest, profile, plugins)

        # Filter to specific components if requested
        if target_components:
            profile_components = [
                comp for comp in profile_components
                if comp in target_components
            ]

        # Resolve dependencies
        resolved_components = self._resolve_dependencies(
            profile_components, manifest, plugins
        )

        # Check for conflicts
        self._check_conflicts(resolved_components, manifest, plugins)

        # Sort by dependency order
        ordered_components = self._sort_by_dependencies(resolved_components, manifest, plugins)

        logger.info(f"Resolved {len(ordered_components)} components in dependency order")

        return ResolvedSpec(
            components=ordered_components,
            plugins=plugins,
            manifest_digest=self._calculate_manifest_digest(manifest),
        )

    def list_profiles(self) -> List[str]:
        """List all available profiles from manifest and plugins.

        Returns:
            List of available profile names
        """
        try:
            manifest = self._load_manifest()
            plugins = self._load_plugins()
            
            # Get profiles from main manifest
            profiles = set()
            if "profiles" in manifest:
                profiles.update(manifest["profiles"].keys())
            
            # Get profiles from plugins
            for plugin_data in plugins.values():
                plugin_manifest = plugin_data["manifest"]
                if "profiles" in plugin_manifest:
                    profiles.update(plugin_manifest["profiles"].keys())
            
            return sorted(list(profiles))
        except Exception as e:
            logger.error(f"Failed to list profiles: {e}")
            return []

    def list_components(self) -> List[str]:
        """List all available components from manifest and plugins.

        Returns:
            List of available component names
        """
        try:
            manifest = self._load_manifest()
            plugins = self._load_plugins()
            
            # Get components from main manifest
            components = set()
            if "components" in manifest:
                components.update(manifest["components"].keys())
            
            # Get components from plugins
            for plugin_data in plugins.values():
                plugin_manifest = plugin_data["manifest"]
                if "components" in plugin_manifest:
                    components.update(plugin_manifest["components"].keys())
            
            return sorted(list(components))
        except Exception as e:
            logger.error(f"Failed to list components: {e}")
            return []

    def _load_manifest(self, manifest_path: Optional[Path] = None) -> Dict:
        """Load and validate installation manifest."""
        if manifest_path is None:
            # Auto-detect manifest
            manifest_path = self.template_repo / MANIFEST_FILENAME

        if not manifest_path.exists():
            raise ValidationError(
                f"Installation manifest not found: {manifest_path}",
                str(manifest_path),
                ["File does not exist"],
            )

        try:
            with manifest_path.open() as f:
                manifest = yaml.safe_load(f)

            # Basic validation
            self._validate_manifest(manifest, manifest_path)

            # Cache for future use
            self._manifest_cache[str(manifest_path)] = manifest

            return manifest

        except yaml.YAMLError as e:
            raise ValidationError(
                f"Invalid YAML in manifest: {e}",
                str(manifest_path),
                [str(e)],
            )
        except Exception as e:
            raise ValidationError(
                f"Failed to load manifest: {e}",
                str(manifest_path),
                [str(e)],
            )

    def _load_plugins(self) -> Dict[str, Dict]:
        """Load and validate all plugin manifests."""
        plugins = {}

        if not self.plugins_dir.exists():
            logger.debug(f"Plugins directory not found: {self.plugins_dir}")
            return plugins

        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            manifest_path = plugin_dir / PLUGIN_MANIFEST_FILENAME
            if not manifest_path.exists():
                continue

            try:
                with manifest_path.open() as f:
                    plugin_manifest = yaml.safe_load(f)

                # Basic validation
                self._validate_plugin_manifest(plugin_manifest, manifest_path)

                plugin_id = plugin_manifest.get("id", plugin_dir.name)
                plugins[plugin_id] = {
                    "path": plugin_dir,
                    "manifest": plugin_manifest,
                }

                logger.debug(f"Loaded plugin: {plugin_id}")

            except Exception as e:
                logger.warning(f"Failed to load plugin manifest {manifest_path}: {e}")
                continue

        logger.info(f"Loaded {len(plugins)} plugins")
        return plugins

    def _validate_manifest(self, manifest: Dict, path: Path) -> None:
        """Validate installation manifest structure."""
        errors = []

        if not isinstance(manifest, dict):
            errors.append("Manifest must be a dictionary")

        if "profiles" not in manifest:
            errors.append("Missing 'profiles' section")

        if "components" not in manifest:
            errors.append("Missing 'components' section")

        # Validate profiles
        if "profiles" in manifest:
            profiles = manifest["profiles"]
            if not isinstance(profiles, dict):
                errors.append("'profiles' must be a dictionary")
            else:
                for profile_name, profile_config in profiles.items():
                    if not isinstance(profile_config, dict):
                        errors.append(f"Profile '{profile_name}' must be a dictionary")
                    elif "components" not in profile_config:
                        errors.append(f"Profile '{profile_name}' missing 'components'")

        # Validate components
        if "components" in manifest:
            components = manifest["components"]
            if not isinstance(components, dict):
                errors.append("'components' must be a dictionary")
            else:
                for comp_name, comp_config in components.items():
                    if not isinstance(comp_config, dict):
                        errors.append(f"Component '{comp_name}' must be a dictionary")
                    elif "file_patterns" not in comp_config:
                        errors.append(f"Component '{comp_name}' missing 'file_patterns'")

        if errors:
            raise ValidationError(
                f"Invalid installation manifest: {path}",
                str(path),
                errors,
            )

    def _validate_plugin_manifest(self, manifest: Dict, path: Path) -> None:
        """Validate plugin manifest structure."""
        errors = []

        if not isinstance(manifest, dict):
            errors.append("Plugin manifest must be a dictionary")

        # Check for plugin metadata section
        if "plugin" not in manifest:
            errors.append("Missing required 'plugin' section")
        else:
            plugin_meta = manifest["plugin"]
            if not isinstance(plugin_meta, dict):
                errors.append("'plugin' section must be a dictionary")
            else:
                # Validate required fields in plugin section
                required_fields = ["name", "version"]
                for field in required_fields:
                    if field not in plugin_meta:
                        errors.append(f"Missing required field in plugin section: {field}")

        if "components" in manifest:
            components = manifest["components"]
            if not isinstance(components, dict):
                errors.append("'components' must be a dictionary")

        if errors:
            raise ValidationError(
                f"Invalid plugin manifest: {path}",
                str(path),
                errors,
            )

    def _get_profile_components(self, manifest: Dict, profile: str, plugins: Dict[str, Dict] = None) -> List[str]:
        """Get component list for a profile from manifest and plugins."""
        if plugins is None:
            plugins = {}
            
        # Collect all available profiles (base + plugin)
        all_profiles = {}
        
        # Add base profiles
        if "profiles" in manifest:
            all_profiles.update(manifest["profiles"])
        
        # Add plugin profiles
        for plugin_data in plugins.values():
            plugin_manifest = plugin_data["manifest"]
            if "profiles" in plugin_manifest:
                all_profiles.update(plugin_manifest["profiles"])
        
        if not all_profiles:
            raise ValidationError(
                "No profiles defined in manifest or plugins",
                "unknown",
                ["Missing profiles section"],
            )

        if profile not in all_profiles:
            available = list(all_profiles.keys())
            raise ValidationError(
                f"Profile '{profile}' not found. Available: {available}",
                "unknown",
                [f"Unknown profile: {profile}"],
            )

        profile_config = all_profiles[profile]
        if "components" not in profile_config:
            raise ValidationError(
                f"Profile '{profile}' has no components defined",
                "unknown",
                ["Missing components in profile"],
            )

        return profile_config["components"]

    def _resolve_dependencies(
        self,
        requested_components: List[str],
        manifest: Dict,
        plugins: Dict[str, Dict],
    ) -> List[str]:
        """Resolve all dependencies for requested components."""
        resolved = set()
        processing = set()

        def resolve_component(comp_name: str, depth: int = 0) -> None:
            if depth > MAX_DEPENDENCY_DEPTH:
                raise DepError(
                    f"Dependency depth exceeded for component '{comp_name}'",
                    comp_name,
                    circular_deps=list(processing),
                )

            if comp_name in processing:
                raise DepError(
                    f"Circular dependency detected: {comp_name}",
                    comp_name,
                    circular_deps=list(processing) + [comp_name],
                )

            if comp_name in resolved:
                return

            processing.add(comp_name)

            # Find component definition (manifest or plugin)
            comp_config = self._find_component_config(comp_name, manifest, plugins)
            if comp_config is None:
                raise DepError(
                    f"Component '{comp_name}' not found",
                    comp_name,
                    missing_deps=[comp_name],
                )

            # Resolve dependencies first
            deps = comp_config.get("dependencies", [])
            for dep in deps:
                resolve_component(dep, depth + 1)

            processing.remove(comp_name)
            resolved.add(comp_name)

        # Resolve all requested components
        for comp_name in requested_components:
            resolve_component(comp_name)

        if len(resolved) > MAX_COMPONENTS_PER_PROFILE:
            raise DepError(
                f"Too many components resolved: {len(resolved)} > {MAX_COMPONENTS_PER_PROFILE}",
                "resolver",
            )

        return list(resolved)

    def _find_component_config(
        self,
        comp_name: str,
        manifest: Dict,
        plugins: Dict[str, Dict],
    ) -> Optional[Dict]:
        """Find component configuration in manifest or plugins."""
        # Check main manifest first
        if "components" in manifest and comp_name in manifest["components"]:
            return manifest["components"][comp_name]

        # Check plugins
        for plugin_id, plugin_data in plugins.items():
            plugin_manifest = plugin_data["manifest"]
            if "components" in plugin_manifest and comp_name in plugin_manifest["components"]:
                config = plugin_manifest["components"][comp_name].copy()
                config["_plugin_id"] = plugin_id
                config["_plugin_path"] = plugin_data["path"]
                return config

        return None

    def _check_conflicts(
        self,
        components: List[str],
        manifest: Dict,
        plugins: Dict[str, Dict],
    ) -> None:
        """Check for conflicts between components."""
        # Track file patterns and capabilities
        file_claims: Dict[str, List[str]] = {}
        capability_claims: Dict[str, List[str]] = {}

        for comp_name in components:
            comp_config = self._find_component_config(comp_name, manifest, plugins)
            if comp_config is None:
                continue

            # Check file pattern conflicts
            patterns = comp_config.get("file_patterns", [])
            for pattern in patterns:
                if pattern not in file_claims:
                    file_claims[pattern] = []
                file_claims[pattern].append(comp_name)

            # Check capability conflicts
            capabilities = comp_config.get("provides", [])
            for capability in capabilities:
                if capability not in capability_claims:
                    capability_claims[capability] = []
                capability_claims[capability].append(comp_name)

        # Report conflicts
        conflicts = []
        conflicting_paths = []

        for pattern, claimants in file_claims.items():
            if len(claimants) > 1:
                conflicts.extend(claimants)
                conflicting_paths.append(pattern)

        for capability, claimants in capability_claims.items():
            if len(claimants) > 1:
                conflicts.extend(claimants)

        if conflicts:
            raise ConflictError(
                "Component conflicts detected",
                list(set(conflicts)),
                conflicting_paths,
            )

    def _sort_by_dependencies(
        self,
        components: List[str],
        manifest: Dict,
        plugins: Dict[str, Dict],
    ) -> List[Dict]:
        """Sort components by dependency order and priority."""
        # Build dependency graph
        deps_graph: Dict[str, List[str]] = {}
        comp_configs: Dict[str, Dict] = {}

        for comp_name in components:
            comp_config = self._find_component_config(comp_name, manifest, plugins)
            if comp_config:
                deps_graph[comp_name] = comp_config.get("dependencies", [])
                comp_configs[comp_name] = comp_config

        # Topological sort with priority
        sorted_components = []
        remaining = set(components)

        while remaining:
            # Find components with no unresolved dependencies
            ready = []
            for comp_name in remaining:
                deps = deps_graph.get(comp_name, [])
                if all(dep not in remaining for dep in deps):
                    priority = self._get_component_priority(comp_name, comp_configs[comp_name])
                    ready.append((priority, comp_name))

            if not ready:
                # Should not happen if dependencies are properly resolved
                remaining_list = list(remaining)
                raise DepError(
                    f"Unresolvable dependencies in components: {remaining_list}",
                    "resolver",
                    missing_deps=remaining_list,
                )

            # Sort by priority and process
            ready.sort()
            for priority, comp_name in ready:
                if comp_name in remaining:
                    sorted_components.append({
                        "name": comp_name,
                        "priority": priority,
                        **comp_configs[comp_name]
                    })
                    remaining.remove(comp_name)

        return sorted_components

    def _get_component_priority(self, comp_name: str, comp_config: Dict) -> int:
        """Get component priority for sorting."""
        # Check explicit priority
        if "priority" in comp_config:
            return comp_config["priority"]

        # Check category-based priority
        category = comp_config.get("category", "unknown")
        return COMPONENT_PRIORITIES.get(category, 100)

    def _calculate_manifest_digest(self, manifest: Dict) -> str:
        """Calculate digest of manifest for change detection."""
        from ..adapters.hashing import sha256_content
        import json

        # Create stable JSON representation
        manifest_json = json.dumps(manifest, sort_keys=True, separators=(',', ':'))
        return sha256_content(manifest_json)
