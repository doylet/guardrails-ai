#!/usr/bin/env python3
"""
Plugin System Module
Handles plugin discovery and manifest management
"""
import yaml
from pathlib import Path
from typing import Dict

from ..utils import Colors


class PluginSystem:
    """Manages plugin discovery and manifest handling"""

    def __init__(self, target_dir: Path):
        self.target_dir = target_dir
        self.plugins = {}

        # Plugins should come from the tool installation plugins directory
        script_dir = Path(__file__).parent.parent.parent / "bin"
        self.plugins_dir = script_dir.parent / "src" / "plugins"

        # Load plugins
        self.plugins = self.discover_plugins()

    def discover_plugins(self) -> Dict:
        """Discover and load plugin manifests from tool installation"""
        plugins = {}

        # Look for plugin-manifest.yaml files only in plugins directory
        if self.plugins_dir.exists():
            for plugin_dir in self.plugins_dir.iterdir():
                if plugin_dir.is_dir():
                    manifest_file = plugin_dir / "plugin-manifest.yaml"
                    if manifest_file.exists():
                        try:
                            with open(manifest_file) as f:
                                manifest = yaml.safe_load(f)
                                plugin_name = manifest.get('name', plugin_dir.name)
                                plugins[plugin_name] = {
                                    'path': plugin_dir,
                                    'manifest': manifest
                                }
                        except Exception as e:
                            print(f"{Colors.warn('[WARN]')} Failed to load plugin manifest {manifest_file}: {e}")

        return plugins

    def get_merged_manifest(self, base_manifest: Dict) -> Dict:
        """Get manifest merged with plugin configurations"""
        merged = base_manifest.copy()

        # Merge plugin components and profiles
        for plugin_name, plugin_data in self.plugins.items():
            plugin_manifest = plugin_data['manifest']

            # Merge components
            if 'components' in plugin_manifest:
                if 'components' not in merged:
                    merged['components'] = {}
                merged['components'].update(plugin_manifest['components'])

            # Merge profiles
            if 'profiles' in plugin_manifest:
                if 'profiles' not in merged:
                    merged['profiles'] = {}
                merged['profiles'].update(plugin_manifest['profiles'])

        return merged

    def is_plugin_component(self, component: str) -> bool:
        """Check if a component comes from a plugin"""
        # Check if component exists in any plugin
        for plugin_name, plugin_data in self.plugins.items():
            plugin_manifest = plugin_data['manifest']
            if 'components' in plugin_manifest and component in plugin_manifest['components']:
                return True
        return False

    def get_plugin_path_for_component(self, component: str) -> Path:
        """Get the plugin directory path for a given component"""
        for plugin_name, plugin_data in self.plugins.items():
            plugin_manifest = plugin_data['manifest']
            if 'components' in plugin_manifest and component in plugin_manifest['components']:
                return plugin_data['path']
        return None

    def get_plugin_name_for_component(self, component: str) -> str:
        """Get the plugin name for a given component"""
        for plugin_name, plugin_data in self.plugins.items():
            plugin_manifest = plugin_data['manifest']
            if 'components' in plugin_manifest and component in plugin_manifest['components']:
                return plugin_name
        return None

    def list_plugin_components(self) -> Dict[str, Dict]:
        """List all components grouped by plugin"""
        plugin_components = {}

        for plugin_name, plugin_data in self.plugins.items():
            plugin_manifest = plugin_data['manifest']
            if 'components' in plugin_manifest:
                plugin_components[plugin_name] = plugin_manifest['components']

        return plugin_components

    def get_all_plugins(self) -> Dict:
        """Get all discovered plugins"""
        return self.plugins
