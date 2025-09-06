#!/usr/bin/env python3
"""
Infrastructure Bootstrap Manager
Core bootstrap functionality extracted from main script
"""
import json
import shutil
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Dict, List

from .utils import Colors


class InfrastructureBootstrap:
    def __init__(self, target_dir: Path = None):
        """Initialize the bootstrap system"""
        self.target_dir = Path(target_dir) if target_dir else Path.cwd()

        # Templates should come from the tool installation, not the target project
        script_dir = Path(__file__).parent.parent.parent / "bin"
        self.template_repo = script_dir.parent / "src" / "ai-guardrails-templates"

        # Manifest should also come from tool installation
        self.manifest_path = script_dir.parent / "src" / "installation-manifest.yaml"
        self.state_path = self.target_dir / ".ai-guardrails-state.yaml"
        self.plugins = {}

        # Load manifest
        self.manifest = self._load_manifest()

        # Discover plugins
        self.plugins = self._discover_plugins()

    def _load_manifest(self) -> Dict:
        """Load installation manifest from tool installation"""
        if not self.manifest_path.exists():
            print(f"{Colors.warn('[WARN]')} Manifest not found: {self.manifest_path}")
            print(f"{Colors.info('[INFO]')} Creating minimal manifest for bootstrapping")
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
        """Discover and load plugin manifests from tool installation"""
        plugins = {}

        # # Import and use utility function
        # try:
        #     from . import utils
        #     utils.activate_plugins()
        # except ImportError:
        #     pass

        # Plugins should come from the tool installation plugins directory
        script_dir = Path(__file__).parent.parent.parent / "bin"
        plugins_dir = script_dir.parent / "src" / "plugins"

        # Look for plugin-manifest.yaml files only in plugins directory
        if plugins_dir.exists():
            for plugin_dir in plugins_dir.iterdir():
                if plugin_dir.is_dir():
                    manifest_file = plugin_dir / "plugin-manifest.yaml"
                    if manifest_file.exists():
                        try:
                            with open(manifest_file) as f:
                                plugin_manifest = yaml.safe_load(f)
                                plugin_name = plugin_manifest['plugin']['name']
                                plugins[plugin_name] = {
                                    'manifest': plugin_manifest,
                                    'path': plugin_dir
                                }
                        except Exception as e:
                            print(f"{Colors.warn('[WARN]')} Failed to load plugin {plugin_dir.name}: {e}")

        return plugins

    def _get_merged_manifest(self) -> Dict:
        """Get manifest merged with plugin configurations"""
        merged = self.manifest.copy()

        # Merge plugin components and profiles
        for plugin_name, plugin_data in self.plugins.items():
            plugin_manifest = plugin_data['manifest']

            # Merge components
            if 'components' in plugin_manifest:
                merged['components'].update(plugin_manifest['components'])

            # Merge profiles
            if 'profiles' in plugin_manifest:
                merged.setdefault('profiles', {}).update(plugin_manifest['profiles'])

        return merged

    def _load_state(self) -> Dict:
        """Load the installation state file"""
        if not self.state_path.exists():
            return {
                'version': '1.0.0',
                'installed_profile': None,
                'installed_components': [],
                'installation_history': []
            }

        try:
            with open(self.state_path) as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"{Colors.warn('[WARN]')} Failed to load state file: {e}")
            return {'version': '1.0.0', 'installed_components': [], 'installation_history': []}

    def _save_state(self, state: Dict):
        """Save the installation state file"""
        try:
            with open(self.state_path, 'w') as f:
                yaml.dump(state, f, default_flow_style=False)
        except Exception as e:
            print(f"{Colors.error('[ERROR]')} Failed to save state file: {e}")

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

        print(Colors.bold("AI Guardrails Installation State"))
        print(Colors.info("=" * 50))

        if state.get('installed_profile'):
            print(f"Installed Profile: {state['installed_profile']}")
        else:
            print("No profile installed (manual component installation)")

        installed_components = state.get('installed_components', [])
        if installed_components:
            print(f"Installed Components: {', '.join(installed_components)}")
        else:
            print("No components installed")

        history = state.get('installation_history', [])
        if history:
            print(f"\nInstallation History ({len(history)} entries):")
            for entry in history[-3:]:  # Show last 3 entries
                print(f"  {entry['timestamp']}: {entry['action']}")

        print()

    def _is_plugin_component(self, component: str) -> bool:
        """Check if a component comes from a plugin"""
        # Check if component exists in any plugin
        for plugin_name, plugin_data in self.plugins.items():
            plugin_manifest = plugin_data['manifest']
            if 'components' in plugin_manifest and component in plugin_manifest['components']:
                return True
        return False

    def _get_plugin_path_for_component(self, component: str) -> Path:
        """Get the plugin directory path for a given component"""
        for plugin_name, plugin_data in self.plugins.items():
            plugin_manifest = plugin_data['manifest']
            if 'components' in plugin_manifest and component in plugin_manifest['components']:
                return plugin_data['path']
        return None

    def _get_plugin_name_for_component(self, component: str) -> str:
        """Get the plugin name for a given component"""
        for plugin_name, plugin_data in self.plugins.items():
            plugin_manifest = plugin_data['manifest']
            if 'components' in plugin_manifest and component in plugin_manifest['components']:
                return plugin_name
        return None

    def discover_files(self, component: str, debug: bool = False) -> List[str]:
        """Dynamically discover files based on patterns - NO hardcoding!"""
        merged_manifest = self._get_merged_manifest()

        if component not in merged_manifest['components']:
            raise ValueError(f"Unknown component: {component}")

        component_config = merged_manifest['components'][component]
        patterns = component_config['file_patterns']

        if debug:
            print(f"Component: {component}")
            print(f"Patterns: {patterns}")

        # Check if this is a plugin component
        is_plugin_component = self._is_plugin_component(component)

        discovered = []
        for pattern in patterns:
            if is_plugin_component:
                plugin_path = self._get_plugin_path_for_component(component)
                if plugin_path:
                    # First try to find files in the plugin's templates directory
                    plugin_templates_path = plugin_path / "templates"
                    if plugin_templates_path.exists():
                        search_path = plugin_templates_path / pattern
                        if debug:
                            print(f"Searching plugin templates: {search_path}")
                        # Handle recursive globs properly
                        if '**' in pattern:
                            matches = list(plugin_templates_path.rglob(pattern.split('**/')[-1]))
                        else:
                            matches = list(search_path.parent.glob(search_path.name))
                        discovered.extend(matches)

                    # Also try the plugin root directory for backwards compatibility
                    if not discovered:
                        search_path = plugin_path / pattern
                        if debug:
                            print(f"Searching plugin root: {search_path}")
                        # Handle recursive globs properly
                        if '**' in pattern:
                            # For recursive patterns, search from the appropriate base directory
                            base_parts = pattern.split('**')[0].strip('/')
                            if base_parts:
                                base_path = plugin_path / base_parts
                                if base_path.exists():
                                    glob_pattern = pattern.split('**/')[-1]
                                    matches = list(base_path.rglob(glob_pattern))
                                else:
                                    matches = []
                            else:
                                glob_pattern = pattern.split('**/')[-1]
                                matches = list(plugin_path.rglob(glob_pattern))
                        else:
                            matches = list(search_path.parent.glob(search_path.name))
                        discovered.extend(matches)
            else:
                search_path = self.template_repo / pattern
                if debug:
                    print(f"Searching base templates: {search_path}")
                # Handle recursive globs properly
                if '**' in pattern:
                    base_parts = pattern.split('**')[0].strip('/')
                    if base_parts:
                        base_path = self.template_repo / base_parts
                        if base_path.exists():
                            glob_pattern = pattern.split('**/')[-1]
                            matches = list(base_path.rglob(glob_pattern))
                        else:
                            matches = []
                    else:
                        glob_pattern = pattern.split('**/')[-1]
                        matches = list(self.template_repo.rglob(glob_pattern))
                else:
                    matches = list(search_path.parent.glob(search_path.name))
                discovered.extend(matches)

        # Convert to relative paths from the appropriate base directory
        relative_files = []

        if is_plugin_component:
            plugin_path = self._get_plugin_path_for_component(component)
            if plugin_path:
                for f in discovered:
                    if f.is_file():
                        # Try to get relative path from templates directory first
                        plugin_templates_path = plugin_path / "templates"
                        if plugin_templates_path.exists() and plugin_templates_path in f.parents:
                            relative_files.append(str(f.relative_to(plugin_templates_path)))
                        elif plugin_path in f.parents:
                            relative_files.append(str(f.relative_to(plugin_path)))
        else:
            relative_files = [str(f.relative_to(self.template_repo)) for f in discovered if f.is_file()]

        if debug:
            print(f"Discovered files: {relative_files}")

        return relative_files

    def debug_discover(self, component: str) -> None:
        """Debug component file discovery with verbose output"""
        try:
            files = self.discover_files(component, debug=True)
            print(f"Discovered {len(files)} files:")
            for file in sorted(files):
                print(f"  {file}")
        except Exception as e:
            print(f"Error: {e}")

    def install_component(self, component: str, force: bool = False) -> bool:
        """Install a specific component"""
        try:
            files = self.discover_files(component)
            if not files:
                print(f"{Colors.warn('[WARN]')} No files found for component: {component}")
                return False

            print(f"Installing component: {component} ({len(files)} files)")

            success = True
            for rel_file in files:
                # Apply target_prefix stripping if configured
                target_rel_file = self._apply_target_prefix_stripping(component, rel_file)

                # Determine source path
                if self._is_plugin_component(component):
                    plugin_path = self._get_plugin_path_for_component(component)
                    if plugin_path:
                        # First try templates directory
                        plugin_templates_path = plugin_path / "templates"
                        if plugin_templates_path.exists():
                            src_path = plugin_templates_path / rel_file
                        else:
                            src_path = plugin_path / rel_file
                    else:
                        src_path = None
                else:
                    src_path = self.template_repo / rel_file

                target_path = self.target_dir / target_rel_file

                if not src_path or not src_path.exists():
                    print(f"  {Colors.error('[ERROR]')} Source not found: {rel_file}")
                    success = False
                    continue

                # Create target directory
                target_path.parent.mkdir(parents=True, exist_ok=True)

                # Get the final target path (may be different for .example files)
                final_target = self._get_merge_target_path(src_path, target_path)

                # Check if final target exists and handle merge/overwrite
                if final_target.exists() and not force:
                    if self._should_merge_file(src_path, final_target):
                        print(f"  merging: {rel_file} -> {final_target.relative_to(self.target_dir)}")
                        self._merge_yaml_file(src_path, final_target)
                    else:
                        print(f"  {Colors.warn('[SKIP]')} exists: {rel_file}")
                        continue
                else:
                    final_target.parent.mkdir(parents=True, exist_ok=True)
                    print(f"  copying: {rel_file} -> {final_target.relative_to(self.target_dir)}")
                    shutil.copy2(src_path, final_target)

            if success:
                self._update_state_for_component(component)

                # Handle special post-install actions
                if component == 'precommit':
                    self._customize_precommit_config()
                    self._install_precommit_hooks()

            return success

        except ValueError as e:
            print(f"{Colors.error('[ERROR]')} {e}")
            return False

    def _customize_precommit_config(self):
        """Customize .pre-commit-config.yaml based on guardrails.yaml settings"""
        guardrails_path = self.target_dir / ".ai" / "guardrails.yaml"
        precommit_path = self.target_dir / ".pre-commit-config.yaml"

        if not guardrails_path.exists() or not precommit_path.exists():
            return

        try:
            with open(guardrails_path) as f:
                guardrails = yaml.safe_load(f)

            with open(precommit_path) as f:
                precommit_config = yaml.safe_load(f)

            # Get disabled languages from guardrails config
            disabled_languages = []
            if 'precommit' in guardrails and 'disabled_languages' in guardrails['precommit']:
                raw_disabled = guardrails['precommit']['disabled_languages']
                # Handle None/null values from YAML loading (empty lists with only comments)
                disabled_languages = raw_disabled if raw_disabled is not None else []

            # Customize pre-commit hooks based on disabled languages
            if disabled_languages:
                self._apply_language_exclusions(precommit_config, disabled_languages)

            # Write back the customized config
            with open(precommit_path, 'w') as f:
                yaml.dump(precommit_config, f, default_flow_style=False, sort_keys=False)

            print(f"  {Colors.ok('[OK]')} Customized pre-commit configuration")
            if disabled_languages:
                print(f"  {Colors.info('[INFO]')} Disabled languages: {', '.join(disabled_languages)}")

        except Exception as e:
            print(f"  {Colors.warn('[WARN]')} Failed to customize pre-commit config: {e}")

    def _apply_language_exclusions(self, precommit_config, disabled_languages):
        """Apply language exclusions to pre-commit configuration"""
        language_file_patterns = {
            'python': r'.*\.py$',
            'node': r'.*\.(js|ts|jsx|tsx)$|.*package\.json$',
            'go': r'.*\.go$|.*go\.mod$|.*go\.sum$',
            'rust': r'.*\.rs$|.*Cargo\.toml$|.*Cargo\.lock$',
            'java': r'.*\.java$|.*pom\.xml$|.*build\.gradle$',
            'dotnet': r'.*\.(cs|fs|vb)$|.*\.csproj$|.*\.fsproj$|.*\.vbproj$'
        }

        # Build exclude pattern for disabled languages
        exclude_patterns = []
        for lang in disabled_languages:
            if lang in language_file_patterns:
                exclude_patterns.append(language_file_patterns[lang])

        if exclude_patterns:
            # Apply exclude pattern to lang-lint hook
            for repo in precommit_config.get('repos', []):
                if repo.get('repo') == 'local':
                    for hook in repo.get('hooks', []):
                        if hook.get('id') == 'lang-lint':
                            # Combine patterns with OR
                            exclude_pattern = '|'.join(f'({pattern})' for pattern in exclude_patterns)
                            hook['exclude'] = exclude_pattern
                            break

    def _install_precommit_hooks(self):
        """Install pre-commit hooks like the old unified script did"""
        try:
            result = subprocess.run(['pre-commit', 'install'],
                                 cwd=self.target_dir,
                                 capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  {Colors.ok('[OK]')} Pre-commit hooks installed")
            else:
                print(f"  {Colors.warn('[WARN]')} Pre-commit install failed: {result.stderr}")
        except Exception as e:
            print(f"  {Colors.warn('[WARN]')} Failed to install pre-commit hooks: {e}")

    def _apply_target_prefix_stripping(self, component: str, rel_file: str) -> str:
        """Apply target_prefix stripping if configured for component"""
        merged_manifest = self._get_merged_manifest()

        if component not in merged_manifest['components']:
            return rel_file

        component_config = merged_manifest['components'][component]
        target_prefix = component_config.get('target_prefix', '')

        if target_prefix and rel_file.startswith(target_prefix):
            return rel_file[len(target_prefix):]

        return rel_file

    def _should_merge_file(self, src_path: Path, target_path: Path) -> bool:
        """Check if a file should be merged instead of copied"""
        # First check if files are identical - if so, no merge needed
        if target_path.exists():
            try:
                with open(src_path, 'r') as f1, open(target_path, 'r') as f2:
                    if f1.read() == f2.read():
                        return False  # Files are identical, skip merge
            except Exception:
                pass  # If comparison fails, proceed with normal logic

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

    def _merge_yaml_file(self, src_path: Path, target_path: Path):
        """Merge YAML/JSON files by combining their contents while preserving format"""
        try:
            # Load both files
            with open(src_path) as f:
                if src_path.suffix == '.json':
                    src_data = json.load(f)
                else:
                    src_data = yaml.safe_load(f)

            if target_path.exists():
                with open(target_path) as f:
                    if target_path.suffix == '.json':
                        target_data = json.load(f)
                    else:
                        target_data = yaml.safe_load(f)
            else:
                target_data = {}

            # Merge the data
            merged_data = self._deep_merge_dict(target_data, src_data)

            # Write back the merged result in the original format
            with open(target_path, 'w') as f:
                if target_path.suffix == '.json':
                    json.dump(merged_data, f, indent=2)
                else:
                    # Clean up null values that should be empty lists (for guardrails.yaml)
                    if target_path.name == 'guardrails.yaml':
                        self._clean_yaml_nulls(merged_data)
                    yaml.dump(merged_data, f, default_flow_style=False)

        except Exception as e:
            # Fallback to copy if merge fails
            print(f"  merge failed, copying instead: {e}")
            shutil.copy2(src_path, target_path)

    def _clean_yaml_nulls(self, data: dict):
        """Clean up null values in YAML data that should be empty lists"""
        list_fields = [
            ['precommit', 'disabled_hooks'],
            ['precommit', 'disabled_languages']
        ]
        
        for field_path in list_fields:
            current = data
            # Navigate to parent
            for key in field_path[:-1]:
                if key in current and isinstance(current[key], dict):
                    current = current[key]
                else:
                    break
            else:
                # Set null fields to empty lists
                field_name = field_path[-1]
                if field_name in current and current[field_name] is None:
                    current[field_name] = []

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
                plugin_name = self._get_plugin_name_for_component(component)
                plugin_components.setdefault(plugin_name, {})[component] = config
            else:
                base_components[component] = config

        # Display base components
        if base_components:
            print("Base Components:")
            for component, config in base_components.items():
                print(f"  {component}: {config['description']}")

        # Display plugin components grouped by plugin
        for plugin_name, components in plugin_components.items():
            print(f"\n{plugin_name} Plugin:")
            for component, config in components.items():
                print(f"  {component}: {config['description']}")

    def list_all_profiles(self):
        """List all available profiles"""
        merged_manifest = self._get_merged_manifest()
        print("Available profiles:")
        for profile, config in merged_manifest['profiles'].items():
            print(f"  {profile}: {config['description']}")
            print(f"    Components: {', '.join(config['components'])}")

    def doctor(self, focus: str = "all") -> bool:
        """Diagnostic workflow - validate installation integrity"""
        print(Colors.bold("AI Guardrails Doctor - Installation Diagnostics"))
        print(Colors.info("=" * 50))

        issues_found = 0
        self._get_merged_manifest()

        if focus == "yaml" or focus == "all":
            issues_found += self._doctor_yaml_structure()

        if focus == "all":
            issues_found += self._doctor_file_integrity()
            issues_found += self._doctor_component_status()
            issues_found += self._doctor_environment()

        print("\n" + Colors.info("=" * 50))
        if issues_found == 0:
            print(Colors.ok("All checks passed - installation is healthy!"))
            return True
        else:
            print(Colors.error(f"Found {issues_found} issues - run 'ensure --apply' to fix"))
            return False

    def _doctor_yaml_structure(self) -> int:
        """Validate YAML file structure and content"""
        print("\nYAML Structure Check:")
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
                    with open(full_path) as f:
                        if file_path.endswith('.json'):
                            json.load(f)
                        else:
                            yaml.safe_load(f)
                    print(f"  {Colors.ok('[OK]')} {description}")
                except Exception as e:
                    print(f"  {Colors.error('[ERROR]')} {description}: {e}")
                    issues += 1
            else:
                print(f"  {Colors.warn('[MISSING]')} {description}")
                issues += 1

        return issues

    def _doctor_file_integrity(self) -> int:
        """Check if all expected files are present"""
        print("\nFile Integrity Check:")
        issues = 0
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
                    print(f"  {Colors.warn('[PARTIAL]')} {component}: {len(missing_files)} missing files")
                    issues += len(missing_files)
                else:
                    print(f"  {Colors.ok('[OK]')} {component}: All files present")

            except Exception as e:
                print(f"  {Colors.error('[ERROR]')} {component}: Cannot check - {e}")
                issues += 1

        return issues

    def _doctor_component_status(self) -> int:
        """Check component installation status"""
        print("\nComponent Status Check:")
        issues = 0

        # Load state to see what components should be installed
        state = self._load_state()
        installed_components = state.get('installed_components', [])

        # If no state exists, check all components (backward compatibility)
        if not installed_components:
            print(f"  {Colors.warn('[WARN]')} No installation state found - checking all available components")
            print("  Run 'ai-guardrails init' to establish proper state tracking")
            merged_manifest = self._get_merged_manifest()
            components_to_check = merged_manifest['components'].keys()
        else:
            components_to_check = installed_components

        merged_manifest = self._get_merged_manifest()

        for component in components_to_check:
            # Skip if component doesn't exist in manifest
            if component not in merged_manifest['components']:
                continue

            try:
                files = self.discover_files(component)
                installed_count = 0

                for rel_file in files:
                    target_path = self.target_dir / rel_file
                    if target_path.exists():
                        installed_count += 1

                if installed_count == 0:
                    print(f"  {Colors.error('[BROKEN]')} {component}: No files installed")
                    issues += 1
                elif installed_count < len(files):
                    print(f"  {Colors.warn('[PARTIAL]')} {component}: {installed_count}/{len(files)} files")
                    issues += 1
                else:
                    print(f"  {Colors.ok('[OK]')} {component}: Fully installed")

            except Exception as e:
                print(f"  {Colors.error('[ERROR]')} {component}: Cannot analyze - {e}")
                issues += 1

        return issues

    def init(self, profile: str = 'auto', dry_run: bool = False) -> bool:
        """One-click installation with smart defaults"""
        # Auto-detect profile if requested
        if profile == 'auto':
            profile = self._detect_project_profile()

        merged_manifest = self._get_merged_manifest()

        if profile not in merged_manifest['profiles']:
            print(f"{Colors.error('[ERROR]')} Unknown profile: {profile}")
            return False

        profile_config = merged_manifest['profiles'][profile]
        components = profile_config['components']

        if dry_run:
            print(f"Would install profile: {profile} ({profile_config['description']})")
            print("Components:")
            for component in components:
                files = self.discover_files(component)
                print(f"  {component}: {len(files)} files")
            return True

        return self.install_profile(profile, force=False)

    def _detect_project_profile(self) -> str:
        """Auto-detect appropriate profile based on project characteristics"""
        # Check for existing Python project
        if (self.target_dir / "pyproject.toml").exists() or (self.target_dir / "setup.py").exists():
            return "standard"

        # Check for Node.js project
        if (self.target_dir / "package.json").exists():
            return "standard"

        # Default to minimal for new projects
        return "minimal"

    def _doctor_environment(self) -> int:
        """Check environment and dependencies"""
        print("\nEnvironment Check:")
        issues = 0

        # Check git repository
        if (self.target_dir / ".git").exists():
            print(f"  {Colors.ok('[OK]')} Git repository detected")
        else:
            print(f"  {Colors.warn('[WARN]')} No git repository (some features may not work)")
            issues += 1

        # Check Python
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        print(f"  {Colors.ok('[OK]')} Python {python_version} available")

        # Check pre-commit
        try:
            result = subprocess.run(['pre-commit', '--version'],
                                 capture_output=True, text=True, check=False)
            if result.returncode == 0:
                print(f"  {Colors.ok('[OK]')} Pre-commit available: {result.stdout.strip()}")
            else:
                print(f"  {Colors.warn('[WARN]')} Pre-commit not installed")
                issues += 1
        except FileNotFoundError:
            print(f"  {Colors.warn('[WARN]')} Pre-commit not installed")
            issues += 1

        return issues
