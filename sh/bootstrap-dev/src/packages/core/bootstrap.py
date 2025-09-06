#!/usr/bin/env python3
"""
Infrastructure Bootstrap Manager

This module provides the main orchestrator class for AI guardrails infrastructure
management. It composes various specialized managers to provide a unified interface
for installation, configuration, and diagnostics.

The InfrastructureBootstrap class follows a composition pattern, delegating
specific responsibilities to focused manager classes while maintaining a clean
public API for end users.
"""
import yaml
from pathlib import Path
from typing import Dict, List

from ..utils import Colors
from ..managers import StateManager, PluginSystem, ComponentManager, ConfigManager
from ..operations import Doctor
from ..presentation import ProfilePresenter


class InfrastructureBootstrap:
    def __init__(self, target_dir: Path = None):
        """Initialize the bootstrap system"""
        self.target_dir = Path(target_dir) if target_dir else Path.cwd()

        # Templates should come from the tool installation, not the target project
        script_dir = Path(__file__).parent.parent.parent.parent / "bin"
        self.template_repo = script_dir.parent / "src" / "ai-guardrails-templates"

        # Manifest should also come from tool installation
        self.manifest_path = script_dir.parent / "src" / "installation-manifest.yaml"

        # Load manifest
        self.manifest = self._load_manifest()

        # Initialize managers
        self.state_manager = StateManager(self.target_dir)
        self.plugin_system = PluginSystem(self.target_dir)
        self.component_manager = ComponentManager(self.target_dir, self.template_repo, self.plugin_system)
        self.config_manager = ConfigManager(self.target_dir)
        self.doctor_manager = Doctor(self.target_dir, self.state_manager, self.component_manager)

        # Get merged manifest (including plugins)
        self.merged_manifest = self.plugin_system.get_merged_manifest(self.manifest)

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

    # Delegate state management to StateManager
    def show_state(self):
        """Show current installation state"""
        return self.state_manager.show_state()

    # Delegate component operations to ComponentManager
    def discover_files(self, component: str, debug: bool = False) -> List[str]:
        """Dynamically discover files based on patterns"""
        return self.component_manager.discover_files(component, self.merged_manifest, debug)

    def debug_discover(self, component: str) -> None:
        """Debug component file discovery with verbose output"""
        return self.component_manager.debug_discover(component, self.merged_manifest)

    def install_component(self, component: str, force: bool = False) -> bool:
        """Install a specific component"""
        success = self.component_manager.install_component(component, self.merged_manifest, force)
        if success:
            self.state_manager.update_state_for_component(component)
        return success

    def list_discovered_files(self, component: str):
        """List what files would be installed for a component"""
        return self.component_manager.list_discovered_files(component, self.merged_manifest)

    def list_all_components(self):
        """List all available components grouped by source"""
        return self.component_manager.list_all_components(self.merged_manifest)

    # Profile management
    def install_profile(self, profile: str, force: bool = False) -> bool:
        """Install a profile"""
        if profile not in self.merged_manifest['profiles']:
            raise ValueError(f"Unknown profile: {profile}")

        profile_config = self.merged_manifest['profiles'][profile]
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
            self.state_manager.update_state_for_profile(profile, installed_components)

        return success

    def list_all_profiles(self):
        """List all available profiles"""
        ProfilePresenter.list_all_profiles(self.merged_manifest)

    # Diagnostic functionality
    def doctor(self, focus: str = "all") -> bool:
        """Diagnostic workflow - validate installation integrity"""
        return self.doctor_manager.run_diagnostics(self.merged_manifest, focus)

    # Initialization workflow
    def init(self, profile: str = 'auto', dry_run: bool = False) -> bool:
        """One-click installation with smart defaults"""
        # Auto-detect profile if requested
        if profile == 'auto':
            profile = self._detect_project_profile()

        if profile not in self.merged_manifest['profiles']:
            available_profiles = list(self.merged_manifest['profiles'].keys())
            print(f"{Colors.error('[ERROR]')} Unknown profile: {profile}")
            print(f"Available profiles: {', '.join(available_profiles)}")
            return False

        profile_config = self.merged_manifest['profiles'][profile]
        components = profile_config['components']

        if dry_run:
            print(f"Would install profile '{profile}' with components:")
            for component in components:
                print(f"  - {component}")
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
