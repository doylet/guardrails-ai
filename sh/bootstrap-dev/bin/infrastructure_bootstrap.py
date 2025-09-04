#!/usr/bin/env python3
"""
Infrastructure-as-Code Bootstrap Manager
Reads installation-manifest.yaml for dynamic file discovery
NO hardcoded file lists in shell scripts!
"""

import yaml
import glob
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

class InfrastructureBootstrap:
    def __init__(self, manifest_path: str = "src/installation-manifest.yaml", template_repo: str = None, target_dir: str = "."):
        # Handle relative paths for manifest
        if not Path(manifest_path).is_absolute():
            # Look for manifest relative to current directory first
            if Path(manifest_path).exists():
                self.manifest_path = Path(manifest_path).resolve()
            else:
                # Look relative to the project root (parent of bin directory)
                bin_dir = Path(__file__).parent
                project_root = bin_dir.parent
                candidate_path = project_root / manifest_path
                if candidate_path.exists():
                    self.manifest_path = candidate_path
                else:
                    # Fallback to original path
                    self.manifest_path = Path(manifest_path).resolve()
        else:
            self.manifest_path = Path(manifest_path)

        self.target_dir = Path(target_dir)
        self.manifest = self._load_manifest()

        # Determine template repository path
        if template_repo:
            self.template_repo = Path(template_repo)
        else:
            # Get from manifest settings or use default
            if 'settings' in self.manifest and 'template_repository' in self.manifest['settings']:
                self.template_repo = self.manifest_path.parent / self.manifest['settings']['template_repository']
            else:
                self.template_repo = self.manifest_path.parent / "ai-guardrails-templates"

        self.plugins = self._discover_plugins()

    def _load_manifest(self) -> Dict:
        """Load installation manifest"""
        with open(self.manifest_path) as f:
            return yaml.safe_load(f)

    def _discover_plugins(self) -> Dict:
        """Discover and load plugin manifests"""
        plugins = {}

        # Get plugins directory from manifest settings
        plugins_dir = None
        if 'settings' in self.manifest and 'plugins_directory' in self.manifest['settings']:
            plugins_dir = Path(self.manifest_path).parent / self.manifest['settings']['plugins_directory']
        else:
            # Fallback: look for plugins in subdirectories of manifest directory
            plugins_dir = Path(self.manifest_path).parent

        # Look for plugin-manifest.yaml files in subdirectories of plugins directory
        if plugins_dir.exists():
            for plugin_manifest in plugins_dir.glob("*/plugin-manifest.yaml"):
                try:
                    with open(plugin_manifest) as f:
                        plugin_config = yaml.safe_load(f)
                        plugin_name = plugin_config['plugin']['name']
                        plugins[plugin_name] = {
                            'config': plugin_config,
                            'path': plugin_manifest.parent
                        }
                        print(f"Discovered plugin: {plugin_name}")
                except Exception as e:
                    print(f"Warning: Failed to load plugin {plugin_manifest}: {e}")

        return plugins

    def _get_merged_manifest(self) -> Dict:
        """Get manifest merged with plugin configurations"""
        merged = self.manifest.copy()

        # Merge plugin components and profiles
        for plugin_name, plugin_data in self.plugins.items():
            plugin_config = plugin_data['config']

            # Merge components
            if 'components' in plugin_config:
                merged.setdefault('components', {}).update(plugin_config['components'])

            # Merge profiles
            if 'profiles' in plugin_config:
                merged.setdefault('profiles', {}).update(plugin_config['profiles'])

        return merged

    def _is_plugin_component(self, component: str) -> bool:
        """Check if a component comes from a plugin"""
        # Check if component exists in any plugin
        for plugin_name, plugin_data in self.plugins.items():
            plugin_config = plugin_data['config']
            if 'components' in plugin_config and component in plugin_config['components']:
                return True
        return False

    def _get_plugin_path_for_component(self, component: str) -> Path:
        """Get the plugin directory path for a given component"""
        for plugin_name, plugin_data in self.plugins.items():
            plugin_config = plugin_data['config']
            if 'components' in plugin_config and component in plugin_config['components']:
                return plugin_data['path']
        return None

    def _get_plugin_name_for_component(self, component: str) -> str:
        """Get the plugin name for a given component"""
        for plugin_name, plugin_data in self.plugins.items():
            plugin_config = plugin_data['config']
            if 'components' in plugin_config and component in plugin_config['components']:
                return plugin_name
        return None

    def discover_files(self, component: str) -> List[str]:
        """Dynamically discover files based on patterns - NO hardcoding!"""
        merged_manifest = self._get_merged_manifest()

        if component not in merged_manifest['components']:
            raise ValueError(f"Unknown component: {component}")

        component_config = merged_manifest['components'][component]
        patterns = component_config['file_patterns']

        # Check if this is a plugin component
        is_plugin_component = self._is_plugin_component(component)

        discovered = []
        for pattern in patterns:
            if is_plugin_component:
                # For plugin components, find the plugin directory and search there
                plugin_path = self._get_plugin_path_for_component(component)
                if plugin_path:
                    search_path = plugin_path / pattern
                else:
                    continue
            else:
                # For base components, search in template repository
                search_path = self.template_repo / pattern

            matches = glob.glob(str(search_path), recursive=True)
            discovered.extend(matches)

        # Convert to relative paths from the appropriate base directory
        relative_files = []

        if is_plugin_component:
            plugin_path = self._get_plugin_path_for_component(component)
            base_dir = plugin_path if plugin_path else Path(self.manifest_path).parent
        else:
            base_dir = self.template_repo

        for file_path in discovered:
            if os.path.isfile(file_path):
                rel_path = os.path.relpath(file_path, base_dir)
                relative_files.append(rel_path)

        return relative_files

    def install_component(self, component: str, force: bool = False) -> bool:
        """Install a specific component"""
        try:
            merged_manifest = self._get_merged_manifest()

            if component not in merged_manifest['components']:
                raise ValueError(f"Unknown component: {component}")

            files = self.discover_files(component)
            is_plugin_component = self._is_plugin_component(component)

            print(f"Installing component: {component}")

            success = True
            for rel_file in files:
                if is_plugin_component:
                    # For plugin components, source is in the plugin directory
                    plugin_path = self._get_plugin_path_for_component(component)
                    src_path = plugin_path / rel_file if plugin_path else None
                    if not src_path:
                        print(f"  error: Could not find plugin path for component {component}")
                        success = False
                        continue
                else:
                    # For base components, source is in template repository
                    src_path = self.template_repo / rel_file

                original_target_path = self.target_dir / rel_file

                # Check if this should be merged and get actual target path
                should_merge = self._should_merge_file(src_path, original_target_path)
                target_path = self._get_merge_target_path(src_path, original_target_path) if should_merge else original_target_path

                # Create target directory if needed
                target_path.parent.mkdir(parents=True, exist_ok=True)

                if target_path.exists() and not force and not should_merge:
                    print(f"  skip (exists): {rel_file}")
                    continue

                try:
                    if should_merge:
                        self._merge_yaml_file(src_path, target_path)
                        print(f"  merged: {rel_file} -> {target_path.relative_to(self.target_dir)}")
                    else:
                        shutil.copy2(src_path, target_path)
                        print(f"  installed: {rel_file}")
                except Exception as e:
                    print(f"  error: {rel_file} - {e}")
                    success = False

            # Install pre-commit hooks if this component includes pre-commit config
            if component == 'precommit' and success:
                self._install_precommit_hooks()

            return success

        except ValueError as e:
            print(f"Error: {e}")
            return False

    def _install_precommit_hooks(self):
        """Install pre-commit hooks like the old unified script did"""
        try:
            # Install pre-commit if not already installed
            print("Installing pre-commit hooks...")
            subprocess.run([
                'python3', '-m', 'pip', 'install', '-q', 'pre-commit'
            ], check=False, cwd=self.target_dir)

            # Install the hooks
            subprocess.run([
                'pre-commit', 'install'
            ], check=False, cwd=self.target_dir)

            subprocess.run([
                'pre-commit', 'install', '-t', 'pre-push'
            ], check=False, cwd=self.target_dir)

            print("Pre-commit hooks installed")

        except Exception as e:
            print(f"Warning: Could not install pre-commit hooks: {e}")

    def _should_merge_file(self, src_path: Path, target_path: Path) -> bool:
        """Check if a file should be merged instead of copied"""
        # Special case: guardrails example files should merge into main guardrails.yaml
        if src_path.name.startswith('guardrails.') and src_path.name.endswith('.example.yaml'):
            return True

        # Merge YAML files with specific names when target exists
        merge_files = {'.ai/guardrails.yaml', '.ai/envelope.json'}
        return target_path.exists() and str(target_path).endswith(tuple(merge_files))

    def _get_merge_target_path(self, src_path: Path, original_target_path: Path) -> Path:
        """Get the actual target path for merging (may differ from original target)"""
        # Special case: guardrails example files merge into main guardrails.yaml
        if src_path.name.startswith('guardrails.') and src_path.name.endswith('.example.yaml'):
            return Path(self.target_dir) / '.ai/guardrails.yaml'

        return original_target_path

    def _merge_yaml_file(self, src_path: Path, target_path: Path):
        """Merge YAML files by combining their contents"""
        try:
            # Load existing target file
            with open(target_path) as f:
                target_data = yaml.safe_load(f) or {}

            # Load source file to merge
            with open(src_path) as f:
                source_data = yaml.safe_load(f) or {}

            # Deep merge the dictionaries
            merged_data = self._deep_merge_dict(target_data, source_data)

            # Write back the merged result
            with open(target_path, 'w') as f:
                yaml.dump(merged_data, f, default_flow_style=False, sort_keys=False)

        except Exception as e:
            # Fallback to copy if merge fails
            print(f"  merge failed, copying instead: {e}")
            shutil.copy2(src_path, target_path)

    def _deep_merge_dict(self, target: dict, source: dict) -> dict:
        """Deep merge two dictionaries"""
        result = target.copy()

        for key, value in source.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge_dict(result[key], value)
            else:
                result[key] = value

        return result

    def install_profile(self, profile: str, force: bool = False) -> bool:
        """Install a profile"""
        merged_manifest = self._get_merged_manifest()

        if profile not in merged_manifest['profiles']:
            raise ValueError(f"Unknown profile: {profile}")

        profile_config = merged_manifest['profiles'][profile]
        components = profile_config['components']

        print(f"Installing profile: {profile} ({profile_config['description']})")

        success = True
        for component in components:
            if not self.install_component(component, force):
                success = False

        return success

    def list_discovered_files(self, component: str):
        """List what files would be installed for a component"""
        try:
            files = self.discover_files(component)
            print(f"Component '{component}' would install {len(files)} files:")
            for file in sorted(files):
                print(f"  {file}")
        except ValueError as e:
            print(f"Error: {e}")

    def list_all_components(self):
        """List all available components grouped by source"""
        merged_manifest = self._get_merged_manifest()

        # Separate base components from plugin components
        base_components = {}
        plugin_components = {}

        for component, config in merged_manifest['components'].items():
            if self._is_plugin_component(component):
                # Find which plugin this component belongs to
                plugin_name = self._get_plugin_name_for_component(component)
                if plugin_name not in plugin_components:
                    plugin_components[plugin_name] = {}
                plugin_components[plugin_name][component] = config
            else:
                base_components[component] = config

        # Display base components
        if base_components:
            print("Base Components:")
            for component, config in base_components.items():
                files = self.discover_files(component)
                print(f"  {component}: {config['description']} ({len(files)} files)")

        # Display plugin components grouped by plugin
        for plugin_name, components in plugin_components.items():
            print(f"\n{plugin_name} Plugin:")
            for component, config in components.items():
                files = self.discover_files(component)
                print(f"  {component}: {config['description']} ({len(files)} files)")

    def list_all_profiles(self):
        """List all available profiles"""
        merged_manifest = self._get_merged_manifest()
        print("Available profiles:")
        for profile, config in merged_manifest['profiles'].items():
            print(f"  {profile}: {config['description']}")
            print(f"    Components: {', '.join(config['components'])}")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Infrastructure-as-Code Bootstrap Manager')
    parser.add_argument('--manifest', default='src/installation-manifest.yaml',
                       help='Installation manifest file')
    parser.add_argument('--template-repo', default=None,
                       help='Template repository path (defaults to manifest setting)')
    parser.add_argument('--target', default='.',
                       help='Target installation directory')
    parser.add_argument('--force', action='store_true',
                       help='Overwrite existing files')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Install profile
    install_parser = subparsers.add_parser('install', help='Install a profile')
    install_parser.add_argument('profile', help='Profile to install')

    # Install component
    component_parser = subparsers.add_parser('component', help='Install specific component')
    component_parser.add_argument('component', help='Component to install')

    # List commands
    subparsers.add_parser('list-components', help='List available components')
    subparsers.add_parser('list-profiles', help='List available profiles')

    # Discover what files would be installed
    discover_parser = subparsers.add_parser('discover', help='Show what files would be installed')
    discover_parser.add_argument('component', help='Component to analyze')

    args = parser.parse_args()

    try:
        bootstrap = InfrastructureBootstrap(args.manifest, args.template_repo, args.target)

        if args.command == 'install':
            success = bootstrap.install_profile(args.profile, args.force)
            exit(0 if success else 1)
        elif args.command == 'component':
            success = bootstrap.install_component(args.component, args.force)
            exit(0 if success else 1)
        elif args.command == 'list-components':
            bootstrap.list_all_components()
        elif args.command == 'list-profiles':
            bootstrap.list_all_profiles()
        elif args.command == 'discover':
            bootstrap.list_discovered_files(args.component)
        else:
            parser.print_help()

    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == '__main__':
    main()
