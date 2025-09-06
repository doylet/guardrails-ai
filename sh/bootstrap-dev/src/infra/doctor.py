#!/usr/bin/env python3
"""
Doctor Module
Diagnostic and health check functionality
"""
import sys
import subprocess
import yaml
from pathlib import Path
from typing import Dict

from .utils import Colors
from .state_manager import StateManager
from .component_manager import ComponentManager


class Doctor:
    """Diagnostic and validation functionality"""

    def __init__(self, target_dir: Path, state_manager: StateManager, component_manager: ComponentManager):
        self.target_dir = target_dir
        self.state_manager = state_manager
        self.component_manager = component_manager

    def run_diagnostics(self, manifest: Dict, focus: str = "all") -> bool:
        """Diagnostic workflow - validate installation integrity"""
        print(Colors.bold("AI Guardrails Doctor - Installation Diagnostics"))
        print(Colors.info("=" * 50))

        issues_found = 0

        if focus == "yaml" or focus == "all":
            issues_found += self._check_yaml_structure()

        if focus == "all":
            issues_found += self._check_file_integrity(manifest)
            issues_found += self._check_component_status(manifest)
            issues_found += self._check_environment()

        print("\n" + Colors.info("=" * 50))
        if issues_found == 0:
            print(Colors.ok("✅ All checks passed - installation is healthy"))
        else:
            print(Colors.error(f"❌ Found {issues_found} issues that need attention"))

        return issues_found == 0

    def _check_yaml_structure(self) -> int:
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
                    if file_path.endswith('.json'):
                        import json
                        with open(full_path) as f:
                            json.load(f)
                    else:
                        with open(full_path) as f:
                            yaml.safe_load(f)
                    print(f"  {Colors.ok('[OK]')} {description}: valid structure")
                except Exception as e:
                    print(f"  {Colors.error('[ERROR]')} {description}: {e}")
                    issues += 1
            else:
                print(f"  {Colors.warn('[WARN]')} {description}: file not found")
                issues += 1

        return issues

    def _check_file_integrity(self, manifest: Dict) -> int:
        """Check if all expected files are present"""
        print("\nFile Integrity Check:")
        issues = 0

        for component, config in manifest['components'].items():
            # Only check components that are marked as installed
            if self.state_manager.is_component_installed(component):
                try:
                    files = self.component_manager.discover_files(component, manifest)
                    missing_files = []

                    for rel_file in files:
                        target_path = self.target_dir / rel_file
                        if not target_path.exists():
                            missing_files.append(rel_file)

                    if missing_files:
                        print(f"  {Colors.warn('[WARN]')} Component '{component}': {len(missing_files)} missing files")
                        issues += len(missing_files)
                    else:
                        print(f"  {Colors.ok('[OK]')} Component '{component}': all files present")

                except Exception as e:
                    print(f"  {Colors.error('[ERROR]')} Component '{component}': {e}")
                    issues += 1

        return issues

    def _check_component_status(self, manifest: Dict) -> int:
        """Check component installation status"""
        print("\nComponent Status Check:")
        issues = 0

        # Load state to see what components should be installed
        installed_components = self.state_manager.get_installed_components()

        # If no state exists, check all components (backward compatibility)
        if not installed_components:
            components_to_check = list(manifest['components'].keys())
            print(f"  {Colors.info('[INFO]')} No state file found, checking all components")
        else:
            components_to_check = installed_components

        for component in components_to_check:
            if component in manifest['components']:
                try:
                    files = self.component_manager.discover_files(component, manifest)
                    installed_files = sum(1 for f in files if (self.target_dir / f).exists())

                    if installed_files == len(files):
                        print(f"  {Colors.ok('[OK]')} Component '{component}': fully installed ({installed_files}/{len(files)} files)")
                    elif installed_files > 0:
                        print(f"  {Colors.warn('[WARN]')} Component '{component}': partially installed ({installed_files}/{len(files)} files)")
                        issues += 1
                    else:
                        print(f"  {Colors.error('[ERROR]')} Component '{component}': not installed (0/{len(files)} files)")
                        issues += 1

                except Exception as e:
                    print(f"  {Colors.error('[ERROR]')} Component '{component}': {e}")
                    issues += 1
            else:
                print(f"  {Colors.error('[ERROR]')} Component '{component}': not found in manifest")
                issues += 1

        return issues

    def _check_environment(self) -> int:
        """Check environment and dependencies"""
        print("\nEnvironment Check:")
        issues = 0

        # Check git repository
        if (self.target_dir / ".git").exists():
            print(f"  {Colors.ok('[OK]')} Git repository detected")
        else:
            print(f"  {Colors.warn('[WARN]')} Not a git repository - some features may not work")
            issues += 1

        # Check Python
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        print(f"  {Colors.ok('[OK]')} Python {python_version} available")

        # Check pre-commit
        try:
            result = subprocess.run(['pre-commit', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"  {Colors.ok('[OK]')} {version}")
            else:
                print(f"  {Colors.warn('[WARN]')} pre-commit not working properly")
                issues += 1
        except FileNotFoundError:
            print(f"  {Colors.error('[ERROR]')} pre-commit not installed")
            issues += 1

        return issues
