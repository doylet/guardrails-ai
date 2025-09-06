#!/usr/bin/env python3
"""
Presentation Layer
Separates display logic from business logic for better SRP
"""
from typing import Dict, List
from ..utils import Colors


class StatePresenter:
    """Handles state display and formatting"""

    @staticmethod
    def show_state(state: Dict):
        """Format and display installation state"""
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
            for entry in history[-3:]:
                action = entry.get('action', 'unknown')
                timestamp = entry.get('timestamp', 'unknown')
                if action == 'install_profile':
                    profile = entry.get('profile', 'unknown')
                    print(f"  {timestamp}: Installed profile '{profile}'")
                elif action == 'install_component':
                    component = entry.get('component', 'unknown')
                    print(f"  {timestamp}: Installed component '{component}'")
        print()


class ComponentPresenter:
    """Handles component display and formatting"""

    @staticmethod
    def list_all_components(manifest: Dict, plugin_system):
        """Format and display all components grouped by source"""
        # Separate base components from plugin components
        base_components = {}
        plugin_components = {}

        for component, config in manifest['components'].items():
            if plugin_system.is_plugin_component(component):
                plugin_name = plugin_system.get_plugin_name_for_component(component)
                if plugin_name not in plugin_components:
                    plugin_components[plugin_name] = {}
                plugin_components[plugin_name][component] = config
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

    @staticmethod
    def list_discovered_files(component: str, files: List[str]):
        """Format and display discovered files for a component"""
        print(f"Files for component '{component}':")
        if files:
            for file in files:
                print(f"  {file}")
        else:
            print("  No files found")


class ProfilePresenter:
    """Handles profile display and formatting"""

    @staticmethod
    def list_all_profiles(manifest: Dict):
        """Format and display all available profiles"""
        print("Available profiles:")
        for profile, config in manifest['profiles'].items():
            print(f"  {profile}: {config['description']}")
