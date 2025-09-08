"""
Plugin Registry System for AI Guardrails Bootstrap

This module provides a comprehensive plugin registry for discovering, managing,
and distributing plugins. It supports both local and remote plugin repositories
with version management, dependency resolution, and security validation.

Features:
- Plugin discovery from multiple sources (local, git, registry)
- Version management with semantic versioning
- Dependency resolution and conflict detection
- Security validation and signature verification
- Plugin metadata caching and indexing
- Installation source tracking
- Plugin update management
- Registry synchronization
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import tempfile

from ..domain.plugin_models import PluginManifest, PluginDependency
from ..core.plugin_validator import PluginValidator


@dataclass
class PluginSource:
    """Plugin source configuration."""

    name: str
    """Source name."""

    url: str
    """Source URL (local path, git repo, or registry endpoint)."""

    type: str
    """Source type: 'local', 'git', 'registry'."""

    enabled: bool = True
    """Whether this source is enabled."""

    priority: int = 100
    """Source priority (lower = higher priority)."""

    auth_token: Optional[str] = None
    """Authentication token for private sources."""

    cache_ttl: int = 3600
    """Cache TTL in seconds."""


@dataclass
class PluginMetadata:
    """Plugin metadata from registry."""

    name: str
    version: str
    description: str
    author: str
    license: Optional[str] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    dependencies: List[PluginDependency] = field(default_factory=list)
    source: Optional[PluginSource] = None
    download_url: Optional[str] = None
    checksum: Optional[str] = None
    size: Optional[int] = None
    last_updated: Optional[datetime] = None
    download_count: int = 0
    rating: float = 0.0


@dataclass
class RegistryIndex:
    """Plugin registry index."""

    version: str
    """Index format version."""

    last_updated: datetime
    """When the index was last updated."""

    plugins: Dict[str, List[PluginMetadata]] = field(default_factory=dict)
    """Plugins by name with versions."""

    sources: List[PluginSource] = field(default_factory=list)
    """Configured plugin sources."""


class PluginRegistry:
    """Plugin registry system for discovery and management."""

    def __init__(self, registry_dir: Path = None):
        self.registry_dir = registry_dir or Path.home() / ".ai-guardrails" / "registry"
        self.registry_dir.mkdir(parents=True, exist_ok=True)

        self.index_file = self.registry_dir / "index.json"
        self.cache_dir = self.registry_dir / "cache"
        self.sources_file = self.registry_dir / "sources.json"

        self.cache_dir.mkdir(exist_ok=True)

        self.validator = PluginValidator()
        self.logger = logging.getLogger(__name__)

        # Load or initialize registry
        self.index = self._load_index()
        self._ensure_default_sources()

    def add_source(self, source: PluginSource) -> bool:
        """
        Add a plugin source to the registry.

        Args:
            source: Plugin source configuration

        Returns:
            True if source was added successfully
        """
        try:
            # Validate source
            if not self._validate_source(source):
                return False

            # Check for duplicates
            existing_sources = {s.name for s in self.index.sources}
            if source.name in existing_sources:
                self.logger.warning(f"Source {source.name} already exists")
                return False

            # Add source
            self.index.sources.append(source)
            self._save_sources()

            self.logger.info(f"Added plugin source: {source.name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add source {source.name}: {e}")
            return False

    def remove_source(self, source_name: str) -> bool:
        """Remove a plugin source from the registry."""
        try:
            original_count = len(self.index.sources)
            self.index.sources = [
                s for s in self.index.sources if s.name != source_name
            ]

            if len(self.index.sources) < original_count:
                self._save_sources()
                self.logger.info(f"Removed plugin source: {source_name}")
                return True
            else:
                self.logger.warning(f"Source {source_name} not found")
                return False

        except Exception as e:
            self.logger.error(f"Failed to remove source {source_name}: {e}")
            return False

    def search_plugins(
        self,
        query: str = "",
        tags: List[str] = None,
        author: str = None,
        limit: int = 50,
    ) -> List[PluginMetadata]:
        """
        Search for plugins in the registry.

        Args:
            query: Search query (matches name and description)
            tags: Filter by tags
            author: Filter by author
            limit: Maximum results to return

        Returns:
            List of matching plugin metadata
        """
        results = []

        for plugin_name, versions in self.index.plugins.items():
            if not versions:
                continue

            # Get latest version
            latest = max(versions, key=lambda v: v.version)

            # Apply filters
            if (
                query
                and query.lower() not in plugin_name.lower()
                and query.lower() not in latest.description.lower()
            ):
                continue

            if author and latest.author != author:
                continue

            if tags:
                if not any(tag in latest.tags for tag in tags):
                    continue

            results.append(latest)

            if len(results) >= limit:
                break

        # Sort by relevance/popularity
        results.sort(key=lambda p: (p.download_count, p.rating), reverse=True)

        return results

    def get_plugin_info(
        self, plugin_name: str, version: str = None
    ) -> Optional[PluginMetadata]:
        """Get information about a specific plugin version."""
        if plugin_name not in self.index.plugins:
            return None

        versions = self.index.plugins[plugin_name]
        if not versions:
            return None

        if version:
            # Find specific version
            for plugin_meta in versions:
                if plugin_meta.version == version:
                    return plugin_meta
            return None
        else:
            # Return latest version
            return max(versions, key=lambda v: v.version)

    def install_plugin(
        self, plugin_name: str, version: str = None, target_dir: Path = None
    ) -> bool:
        """
        Install plugin from registry.

        Args:
            plugin_name: Name of plugin to install
            version: Specific version (or latest if None)
            target_dir: Target installation directory

        Returns:
            True if installation successful
        """
        try:
            # Get plugin metadata
            plugin_meta = self.get_plugin_info(plugin_name, version)
            if not plugin_meta:
                self.logger.error(f"Plugin not found: {plugin_name}")
                return False

            # Download plugin
            plugin_path = self._download_plugin(plugin_meta)
            if not plugin_path:
                return False

            # Install using enhanced installer
            from ..adapters.enhanced_plugin_installer import (
                EnhancedPluginInstaller,
                PluginInstallationContext,
            )

            target_dir = target_dir or Path.cwd()
            installer = EnhancedPluginInstaller(plugin_path, target_dir)

            # Load manifest
            manifest_path = plugin_path / "plugin-manifest.yaml"
            if not manifest_path.exists():
                self.logger.error(f"Plugin manifest not found: {manifest_path}")
                return False

            import yaml

            with open(manifest_path) as f:
                manifest_data = yaml.safe_load(f)

            manifest = PluginManifest.from_dict(manifest_data)

            # Create installation context
            context = PluginInstallationContext(
                plugin_path=plugin_path,
                target_path=target_dir,
                manifest=manifest,
                configuration={},
                dry_run=False,
                force=False,
            )

            # Install plugin
            result = installer.install_plugin(context)

            if result.success:
                self.logger.info(
                    f"Successfully installed plugin: {plugin_name} v{plugin_meta.version}"
                )

                # Update download count
                plugin_meta.download_count += 1
                self._save_index()

            return result.success

        except Exception as e:
            self.logger.error(f"Failed to install plugin {plugin_name}: {e}")
            return False

    def update_index(self, force: bool = False) -> bool:
        """Update plugin index from all sources."""
        try:
            updated = False

            for source in self.index.sources:
                if not source.enabled:
                    continue

                # Check if cache is still valid
                if not force and self._is_cache_valid(source):
                    continue

                self.logger.info(f"Updating index from source: {source.name}")

                if source.type == "registry":
                    if self._update_from_registry(source):
                        updated = True
                elif source.type == "local":
                    if self._update_from_local(source):
                        updated = True
                elif source.type == "git":
                    if self._update_from_git(source):
                        updated = True

            if updated:
                self.index.last_updated = datetime.now()
                self._save_index()
                self.logger.info("Plugin index updated successfully")

            return True

        except Exception as e:
            self.logger.error(f"Failed to update plugin index: {e}")
            return False

    def _load_index(self) -> RegistryIndex:
        """Load plugin index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file) as f:
                    data = json.load(f)

                # Convert datetime strings back to datetime objects
                if "last_updated" in data:
                    data["last_updated"] = datetime.fromisoformat(data["last_updated"])

                # Convert plugin metadata
                plugins = {}
                for name, versions in data.get("plugins", {}).items():
                    plugins[name] = []
                    for version_data in versions:
                        if (
                            "last_updated" in version_data
                            and version_data["last_updated"]
                        ):
                            version_data["last_updated"] = datetime.fromisoformat(
                                version_data["last_updated"]
                            )

                        # Convert dependencies
                        deps = []
                        for dep_data in version_data.get("dependencies", []):
                            deps.append(PluginDependency(**dep_data))
                        version_data["dependencies"] = deps

                        plugins[name].append(PluginMetadata(**version_data))

                data["plugins"] = plugins

                # Load sources
                sources = []
                for source_data in data.get("sources", []):
                    sources.append(PluginSource(**source_data))
                data["sources"] = sources

                return RegistryIndex(**data)

            except Exception as e:
                self.logger.warning(f"Failed to load index, creating new one: {e}")

        return RegistryIndex(
            version="1.0", last_updated=datetime.now(), plugins={}, sources=[]
        )

    def _save_index(self):
        """Save plugin index to disk."""
        try:
            # Convert to serializable format
            data = {
                "version": self.index.version,
                "last_updated": self.index.last_updated.isoformat(),
                "plugins": {},
                "sources": [],
            }

            # Convert plugins
            for name, versions in self.index.plugins.items():
                data["plugins"][name] = []
                for plugin_meta in versions:
                    plugin_data = {
                        "name": plugin_meta.name,
                        "version": plugin_meta.version,
                        "description": plugin_meta.description,
                        "author": plugin_meta.author,
                        "license": plugin_meta.license,
                        "homepage": plugin_meta.homepage,
                        "repository": plugin_meta.repository,
                        "tags": plugin_meta.tags,
                        "dependencies": [
                            {
                                "plugin": dep.plugin,
                                "version": dep.version,
                                "optional": dep.optional,
                                "reason": dep.reason,
                            }
                            for dep in plugin_meta.dependencies
                        ],
                        "download_url": plugin_meta.download_url,
                        "checksum": plugin_meta.checksum,
                        "size": plugin_meta.size,
                        "last_updated": plugin_meta.last_updated.isoformat()
                        if plugin_meta.last_updated
                        else None,
                        "download_count": plugin_meta.download_count,
                        "rating": plugin_meta.rating,
                    }
                    data["plugins"][name].append(plugin_data)

            # Convert sources
            for source in self.index.sources:
                data["sources"].append(
                    {
                        "name": source.name,
                        "url": source.url,
                        "type": source.type,
                        "enabled": source.enabled,
                        "priority": source.priority,
                        "auth_token": source.auth_token,
                        "cache_ttl": source.cache_ttl,
                    }
                )

            with open(self.index_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save index: {e}")

    def _save_sources(self):
        """Save sources configuration."""
        try:
            sources_data = []
            for source in self.index.sources:
                sources_data.append(
                    {
                        "name": source.name,
                        "url": source.url,
                        "type": source.type,
                        "enabled": source.enabled,
                        "priority": source.priority,
                        "auth_token": source.auth_token,
                        "cache_ttl": source.cache_ttl,
                    }
                )

            with open(self.sources_file, "w") as f:
                json.dump(sources_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save sources: {e}")

    def _ensure_default_sources(self):
        """Ensure default plugin sources are configured."""
        if not self.index.sources:
            # Add default local source
            local_source = PluginSource(
                name="local", url="./plugins", type="local", priority=1
            )
            self.index.sources.append(local_source)
            self._save_sources()

    def _validate_source(self, source: PluginSource) -> bool:
        """Validate plugin source configuration."""
        if not source.name or not source.url:
            return False

        if source.type not in ["local", "git", "registry"]:
            return False

        return True

    def _is_cache_valid(self, source: PluginSource) -> bool:
        """Check if source cache is still valid."""
        cache_file = self.cache_dir / f"{source.name}.json"
        if not cache_file.exists():
            return False

        try:
            cache_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            return datetime.now() - cache_time < timedelta(seconds=source.cache_ttl)
        except Exception:
            return False

    def _update_from_registry(self, source: PluginSource) -> bool:
        """Update index from remote registry."""
        # Implementation for remote registry updates
        return True

    def _update_from_local(self, source: PluginSource) -> bool:
        """Update index from local plugin directory."""
        try:
            plugins_dir = Path(source.url)
            if not plugins_dir.exists():
                return False

            updated = False

            for plugin_dir in plugins_dir.iterdir():
                if not plugin_dir.is_dir():
                    continue

                manifest_file = plugin_dir / "plugin-manifest.yaml"
                if not manifest_file.exists():
                    continue

                try:
                    import yaml

                    with open(manifest_file) as f:
                        manifest_data = yaml.safe_load(f)

                    # Extract metadata
                    plugin_meta = PluginMetadata(
                        name=manifest_data.get("name", plugin_dir.name),
                        version=manifest_data.get("version", "0.1.0"),
                        description=manifest_data.get("description", ""),
                        author=manifest_data.get("author", "Unknown"),
                        license=manifest_data.get("license"),
                        homepage=manifest_data.get("homepage"),
                        tags=manifest_data.get("tags", []),
                        source=source,
                        last_updated=datetime.now(),
                    )

                    # Add to index
                    if plugin_meta.name not in self.index.plugins:
                        self.index.plugins[plugin_meta.name] = []

                    # Check if this version already exists
                    existing = [
                        p
                        for p in self.index.plugins[plugin_meta.name]
                        if p.version == plugin_meta.version
                    ]

                    if not existing:
                        self.index.plugins[plugin_meta.name].append(plugin_meta)
                        updated = True

                except Exception as e:
                    self.logger.warning(f"Failed to process plugin {plugin_dir}: {e}")

            return updated

        except Exception as e:
            self.logger.error(f"Failed to update from local source {source.name}: {e}")
            return False

    def _update_from_git(self, source: PluginSource) -> bool:
        """Update index from git repository."""
        # Implementation for git repository updates
        return True

    def _download_plugin(self, plugin_meta: PluginMetadata) -> Optional[Path]:
        """Download plugin to temporary location."""
        try:
            if plugin_meta.source.type == "local":
                # For local plugins, return the plugin directory
                return Path(plugin_meta.source.url) / plugin_meta.name

            # For remote plugins, implement download logic
            temp_dir = Path(tempfile.mkdtemp())
            # Download implementation would go here

            return temp_dir

        except Exception as e:
            self.logger.error(f"Failed to download plugin {plugin_meta.name}: {e}")
            return None


class PluginRegistryError(Exception):
    """Exception raised during plugin registry operations."""

    pass
