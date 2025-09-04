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
    def __init__(self, manifest_path: str, template_repo: str, target_dir: str = "."):
        self.manifest_path = Path(manifest_path)
        self.template_repo = Path(template_repo)
        self.target_dir = Path(target_dir)
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> Dict:
        """Load installation manifest"""
        with open(self.manifest_path) as f:
            return yaml.safe_load(f)

    def discover_files(self, component: str) -> List[str]:
        """Dynamically discover files based on patterns - NO hardcoding!"""
        if component not in self.manifest['file_patterns']:
            raise ValueError(f"Unknown component: {component}")

        component_config = self.manifest['file_patterns'][component]
        patterns = component_config['patterns']

        discovered = []
        for pattern in patterns:
            # Search in template repository
            search_path = self.template_repo / pattern
            matches = glob.glob(str(search_path), recursive=True)
            discovered.extend(matches)

        # Convert to relative paths from template repo
        relative_files = []
        for file_path in discovered:
            if os.path.isfile(file_path):
                rel_path = os.path.relpath(file_path, self.template_repo)
                relative_files.append(rel_path)

        return relative_files

    def install_component(self, component: str, force: bool = False) -> bool:
        """Install a specific component"""
        try:
            files = self.discover_files(component)
            
            print(f"Installing component: {component}")
            
            success = True
            for rel_file in files:
                src_path = self.template_repo / rel_file
                target_path = self.target_dir / rel_file

                # Create target directory if needed
                target_path.parent.mkdir(parents=True, exist_ok=True)

                if target_path.exists() and not force:
                    print(f"  skip (exists): {rel_file}")
                    continue

                try:
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

    def install_profile(self, profile: str, force: bool = False) -> bool:
        """Install a profile"""
        if profile not in self.manifest['profiles']:
            raise ValueError(f"Unknown profile: {profile}")

        profile_config = self.manifest['profiles'][profile]
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
        """List all available components and what they install"""
        print("Available components (discovered dynamically):")
        for component, config in self.manifest['file_patterns'].items():
            files = self.discover_files(component)
            print(f"  {component}: {config['description']} ({len(files)} files)")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Infrastructure-as-Code Bootstrap Manager')
    parser.add_argument('--manifest', default='installation-manifest.yaml',
                       help='Installation manifest file')
    parser.add_argument('--template-repo', default='src/ai-guardrails-templates',
                       help='Template repository path')
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
        elif args.command == 'discover':
            bootstrap.list_discovered_files(args.component)
        else:
            parser.print_help()

    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == '__main__':
    main()
