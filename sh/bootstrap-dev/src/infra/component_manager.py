#!/usr/bin/env python3
"""
Component Manager Module
Handles component discovery, installation, and file operations
"""
import shutil
from pathlib import Path
from typing import Dict, List
from glob import glob

from .utils import Colors
from .plugin_system import PluginSystem
from .config_manager import ConfigManager
from .presenters import ComponentPresenter


class ComponentManager:
    """Manages component operations and file handling"""

    def __init__(self, target_dir: Path, template_repo: Path, plugin_system: PluginSystem):
        self.target_dir = target_dir
        self.template_repo = template_repo
        self.plugin_system = plugin_system
        self.config_manager = ConfigManager(target_dir)

    def discover_files(self, component: str, manifest: Dict, debug: bool = False) -> List[str]:
        """Dynamically discover files based on patterns - NO hardcoding!"""
        if component not in manifest['components']:
            raise ValueError(f"Unknown component: {component}")

        component_config = manifest['components'][component]
        patterns = component_config['file_patterns']

        if debug:
            print(f"Component: {component}")
            print(f"Patterns: {patterns}")

        # Check if this is a plugin component
        is_plugin_component = self.plugin_system.is_plugin_component(component)

        discovered = []
        for pattern in patterns:
            if is_plugin_component:
                plugin_path = self.plugin_system.get_plugin_path_for_component(component)
                if plugin_path:
                    search_pattern = str(plugin_path / pattern)
                    discovered.extend(Path(f) for f in glob(search_pattern, recursive=True))
            else:
                search_pattern = str(self.template_repo / pattern)
                discovered.extend(Path(f) for f in glob(search_pattern, recursive=True))

        # Convert to relative paths from the appropriate base directory
        relative_files = []

        if is_plugin_component:
            plugin_path = self.plugin_system.get_plugin_path_for_component(component)
            if plugin_path:
                relative_files = [str(f.relative_to(plugin_path)) for f in discovered if f.is_file()]
        else:
            relative_files = [str(f.relative_to(self.template_repo)) for f in discovered if f.is_file()]

        if debug:
            print(f"Discovered files: {relative_files}")

        return relative_files

    def debug_discover(self, component: str, manifest: Dict) -> None:
        """Debug component file discovery with verbose output"""
        try:
            files = self.discover_files(component, manifest, debug=True)
            print(f"Discovered {len(files)} files:")
            for file in sorted(files):
                print(f"  {file}")
        except Exception as e:
            print(f"Error: {e}")

    def install_component(self, component: str, manifest: Dict, force: bool = False) -> bool:
        """Install a specific component"""
        try:
            files = self.discover_files(component, manifest)
            if not files:
                print(f"{Colors.warn('[WARN]')} No files found for component: {component}")
                return False

            print(f"Installing component: {component} ({len(files)} files)")

            success = True
            for rel_file in files:
                if not self._install_single_file(component, rel_file, force, manifest):
                    success = False

            if success:
                # Post-installation customization for specific components
                if component == 'precommit':
                    self.config_manager.customize_precommit_config()
                    self.config_manager.install_precommit_hooks()

            return success

        except ValueError as e:
            print(f"{Colors.error('[ERROR]')} {e}")
            return False

    def _install_single_file(self, component: str, rel_file: str, force: bool, manifest: Dict) -> bool:
        """Install a single file for a component"""
        try:
            # Apply target prefix stripping if configured
            target_rel_file = self._apply_target_prefix_stripping(component, rel_file, manifest)

            # Determine source and target paths
            is_plugin_component = self.plugin_system.is_plugin_component(component)

            if is_plugin_component:
                plugin_path = self.plugin_system.get_plugin_path_for_component(component)
                src_path = plugin_path / rel_file
            else:
                src_path = self.template_repo / rel_file

            target_path = self.target_dir / target_rel_file

            # Check if we should merge or copy
            should_merge = self._should_merge_file(src_path, target_path)

            if should_merge:
                # Get the actual merge target (may be different for example files)
                merge_target_path = self._get_merge_target_path(src_path, target_path)
                print(f"  merging: {rel_file} -> {merge_target_path.relative_to(self.target_dir)}")

                # Create directory if needed
                merge_target_path.parent.mkdir(parents=True, exist_ok=True)

                # Merge the file
                if src_path.suffix in ['.yaml', '.yml', '.json']:
                    self.config_manager.merge_yaml_file(src_path, merge_target_path)
                else:
                    shutil.copy2(src_path, merge_target_path)
            elif target_path.exists() and not force:
                print(f"  skipping: {target_rel_file} (already exists)")
            else:
                action = "overwriting" if target_path.exists() else "copying"
                print(f"  {action}: {target_rel_file}")

                # Create directory if needed
                target_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy the file
                shutil.copy2(src_path, target_path)

            return True

        except Exception as e:
            print(f"  {Colors.error('[ERROR]')} Failed to install {rel_file}: {e}")
            return False

    def _apply_target_prefix_stripping(self, component: str, rel_file: str, manifest: Dict) -> str:
        """Apply target_prefix stripping if configured for component"""
        if component not in manifest['components']:
            return rel_file

        component_config = manifest['components'][component]
        target_prefix = component_config.get('target_prefix', '')

        if target_prefix and rel_file.startswith(target_prefix):
            return rel_file[len(target_prefix):]

        return rel_file

    def _should_merge_file(self, src_path: Path, target_path: Path) -> bool:
        """Check if a file should be merged instead of copied"""
        # First check if files are identical - if so, no merge needed
        if target_path.exists():
            try:
                with open(src_path, 'rb') as f1, open(target_path, 'rb') as f2:
                    if f1.read() == f2.read():
                        return False  # Files are identical, no merge needed
            except Exception:
                pass  # Fall through to merge logic

        # Special case: example files should merge/rename to main files
        if src_path.name.startswith('guardrails.') and src_path.name.endswith('.example.yaml'):
            return True
        if src_path.name.endswith('.example.yaml') or src_path.name.endswith('.yaml.example'):
            return True

        # Do NOT merge regular (non-example) files when target already exists
        # This preserves user customizations
        return False

    def _get_merge_target_path(self, src_path: Path, original_target_path: Path) -> Path:
        """Get the actual target path for merging (may differ from original target)"""
        # Special case: guardrails example files merge into main guardrails.yaml
        if src_path.name.startswith('guardrails.') and src_path.name.endswith('.example.yaml'):
            return original_target_path.parent / 'guardrails.yaml'

        # General case: .example files should install without .example suffix
        if src_path.name.endswith('.example.yaml'):
            new_name = src_path.name.replace('.example.yaml', '.yaml')
            return original_target_path.parent / new_name
        if src_path.name.endswith('.yaml.example'):
            new_name = src_path.name.replace('.yaml.example', '.yaml')
            return original_target_path.parent / new_name

        return original_target_path

    def list_discovered_files(self, component: str, manifest: Dict):
        """List what files would be installed for a component"""
        try:
            files = self.discover_files(component, manifest)
            ComponentPresenter.list_discovered_files(component, files)
        except ValueError as e:
            print(f"Error: {e}")

    def list_all_components(self, manifest: Dict):
        """List all available components grouped by source"""
        ComponentPresenter.list_all_components(manifest, self.plugin_system)
