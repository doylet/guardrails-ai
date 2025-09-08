#!/usr/bin/env python3
"""
Configuration Manager Module
Handles pre-commit and other configuration customization
"""
import yaml
import subprocess
from pathlib import Path
from typing import Dict, List

from ..utils import Colors
from ..operations import YAMLOperations


class ConfigManager:
    """Manages configuration file customization"""

    def __init__(self, target_dir: Path):
        self.target_dir = target_dir

    def customize_precommit_config(self):
        """Customize .pre-commit-config.yaml based on guardrails.yaml settings"""
        guardrails_path = self.target_dir / ".ai" / "guardrails.yaml"
        precommit_path = self.target_dir / ".pre-commit-config.yaml"

        if not guardrails_path.exists() or not precommit_path.exists():
            return

        try:
            with open(guardrails_path) as f:
                guardrails = yaml.safe_load(f) or {}

            with open(precommit_path) as f:
                precommit_config = yaml.safe_load(f) or {}

            # Get disabled languages from guardrails config
            disabled_languages = []
            if 'precommit' in guardrails and 'disabled_languages' in guardrails['precommit']:
                disabled_languages = guardrails['precommit']['disabled_languages'] or []

            # Always apply language exclusions (even if empty list, to set up the pattern)
            self.apply_language_exclusions(precommit_config, disabled_languages)

            # Write back the customized config
            with open(precommit_path, 'w') as f:
                yaml.dump(precommit_config, f, default_flow_style=False, sort_keys=False, indent=2)

            print(f"  {Colors.ok('[OK]')} Customized pre-commit configuration")
            if disabled_languages:
                print(f"  {Colors.info('[INFO]')} Disabled languages: {', '.join(disabled_languages)}")

        except Exception as e:
            print(f"  {Colors.warn('[WARN]')} Failed to customize pre-commit config: {e}")

    def apply_language_exclusions(self, precommit_config: Dict, disabled_languages: List[str]):
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
                exclude_patterns.append(f"({language_file_patterns[lang]})")

        if exclude_patterns:
            combined_exclude = '|'.join(exclude_patterns)

            # Apply exclude pattern to lang-lint hook
            for repo in precommit_config.get('repos', []):
                if repo.get('repo') == 'local':
                    for hook in repo.get('hooks', []):
                        if hook.get('id') == 'lang-lint':
                            hook['exclude'] = combined_exclude
                            break

    def merge_yaml_file(self, src_path: Path, target_path: Path):
        """Merge YAML/JSON files by combining their contents while preserving format"""
        try:
            # Load both files
            with open(src_path) as f:
                src_data = yaml.safe_load(f) or {}

            if target_path.exists():
                target_data = YAMLOperations.load_yaml_file(target_path)
            else:
                target_data = {}

            # Special handling for .pre-commit-config.yaml: preserve custom exclude patterns
            preserved_excludes = {}
            if target_path.name == '.pre-commit-config.yaml' and 'repos' in target_data:
                for repo in target_data.get('repos', []):
                    if repo.get('repo') == 'local':
                        for hook in repo.get('hooks', []):
                            if hook.get('exclude'):
                                preserved_excludes[hook.get('id')] = hook['exclude']

            # Merge the data
            merged_data = YAMLOperations.deep_merge_dict(target_data, src_data)

            # Restore preserved exclude patterns for .pre-commit-config.yaml
            if target_path.name == '.pre-commit-config.yaml' and preserved_excludes:
                for repo in merged_data.get('repos', []):
                    if repo.get('repo') == 'local':
                        for hook in repo.get('hooks', []):
                            hook_id = hook.get('id')
                            if hook_id in preserved_excludes:
                                hook['exclude'] = preserved_excludes[hook_id]

            # Write back the merged result in the original format
            with open(target_path, 'w') as f:
                yaml.dump(merged_data, f, default_flow_style=False, sort_keys=False, indent=2)

        except Exception as e:
            # Fallback to copy if merge fails
            print(f"  merge failed, copying instead: {e}")
            import shutil
            shutil.copy2(src_path, target_path)

    def install_precommit_hooks(self):
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
