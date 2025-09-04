#!/usr/bin/env python3
"""
Dynamic Bootstrap Component Manager
Reads bootstrap-config.yaml and manages component installation
"""

import yaml
import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Set, Any
import json

class BootstrapManager:
    def __init__(self, config_path: str, template_repo: str):
        self.config_path = Path(config_path)
        self.template_repo = Path(template_repo)
        self.config = self._load_config()
        self.target_dir = Path.cwd()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load and validate bootstrap configuration"""
        with open(self.config_path) as f:
            config = yaml.safe_load(f)
        
        # Validate required sections
        required_sections = ['components', 'profiles']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required section: {section}")
        
        return config
    
    def detect_environment(self) -> Dict[str, bool]:
        """Detect current environment capabilities"""
        env = {}
        
        if 'environment_detection' in self.config:
            for check_name, check_config in self.config['environment_detection'].items():
                try:
                    result = subprocess.run(
                        check_config['check'], 
                        shell=True, 
                        capture_output=True,
                        text=True
                    )
                    env[check_name] = result.returncode == 0
                except Exception:
                    env[check_name] = False
        
        return env
    
    def resolve_dependencies(self, selected_components: List[str]) -> List[str]:
        """Resolve component dependencies in correct order"""
        resolved = []
        visited = set()
        
        def resolve_component(comp_name: str):
            if comp_name in visited:
                return
            
            visited.add(comp_name)
            component = self.config['components'].get(comp_name)
            
            if not component:
                raise ValueError(f"Unknown component: {comp_name}")
            
            # Resolve dependencies first
            for dep in component.get('depends_on', []):
                resolve_component(dep)
            
            if comp_name not in resolved:
                resolved.append(comp_name)
        
        for comp in selected_components:
            resolve_component(comp)
        
        return resolved
    
    def filter_by_environment(self, component: Dict[str, Any], env: Dict[str, bool]) -> List[Dict[str, Any]]:
        """Filter component files based on environment conditions"""
        filtered_files = []
        
        for file_config in component.get('files', []):
            # Check conditions
            conditions = file_config.get('conditions', [])
            if conditions:
                meets_conditions = True
                for condition in conditions:
                    for env_key, required in condition.items():
                        if env.get(env_key, False) != required:
                            meets_conditions = False
                            break
                    if not meets_conditions:
                        break
                
                if meets_conditions:
                    filtered_files.append(file_config)
            else:
                filtered_files.append(file_config)
        
        return filtered_files
    
    def install_component(self, comp_name: str, env: Dict[str, bool], force: bool = False) -> bool:
        """Install a single component"""
        component = self.config['components'][comp_name]
        
        print(f"Installing component: {component.get('name', comp_name)}")
        
        # Filter files by environment
        files_to_install = self.filter_by_environment(component, env)
        
        success = True
        for file_config in files_to_install:
            source_path = self.template_repo / file_config['source']
            target_path = self.target_dir / file_config['target']
            
            # Create target directory
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists and force not set
            if target_path.exists() and not force:
                print(f"  skip (exists): {target_path}")
                continue
            
            try:
                # Copy file
                if source_path.exists():
                    import shutil
                    shutil.copy2(source_path, target_path)
                    print(f"  installed: {target_path}")
                    
                    # Set permissions if specified
                    if 'permissions' in file_config:
                        os.chmod(target_path, int(file_config['permissions'], 8))
                        
                elif file_config.get('embedded_fallback'):
                    print(f"  warning: Using embedded fallback for {target_path}")
                    # Would call embedded fallback function here
                else:
                    print(f"  error: Template not found: {source_path}")
                    success = False
                    
            except Exception as e:
                print(f"  error: Failed to install {target_path}: {e}")
                success = False
        
        # Run post-install commands
        for cmd in component.get('post_install', []):
            try:
                subprocess.run(cmd, shell=True, check=True, cwd=self.target_dir)
                print(f"  post-install: {cmd}")
            except subprocess.CalledProcessError as e:
                print(f"  post-install error: {cmd} failed: {e}")
        
        return success
    
    def install_profile(self, profile_name: str, force: bool = False) -> bool:
        """Install a predefined profile"""
        if profile_name not in self.config['profiles']:
            raise ValueError(f"Unknown profile: {profile_name}")
        
        profile = self.config['profiles'][profile_name]
        components = profile['components']
        
        print(f"Installing profile: {profile.get('description', profile_name)}")
        
        env = self.detect_environment()
        print(f"Environment: {env}")
        
        # Resolve dependencies
        ordered_components = self.resolve_dependencies(components)
        
        success = True
        for comp_name in ordered_components:
            if not self.install_component(comp_name, env, force):
                success = False
        
        # Update .gitignore
        if self.config.get('settings', {}).get('update_gitignore', True):
            self._update_gitignore()
        
        return success
    
    def _update_gitignore(self):
        """Update .gitignore with specified entries"""
        gitignore_path = self.target_dir / '.gitignore'
        entries = self.config.get('settings', {}).get('gitignore_entries', [])
        
        if not entries:
            return
        
        existing_entries = set()
        if gitignore_path.exists():
            with open(gitignore_path) as f:
                existing_entries = {line.strip() for line in f if line.strip()}
        
        new_entries = [entry for entry in entries if entry not in existing_entries]
        
        if new_entries:
            with open(gitignore_path, 'a') as f:
                if existing_entries:  # Add newline if file has content
                    f.write('\n')
                f.write('\n'.join(new_entries) + '\n')
            print(f"Updated .gitignore with {len(new_entries)} entries")
    
    def list_components(self):
        """List available components"""
        print("Available components:")
        for comp_name, component in self.config['components'].items():
            required = "required" if component.get('required') else "optional"
            deps = component.get('depends_on', [])
            deps_str = f" (depends on: {', '.join(deps)})" if deps else ""
            print(f"  {comp_name}: {component.get('name', comp_name)} [{required}]{deps_str}")
    
    def list_profiles(self):
        """List available installation profiles"""
        print("Available profiles:")
        for profile_name, profile in self.config['profiles'].items():
            components = ', '.join(profile['components'])
            print(f"  {profile_name}: {profile.get('description', profile_name)}")
            print(f"    Components: {components}")

def main():
    parser = argparse.ArgumentParser(description='Dynamic AI Guardrails Bootstrap Manager')
    parser.add_argument('--config', default='bootstrap-config.yaml', help='Bootstrap configuration file')
    parser.add_argument('--template-repo', default='src/ai-guardrails-templates', help='Template repository path')
    parser.add_argument('--force', action='store_true', help='Overwrite existing files')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Install profile command
    install_parser = subparsers.add_parser('install', help='Install a profile')
    install_parser.add_argument('profile', help='Profile name to install')
    
    # List commands
    subparsers.add_parser('list-components', help='List available components')
    subparsers.add_parser('list-profiles', help='List available profiles')
    
    # Environment detection
    subparsers.add_parser('detect-env', help='Detect current environment')
    
    args = parser.parse_args()
    
    try:
        manager = BootstrapManager(args.config, args.template_repo)
        
        if args.command == 'install':
            success = manager.install_profile(args.profile, args.force)
            sys.exit(0 if success else 1)
        elif args.command == 'list-components':
            manager.list_components()
        elif args.command == 'list-profiles':
            manager.list_profiles()
        elif args.command == 'detect-env':
            env = manager.detect_environment()
            print(json.dumps(env, indent=2))
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
