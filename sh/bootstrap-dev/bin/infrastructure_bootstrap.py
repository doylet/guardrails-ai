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
import sys
from pathlib import Path
from typing import Dict, List

class InfrastructureBootstrap:
    def __init__(self, target_dir: Path = None):
        """Initialize the bootstrap system"""
        self.target_dir = Path(target_dir) if target_dir else Path.cwd()
        self.manifest_path = self.target_dir / "src" / "installation-manifest.yaml"
        self.state_path = self.target_dir / ".ai-guardrails-state.yaml"
        self.template_repo = self.target_dir / "src" / "ai-guardrails-templates"
        self.plugins = {}

        # Load manifest
        self.manifest = self._load_manifest()

        # Discover plugins
        self._discover_plugins()

    def _load_manifest(self) -> Dict:
        """Load installation manifest or create default if it doesn't exist"""
        if not self.manifest_path.exists():
            # For fresh projects, use the template manifest from this repository
            # Look for the manifest in the current repository structure
            template_manifest_path = None
            
            # Try to find the template manifest in common locations
            search_paths = [
                Path(__file__).parent.parent / "src" / "installation-manifest.yaml",  # When running from this repo
                self.target_dir / "src" / "installation-manifest.yaml",  # Target location
            ]
            
            for path in search_paths:
                if path.exists():
                    template_manifest_path = path
                    break
            
            if template_manifest_path:
                # Load from template
                with open(template_manifest_path) as f:
                    return yaml.safe_load(f)
            else:
                # Create minimal default manifest for bootstrapping
                return self._create_minimal_manifest()
        
        with open(self.manifest_path) as f:
            return yaml.safe_load(f)

    def _create_minimal_manifest(self) -> Dict:
        """Create a minimal manifest for bootstrapping"""
        return {
            'version': '1.0.0',
            'name': 'ai-guardrails-installation',
            'components': {
                'core': {
                    'description': 'Core AI guardrails configuration',
                    'file_patterns': ['.ai/*.yaml', '.ai/*.json']
                }
            },
            'profiles': {
                'minimal': {
                    'description': 'Minimal profile for bootstrapping',
                    'components': ['core']
                },
                'standard': {
                    'description': 'Standard profile',
                    'components': ['core']
                }
            },
            'settings': {
                'template_source_directory': 'src/ai-guardrails-templates',
                'plugin_directories': ['src/plugins']
            }
        }

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

    def _load_state(self) -> Dict:
        """Load the installation state file"""
        if not self.state_path.exists():
            return {
                'version': '1.0',
                'installed_profile': None,
                'installed_components': [],
                'installation_history': []
            }

        try:
            with open(self.state_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not load state file: {e}")
            return {
                'version': '1.0',
                'installed_profile': None,
                'installed_components': [],
                'installation_history': []
            }

    def _save_state(self, state: Dict):
        """Save the installation state file"""
        try:
            with open(self.state_path, 'w') as f:
                yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"Warning: Could not save state file: {e}")

    def _update_state_for_profile(self, profile: str, components: List[str]):
        """Update state file after profile installation"""
        from datetime import datetime

        state = self._load_state()
        state['installed_profile'] = profile
        state['installed_components'] = list(set(state.get('installed_components', []) + components))

        # Add to history
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': 'install_profile',
            'profile': profile,
            'components': components
        }
        state.setdefault('installation_history', []).append(history_entry)

        self._save_state(state)

    def _update_state_for_component(self, component: str):
        """Update state file after component installation"""
        from datetime import datetime

        state = self._load_state()
        if component not in state.get('installed_components', []):
            state.setdefault('installed_components', []).append(component)

            # Add to history
            history_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': 'install_component',
                'component': component
            }
            state.setdefault('installation_history', []).append(history_entry)

            self._save_state(state)

    def show_state(self):
        """Show current installation state"""
        state = self._load_state()

        print("🔍 AI Guardrails Installation State")
        print("=" * 50)

        if state.get('installed_profile'):
            print(f"📦 Profile: {state['installed_profile']}")
        else:
            print("📦 Profile: Not set (manual installation)")

        installed_components = state.get('installed_components', [])
        if installed_components:
            print(f"🧩 Components ({len(installed_components)}):")
            for component in sorted(installed_components):
                print(f"  • {component}")
        else:
            print("🧩 Components: None tracked (run 'init' to establish state)")

        history = state.get('installation_history', [])
        if history:
            print(f"\n📋 Installation History ({len(history)} entries):")
            for entry in history[-5:]:  # Show last 5 entries
                timestamp = entry.get('timestamp', 'Unknown')
                action = entry.get('action', 'Unknown')
                if action == 'install_profile':
                    print(f"  • {timestamp}: Installed profile '{entry.get('profile')}' with {len(entry.get('components', []))} components")
                elif action == 'install_component':
                    print(f"  • {timestamp}: Installed component '{entry.get('component')}'")
            if len(history) > 5:
                print(f"  ... and {len(history) - 5} more entries")

        print()

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

            # Update state for successful individual component installation
            if success:
                self._update_state_for_component(component)

            return success

        except ValueError as e:
            print(f"Error: {e}")
            return False

    def _customize_precommit_config(self):
        """Customize .pre-commit-config.yaml based on guardrails.yaml settings"""
        guardrails_path = self.target_dir / ".ai" / "guardrails.yaml"
        precommit_path = self.target_dir / ".pre-commit-config.yaml"
        
        if not guardrails_path.exists() or not precommit_path.exists():
            return
        
        try:
            # Load guardrails config
            with open(guardrails_path, 'r') as f:
                guardrails_config = yaml.safe_load(f) or {}
            
            # Load current pre-commit config
            with open(precommit_path, 'r') as f:
                precommit_config = yaml.safe_load(f) or {}
            
            # Check if there's a precommit configuration section
            precommit_settings = guardrails_config.get('precommit', {})
            disabled_hooks = precommit_settings.get('disabled_hooks', [])
            disabled_languages = precommit_settings.get('disabled_languages', [])
            
            if not disabled_hooks and not disabled_languages:
                return  # Nothing to customize
            
            # Process repositories and hooks
            updated = False
            for repo in precommit_config.get('repos', []):
                if repo.get('repo') == 'local':
                    # Filter out disabled hooks
                    original_hooks = repo.get('hooks', [])
                    filtered_hooks = []
                    
                    for hook in original_hooks:
                        hook_id = hook.get('id', '')
                        hook_name = hook.get('name', '')
                        hook_entry = hook.get('entry', '')
                        
                        # Check if hook should be disabled
                        should_disable = False
                        
                        # Disable by hook ID
                        if hook_id in disabled_hooks:
                            should_disable = True
                            print(f"  Disabling pre-commit hook: {hook_id}")
                        
                        # Disable by language (check if hook name, ID, or entry contains language)
                        for lang in disabled_languages:
                            lang_lower = lang.lower()
                            if (lang_lower in hook_name.lower() or 
                                lang_lower in hook_id.lower() or
                                lang_lower in hook_entry.lower()):
                                should_disable = True
                                print(f"  Disabling {lang} hook: {hook_id} ({hook_name})")
                                break
                        
                        if not should_disable:
                            filtered_hooks.append(hook)
                        else:
                            updated = True
                    
                    repo['hooks'] = filtered_hooks
            
            # Save updated config if changes were made
            if updated:
                with open(precommit_path, 'w') as f:
                    yaml.dump(precommit_config, f, default_flow_style=False, sort_keys=False)
                print(f"  Customized .pre-commit-config.yaml based on guardrails settings")
            
        except Exception as e:
            print(f"Warning: Could not customize pre-commit config: {e}")

    def _install_precommit_hooks(self):
        """Install pre-commit hooks like the old unified script did"""
        try:
            # First customize the config based on guardrails.yaml settings
            self._customize_precommit_config()
            
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
        installed_components = []

        for component in components:
            if self.install_component(component, force):
                installed_components.append(component)
            else:
                success = False

        # Update state file if any components were installed
        if installed_components:
            self._update_state_for_profile(profile, installed_components)

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

    def doctor(self, focus: str = "all") -> bool:
        """Diagnostic workflow - validate installation integrity"""
        print("🔍 AI Guardrails Doctor - Installation Diagnostics")
        print("=" * 50)

        issues_found = 0
        merged_manifest = self._get_merged_manifest()

        if focus == "yaml" or focus == "all":
            issues_found += self._doctor_yaml_structure()

        if focus == "all":
            issues_found += self._doctor_file_integrity()
            issues_found += self._doctor_component_status()
            issues_found += self._doctor_environment()

        print("\n" + "=" * 50)
        if issues_found == 0:
            print("✅ All checks passed - installation is healthy!")
            return True
        else:
            print(f"⚠️  Found {issues_found} issues - run 'ensure --apply' to fix")
            return False

    def _doctor_yaml_structure(self) -> int:
        """Validate YAML file structure and content"""
        print("\n📋 YAML Structure Check:")
        issues = 0

        yaml_files = [
            (".ai/guardrails.yaml", "AI guardrails configuration"),
            (".ai/envelope.json", "Copilot envelope schema"),
            (".pre-commit-config.yaml", "Pre-commit hooks configuration")
        ]

        for file_path, description in yaml_files:
            full_path = self.target_dir / file_path
            if full_path.exists():
                try:
                    if file_path.endswith('.yaml'):
                        with open(full_path) as f:
                            yaml.safe_load(f)
                    elif file_path.endswith('.json'):
                        import json
                        with open(full_path) as f:
                            json.load(f)
                    print(f"  ✅ {file_path}: Valid syntax")
                except Exception as e:
                    print(f"  ❌ {file_path}: Invalid syntax - {e}")
                    issues += 1
            else:
                print(f"  ⚠️  {file_path}: Missing ({description})")
                issues += 1

        return issues

    def _doctor_file_integrity(self) -> int:
        """Check if all expected files are present"""
        print("\n📁 File Integrity Check:")
        issues = 0
        merged_manifest = self._get_merged_manifest()

        for component, config in merged_manifest['components'].items():
            try:
                files = self.discover_files(component)
                missing_files = []

                for rel_file in files:
                    # Determine source path
                    if self._is_plugin_component(component):
                        plugin_path = self._get_plugin_path_for_component(component)
                        src_path = plugin_path / rel_file if plugin_path else None
                    else:
                        src_path = self.template_repo / rel_file

                    # Check target path
                    target_path = self.target_dir / rel_file
                    if src_path and src_path.exists() and not target_path.exists():
                        missing_files.append(rel_file)

                if missing_files:
                    print(f"  ⚠️  {component}: Missing {len(missing_files)} files")
                    for missing in missing_files[:3]:  # Show first 3
                        print(f"    - {missing}")
                    if len(missing_files) > 3:
                        print(f"    ... and {len(missing_files) - 3} more")
                    issues += len(missing_files)
                else:
                    print(f"  ✅ {component}: All files present")

            except Exception as e:
                print(f"  ❌ {component}: Cannot check - {e}")
                issues += 1

        return issues

    def _doctor_component_status(self) -> int:
        """Check component installation status"""
        print("\n🧩 Component Status Check:")
        issues = 0
        merged_manifest = self._get_merged_manifest()

        for component, config in merged_manifest['components'].items():
            try:
                files = self.discover_files(component)
                installed_count = 0

                for rel_file in files:
                    target_path = self.target_dir / rel_file
                    if target_path.exists():
                        installed_count += 1

                if installed_count == 0:
                    print(f"  ❌ {component}: Not installed (0/{len(files)} files)")
                    issues += 1
                elif installed_count < len(files):
                    print(f"  ⚠️  {component}: Partially installed ({installed_count}/{len(files)} files)")
                    issues += 1
                else:
                    print(f"  ✅ {component}: Fully installed ({installed_count}/{len(files)} files)")

            except Exception as e:
                print(f"  ❌ {component}: Cannot analyze - {e}")
                issues += 1

        return issues

    def _doctor_environment(self) -> int:
        """Check environment and dependencies"""
        print("\n🌍 Environment Check:")
        issues = 0

        # Check git repository
        if (self.target_dir / ".git").exists():
            print("  ✅ Git repository detected")
        else:
            print("  ⚠️  No git repository (some features may not work)")
            issues += 1

        # Check Python
        import sys
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        print(f"  ✅ Python {python_version} available")

        # Check pre-commit
        try:
            result = subprocess.run(['pre-commit', '--version'],
                                 capture_output=True, text=True, check=False)
            if result.returncode == 0:
                print(f"  ✅ Pre-commit available: {result.stdout.strip()}")
            else:
                print("  ⚠️  Pre-commit not installed")
                issues += 1
        except FileNotFoundError:
            print("  ⚠️  Pre-commit not installed")
            issues += 1

        return issues

    def doctor_yaml(self, component_filter: str = None):
        """Generate YAML repair manifest for repairs needed."""
        from datetime import datetime

        repair_manifest = {
            'repair_manifest': {
                'generated': datetime.now().isoformat(),
                'scope': component_filter or 'all',
                'repairs': []
            }
        }

        # Check installation manifest
        manifest_path = self.target_dir / "src" / "installation-manifest.yaml"
        if not manifest_path.exists():
            repair_manifest['repair_manifest']['repairs'].append({
                'type': 'missing_file',
                'path': str(manifest_path),
                'action': 'create_installation_manifest'
            })
        else:
            try:
                with open(manifest_path, 'r') as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                repair_manifest['repair_manifest']['repairs'].append({
                    'type': 'yaml_syntax_error',
                    'path': str(manifest_path),
                    'error': str(e),
                    'action': 'fix_yaml_syntax'
                })

        # Check plugin manifests
        plugins_dir = self.target_dir / "src" / "plugins"
        if plugins_dir.exists():
            for plugin_dir in plugins_dir.iterdir():
                if plugin_dir.is_dir():
                    plugin_manifest = plugin_dir / "plugin-manifest.yaml"
                    if not plugin_manifest.exists():
                        repair_manifest['repair_manifest']['repairs'].append({
                            'type': 'missing_file',
                            'path': str(plugin_manifest),
                            'plugin': plugin_dir.name,
                            'action': 'create_plugin_manifest'
                        })
                    else:
                        try:
                            with open(plugin_manifest, 'r') as f:
                                yaml.safe_load(f)
                        except yaml.YAMLError as e:
                            repair_manifest['repair_manifest']['repairs'].append({
                                'type': 'yaml_syntax_error',
                                'path': str(plugin_manifest),
                                'plugin': plugin_dir.name,
                                'error': str(e),
                                'action': 'fix_yaml_syntax'
                            })

        # Check for missing files from components (only check installed components)
        try:
            # Load state to see what components should be installed
            state = self._load_state()
            installed_components = state.get('installed_components', [])

            # If no state exists, check all components (backward compatibility)
            if not installed_components:
                print("⚠️  No installation state found - checking all available components")
                print("💡 Run 'ai-guardrails init' to establish proper state tracking")

            merged_manifest = self._get_merged_manifest()
            components_to_check = installed_components if installed_components else merged_manifest['components'].keys()

            for component in components_to_check:
                # Filter by component if specified
                if component_filter and component != component_filter:
                    continue

                # Skip if component doesn't exist in manifest
                if component not in merged_manifest['components']:
                    continue

                config = merged_manifest['components'][component]

                try:
                    files = self.discover_files(component)
                    for rel_file in files:
                        # Determine source path
                        if self._is_plugin_component(component):
                            plugin_path = self._get_plugin_path_for_component(component)
                            src_path = plugin_path / rel_file if plugin_path else None
                        else:
                            src_path = self.template_repo / rel_file

                        # Check target path
                        target_path = self.target_dir / rel_file
                        if src_path and src_path.exists() and not target_path.exists():
                            # Include ALL missing files, not just YAML (that was too limiting)
                            repair_manifest['repair_manifest']['repairs'].append({
                                'type': 'missing_file',
                                'path': str(target_path),
                                'component': component,
                                'source_file': rel_file,
                                'action': 'install_component'
                            })
                except Exception as e:
                    # If we can't discover files for a component, note it
                    repair_manifest['repair_manifest']['repairs'].append({
                        'type': 'component_error',
                        'component': component,
                        'error': str(e),
                        'action': 'check_component_configuration'
                    })
        except Exception as e:
            repair_manifest['repair_manifest']['repairs'].append({
                'type': 'manifest_error',
                'error': str(e),
                'action': 'check_installation_manifest'
            })

        # Output the repair manifest as YAML
        print(yaml.dump(repair_manifest, default_flow_style=False, sort_keys=False))

        return len(repair_manifest['repair_manifest']['repairs']) == 0

    def ensure(self, apply: bool = False, focus: str = "all", yaml_input: str = None, component_filter: str = None) -> bool:
        """Ensure workflow - repair/install missing components"""
        if apply:
            print("🔧 AI Guardrails Ensure - Applying Repairs")
        else:
            print("🔍 AI Guardrails Ensure - Dry Run (use --apply to fix)")
        print("=" * 50)

        # Handle YAML input from stdin or detect YAML focus
        if yaml_input:
            print("📄 Processing YAML repair manifest...")
            try:
                # Try to parse YAML input
                if yaml_input.strip().startswith('{'):
                    # Looks like JSON, try JSON first
                    import json
                    repair_data = json.loads(yaml_input)
                else:
                    # Try YAML
                    repair_data = yaml.safe_load(yaml_input)

                if 'repair_manifest' in repair_data:
                    repairs = repair_data['repair_manifest']['repairs']
                    return self._apply_repair_manifest(repairs, apply)
                else:
                    print("❌ Invalid repair manifest format - missing 'repair_manifest' key")
                    return False
            except (yaml.YAMLError, json.JSONDecodeError) as e:
                print(f"❌ Failed to parse YAML input: {e}")
                return False

        # Standard workflow - run doctor first to identify issues
        print("Running diagnostics...")
        issues_found = not self.doctor(focus)

        if not issues_found:
            print("\n✅ No issues found - nothing to repair!")
            return True

        if not apply:
            print(f"\n💡 Run with --apply to automatically fix issues")
            return False

        print(f"\n🔧 Applying repairs...")
        repairs_successful = 0

        if focus == "yaml" or focus == "all":
            repairs_successful += self._ensure_yaml_structure(apply)

        if focus == "all":
            repairs_successful += self._ensure_components(apply)
            repairs_successful += self._ensure_environment(apply)

        print(f"\n✅ Applied {repairs_successful} repairs successfully")
        return True

    def _apply_repair_manifest(self, repairs: list, apply: bool) -> bool:
        """Apply repairs from a YAML manifest"""
        if not apply:
            print(f"📋 Would apply {len(repairs)} repairs:")
            for repair in repairs:
                print(f"  - {repair['action']}: {repair['path']}")
            print("\n💡 Use --apply to execute these repairs")
            return False

        repairs_successful = 0
        for repair in repairs:
            try:
                if repair['action'] == 'install_component':
                    component = repair.get('component', 'core')
                    print(f"  Installing component: {component}")
                    if self.install_component(component, force=True):
                        repairs_successful += 1
                elif repair['action'] == 'create_installation_manifest':
                    print(f"  Creating installation manifest...")
                    # Create a basic installation manifest
                    self._create_default_installation_manifest()
                    repairs_successful += 1
                elif repair['action'] == 'create_plugin_manifest':
                    plugin = repair.get('plugin', 'unknown')
                    print(f"  Creating plugin manifest for: {plugin}")
                    self._create_default_plugin_manifest(plugin)
                    repairs_successful += 1
                elif repair['action'] == 'fix_yaml_syntax':
                    print(f"  ⚠️  Cannot auto-fix YAML syntax in: {repair['path']}")
                    print(f"     Error: {repair.get('error', 'Unknown')}")
                    print(f"     Please fix manually")
                else:
                    print(f"  ❌ Unknown repair action: {repair['action']}")
            except Exception as e:
                print(f"  ❌ Failed to apply repair {repair['action']}: {e}")

        print(f"\n✅ Applied {repairs_successful}/{len(repairs)} repairs successfully")
        return repairs_successful == len(repairs)

    def init(self, profile: str = "auto", dry_run: bool = False) -> bool:
        """One-click installation with smart defaults"""
        print("🚀 AI Guardrails Init - One-Click Installation")
        print("=" * 50)

        # Check if we need to bootstrap from scratch
        if not self.template_repo.exists() and not self.manifest_path.exists():
            print("🔄 Bootstrapping from scratch...")
            if not self._bootstrap_from_remote():
                print("❌ Failed to bootstrap - unable to fetch AI Guardrails templates")
                return False

        # Auto-detect environment if profile is 'auto'
        if profile == "auto":
            profile = self._detect_best_profile()
            print(f"🔍 Auto-detected profile: {profile}")

        print(f"📦 Installing profile: {profile}")

        # Show what will be installed
        merged_manifest = self._get_merged_manifest()
        if profile not in merged_manifest['profiles']:
            print(f"❌ Unknown profile: {profile}")
            return False

        profile_config = merged_manifest['profiles'][profile]
        components = profile_config['components']

        print(f"📋 Will install {len(components)} components:")
        for component in components:
            component_config = merged_manifest['components'].get(component, {})
            description = component_config.get('description', 'No description')
            print(f"  • {component}: {description}")

        if dry_run:
            print("\n💡 This is a dry run - use without --dry-run to install")
            return True

        # Confirm installation
        print(f"\n🔧 Installing {profile} profile...")
        success = self.install_profile(profile, force=False)

        if success:
            print(f"\n✅ AI Guardrails successfully initialized with {profile} profile!")
            print("\n📚 Next steps:")
            print("  • Run 'ai-guardrails doctor' to validate installation")
            print("  • Check '.ai/guardrails.yaml' for configuration")
            print("  • Customize components with 'ai-guardrails component <name>'")
        else:
            print(f"\n❌ Installation failed - run 'ai-guardrails doctor' for diagnostics")

        return success

    def _bootstrap_from_remote(self) -> bool:
        """Bootstrap AI Guardrails templates from remote repository"""
        import subprocess
        import tempfile
        import shutil
        
        print("📥 Fetching AI Guardrails templates...")
        
        try:
            # Create temporary directory for cloning
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Clone the repository (using sparse checkout for efficiency)
                repo_url = "https://github.com/your-org/ai-guardrails-bootstrap.git"  # Update with actual repo
                
                # For now, let's try to copy from the local repository if we're in it
                # This handles the case where the user is running from the bootstrap repo
                current_script_dir = Path(__file__).parent.parent
                
                if (current_script_dir / "src" / "installation-manifest.yaml").exists():
                    print("📋 Using local templates...")
                    
                    # Copy manifest
                    src_dir = self.target_dir / "src"
                    src_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(
                        current_script_dir / "src" / "installation-manifest.yaml",
                        src_dir / "installation-manifest.yaml"
                    )
                    
                    # Copy templates
                    if (current_script_dir / "src" / "ai-guardrails-templates").exists():
                        if self.template_repo.exists():
                            shutil.rmtree(self.template_repo)
                        shutil.copytree(
                            current_script_dir / "src" / "ai-guardrails-templates",
                            self.template_repo
                        )
                    
                    print("✅ Templates copied successfully")
                    return True
                else:
                    # TODO: Implement remote fetching
                    print("❌ Remote fetching not implemented yet")
                    print("💡 Please run this command from the AI Guardrails bootstrap repository")
                    return False
                    
        except Exception as e:
            print(f"❌ Failed to bootstrap templates: {e}")
            return False

    def _detect_best_profile(self) -> str:
        """Auto-detect the best installation profile based on environment"""
        print("🔍 Detecting environment...")

        # Check for git repository
        has_git = (self.target_dir / ".git").exists()
        print(f"  Git repository: {'✅ detected' if has_git else '❌ not found'}")

        # Check for Python project
        has_python = any([
            (self.target_dir / "pyproject.toml").exists(),
            (self.target_dir / "requirements.txt").exists(),
            (self.target_dir / "setup.py").exists(),
            (self.target_dir / "Pipfile").exists()
        ])
        print(f"  Python project: {'✅ detected' if has_python else '❌ not found'}")

        # Check for Node.js project
        has_node = (self.target_dir / "package.json").exists()
        print(f"  Node.js project: {'✅ detected' if has_node else '❌ not found'}")

        # Check for existing AI guardrails
        has_existing = (self.target_dir / ".ai").exists()
        print(f"  Existing .ai config: {'⚠️  found' if has_existing else '✅ clean slate'}")

        # Decide profile based on environment
        if has_git and (has_python or has_node):
            return "full"  # Full-featured project
        elif has_git:
            return "standard"  # Git project without language detection
        else:
            return "minimal"  # Simple setup

    def _create_default_installation_manifest(self):
        """Create a basic installation manifest"""
        manifest_path = self.target_dir / "src" / "installation-manifest.yaml"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        default_manifest = {
            'components': {
                'core': {
                    'description': 'Core AI Guardrails files',
                    'files': ['.ai/guardrails.yaml']
                }
            },
            'profiles': {
                'default': {
                    'description': 'Default profile',
                    'components': ['core']
                }
            },
            'settings': {
                'template_source_directory': 'src/ai-guardrails-templates',
                'plugin_directories': ['src/plugins']
            }
        }

        with open(manifest_path, 'w') as f:
            yaml.dump(default_manifest, f, default_flow_style=False, sort_keys=False)

    def _create_default_plugin_manifest(self, plugin_name: str):
        """Create a basic plugin manifest"""
        plugin_dir = self.target_dir / "src" / "plugins" / plugin_name
        manifest_path = plugin_dir / "plugin-manifest.yaml"

        plugin_dir.mkdir(parents=True, exist_ok=True)

        default_manifest = {
            'components': {
                f'{plugin_name}-core': {
                    'description': f'Core files for {plugin_name} plugin',
                    'files': ['README.md']
                }
            },
            'profiles': {
                'default': {
                    'description': f'Default profile for {plugin_name}',
                    'components': [f'{plugin_name}-core']
                }
            }
        }

        with open(manifest_path, 'w') as f:
            yaml.dump(default_manifest, f, default_flow_style=False, sort_keys=False)

    def _ensure_yaml_structure(self, apply: bool) -> int:
        """Repair YAML structure issues"""
        if not apply:
            return 0

        repairs = 0

        # Check for missing core YAML files and install them
        yaml_component_map = {
            ".ai/guardrails.yaml": "core",
            ".ai/envelope.json": "core",
            ".pre-commit-config.yaml": "precommit"
        }

        for file_path, component in yaml_component_map.items():
            full_path = self.target_dir / file_path
            if not full_path.exists():
                print(f"  🔧 Installing missing {file_path}")
                if self.install_component(component, force=False):
                    repairs += 1

        return repairs

    def _ensure_components(self, apply: bool) -> int:
        """Repair component installation issues"""
        if not apply:
            return 0

        repairs = 0
        merged_manifest = self._get_merged_manifest()

        for component, config in merged_manifest['components'].items():
            try:
                files = self.discover_files(component)
                missing_files = []

                for rel_file in files:
                    target_path = self.target_dir / rel_file
                    if not target_path.exists():
                        missing_files.append(rel_file)

                if missing_files:
                    print(f"  🔧 Reinstalling {component} (missing {len(missing_files)} files)")
                    if self.install_component(component, force=False):
                        repairs += 1

            except Exception as e:
                print(f"  ❌ Cannot repair {component}: {e}")

        return repairs

    def _ensure_environment(self, apply: bool) -> int:
        """Repair environment issues"""
        if not apply:
            return 0

        repairs = 0

        # Install pre-commit if missing
        try:
            subprocess.run(['pre-commit', '--version'],
                         capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("  🔧 Installing pre-commit")
            try:
                subprocess.run([
                    'python3', '-m', 'pip', 'install', 'pre-commit'
                ], check=True, capture_output=True)
                repairs += 1
            except subprocess.CalledProcessError as e:
                print(f"  ❌ Failed to install pre-commit: {e}")

        return repairs

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

    # Init command - one-click installation
    init_parser = subparsers.add_parser('init', help='One-click installation with smart defaults')
    init_parser.add_argument('--profile', default='auto',
                            choices=['auto', 'minimal', 'standard', 'full'],
                            help='Installation profile (default: auto-detect)')
    init_parser.add_argument('--dry-run', action='store_true',
                            help='Show what would be installed without applying')

    # Install profile
    install_parser = subparsers.add_parser('install', help='Install a profile')
    install_parser.add_argument('profile', help='Profile to install')

    # Install component
    component_parser = subparsers.add_parser('component', help='Install specific component')
    component_parser.add_argument('component', help='Component to install')

    # Doctor workflow
    doctor_parser = subparsers.add_parser('doctor', help='Validate installation integrity')
    doctor_parser.add_argument('focus', nargs='?', default='all',
                              choices=['all', 'yaml'],
                              help='Focus area for diagnostics (default: all)')
    doctor_parser.add_argument('--format', choices=['human', 'yaml'], default='human',
                              help='Output format: human-readable or YAML repair manifest')
    doctor_parser.add_argument('--component',
                              help='Generate repair manifest for specific component only')

    # Ensure workflow
    ensure_parser = subparsers.add_parser('ensure', help='Repair installation issues')
    ensure_parser.add_argument('--apply', action='store_true',
                              help='Apply repairs (default: dry run)')
    ensure_parser.add_argument('--manifest',
                              help='Apply repairs from YAML manifest file')
    ensure_parser.add_argument('--from-stdin', action='store_true',
                              help='Read repair manifest from stdin')
    ensure_parser.add_argument('--component',
                              help='Repair specific component only')
    ensure_parser.add_argument('focus', nargs='?', default='all',
                              choices=['all', 'yaml'],
                              help='Focus area for repairs (default: all)')

    # List commands
    subparsers.add_parser('list-components', help='List available components')
    subparsers.add_parser('list-profiles', help='List available profiles')
    subparsers.add_parser('show-state', help='Show current installation state')

    # Pre-commit configuration
    subparsers.add_parser('configure-precommit', help='Reconfigure pre-commit hooks based on guardrails.yaml settings')

    # Discover what files would be installed
    discover_parser = subparsers.add_parser('discover', help='Show what files would be installed')
    discover_parser.add_argument('component', help='Component to analyze')

    args = parser.parse_args()

    try:
        bootstrap = InfrastructureBootstrap(args.target)

        if args.command == 'init':
            success = bootstrap.init(args.profile, args.dry_run)
            exit(0 if success else 1)
        elif args.command == 'install':
            success = bootstrap.install_profile(args.profile, args.force)
            exit(0 if success else 1)
        elif args.command == 'component':
            success = bootstrap.install_component(args.component, args.force)
            exit(0 if success else 1)
        elif args.command == 'doctor':
            if args.format == 'yaml':
                success = bootstrap.doctor_yaml(component_filter=args.component)
            else:
                success = bootstrap.doctor(args.focus)
            exit(0 if success else 1)
        elif args.command == 'ensure':
            # Handle different input sources for repair manifest
            yaml_input = None

            if args.manifest:
                # Read from file
                with open(args.manifest, 'r') as f:
                    yaml_input = f.read()
            elif args.from_stdin and not sys.stdin.isatty():
                # Read from stdin
                yaml_input = sys.stdin.read().strip()
            elif not sys.stdin.isatty():
                # Auto-detect stdin input
                yaml_input = sys.stdin.read().strip()

            success = bootstrap.ensure(
                apply=args.apply,
                focus=args.focus,
                yaml_input=yaml_input,
                component_filter=args.component
            )
            exit(0 if success else 1)
        elif args.command == 'list-components':
            bootstrap.list_all_components()
        elif args.command == 'list-profiles':
            bootstrap.list_all_profiles()
        elif args.command == 'show-state':
            bootstrap.show_state()
        elif args.command == 'configure-precommit':
            print("🔧 Reconfiguring pre-commit hooks...")
            bootstrap._customize_precommit_config()
            print("✅ Pre-commit configuration updated")
        elif args.command == 'discover':
            bootstrap.list_discovered_files(args.component)
        else:
            parser.print_help()

    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == '__main__':
    main()
