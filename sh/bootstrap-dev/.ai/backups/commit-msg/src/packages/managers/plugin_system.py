#!/usr/bin/env python3
"""
Plugin System Module
Handles plugin discovery and manifest management with enhanced schema integration
"""
import yaml
from pathlib import Path
from typing import Dict, List, Optional

from ..utils import Colors
from ..core.enhanced_plugin_discovery import EnhancedPluginDiscovery


class PluginSystem:
    """Manages plugin discovery and manifest handling with enhanced schema composition support"""

    def __init__(self, target_dir: Path):
        self.target_dir = target_dir
        self.plugins = {}

        # Plugins should come from the tool installation plugins directory
        # Path calculation: src/packages/managers -> src -> plugins
        script_dir = Path(__file__).parent.parent.parent
        self.plugins_dir = script_dir / "plugins"

        # Initialize enhanced plugin discovery
        self.enhanced_discovery = EnhancedPluginDiscovery(self.plugins_dir, target_dir)
        
        # Load plugins using enhanced discovery
        self.plugins = self.enhanced_discovery.plugins

    def discover_plugins(self) -> Dict:
        """Discover and load plugin manifests from tool installation (legacy method)"""
        # Delegate to enhanced discovery
        return self.enhanced_discovery.plugins

    def get_enabled_plugins(self) -> List[str]:
        """Get list of currently enabled plugin names."""
        return self.enhanced_discovery.get_enabled_plugins()
    
    def get_plugin_structures(self) -> List[Dict]:
        """Get plugin structure schemas for enabled plugins."""
        enabled_plugins = self.get_enabled_plugins()
        structures = []
        
        for plugin_name in enabled_plugins:
            if plugin_name in self.plugins:
                plugin_dir = self.plugins[plugin_name]['path']
                structure_file = plugin_dir / "plugin-structure.schema.yaml"
                
                if structure_file.exists():
                    try:
                        with open(structure_file, 'r') as f:
                            structure = yaml.safe_load(f)
                            structures.append(structure)
                    except Exception as e:
                        print(f"{Colors.warn('[WARN]')} Failed to load plugin structure {structure_file}: {e}")
        
        return structures
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a specific plugin."""
        success = self.enhanced_discovery.enable_plugin(plugin_name)
        if success:
            self.enhanced_discovery.save_plugin_config()
        return success
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a specific plugin."""
        success = self.enhanced_discovery.disable_plugin(plugin_name)
        if success:
            self.enhanced_discovery.save_plugin_config()
        return success
    
    def get_plugin_installation_order(self, requested_plugins: List[str] = None) -> List[str]:
        """Get plugins in dependency-resolved installation order."""
        return self.enhanced_discovery.get_plugin_installation_order(requested_plugins)
    
    def validate_plugin_selection(self, plugins: List[str]) -> Dict:
        """Validate plugin selection for conflicts and dependencies."""
        return self.enhanced_discovery.validate_plugin_selection(plugins)
    
    def get_plugin_analysis(self) -> Dict:
        """Get comprehensive plugin analysis report."""
        return self.enhanced_discovery.get_plugin_analysis()

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
