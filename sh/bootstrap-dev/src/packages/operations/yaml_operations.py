#!/usr/bin/env python3
"""
YAML Operations Module
Utilities for merging and manipulating YAML configurations
"""
import yaml


class YAMLOperations:
    """Utilities for YAML merging and manipulation"""

    @staticmethod
    def clean_yaml_nulls(data: dict):
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
                    current = None
                    break
            else:
                # Fix null values in list fields
                if current and field_path[-1] in current and current[field_path[-1]] is None:
                    current[field_path[-1]] = []

    @staticmethod
    def deep_merge_dict(target: dict, source: dict) -> dict:
        """Deep merge two dictionaries with smart array handling"""
        result = target.copy()

        for key, value in source.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = YAMLOperations.deep_merge_dict(result[key], value)
                elif isinstance(result[key], list) and isinstance(value, list):
                    # Smart array merging based on content type
                    if key == 'repos':
                        result[key] = YAMLOperations.merge_precommit_repos(result[key], value)
                    else:
                        # Simple list merging - avoid duplicates
                        merged_list = result[key].copy()
                        for item in value:
                            if item not in merged_list:
                                merged_list.append(item)
                        result[key] = merged_list
                else:
                    # Source value overwrites target
                    result[key] = value
            else:
                result[key] = value

        return result

    @staticmethod
    def merge_precommit_repos(target_repos: list, source_repos: list) -> list:
        """Intelligently merge pre-commit repos arrays"""
        result = []

        # Create lookup maps by repo URL for efficient merging
        target_map = {repo.get('repo'): repo for repo in target_repos if isinstance(repo, dict)}
        source_map = {repo.get('repo'): repo for repo in source_repos if isinstance(repo, dict)}

        # Add all repos from target first (preserves existing structure)
        for repo in target_repos:
            if isinstance(repo, dict) and repo.get('repo'):
                repo_url = repo['repo']
                if repo_url in source_map:
                    # Merge with source version
                    result.append(YAMLOperations.merge_repo_configs(repo, source_map[repo_url]))
                else:
                    result.append(repo)
            else:
                result.append(repo)

        # Add any source repos that weren't in target
        for repo_url, repo in source_map.items():
            if repo_url not in target_map:
                result.append(repo)

        return result

    @staticmethod
    def merge_repo_configs(target_repo: dict, source_repo: dict) -> dict:
        """Merge individual repo configurations"""
        result = target_repo.copy()

        for key, value in source_repo.items():
            if key == 'hooks' and 'hooks' in result:
                result[key] = YAMLOperations.merge_hooks(result[key], value)
            elif key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = YAMLOperations.deep_merge_dict(result[key], value)
            else:
                result[key] = value

        return result

    @staticmethod
    def merge_hooks(target_hooks: list, source_hooks: list) -> list:
        """Merge hooks arrays, preserving existing hooks and their configurations"""
        result = []

        # Create lookup map by hook ID
        target_map = {hook.get('id'): hook for hook in target_hooks if isinstance(hook, dict)}
        source_map = {hook.get('id'): hook for hook in source_hooks if isinstance(hook, dict)}

        # Add all hooks from target first (preserves existing configurations)
        for hook in target_hooks:
            if isinstance(hook, dict) and hook.get('id'):
                hook_id = hook['id']
                if hook_id in source_map:
                    # Merge with source version
                    result.append(YAMLOperations.merge_hook_configs(hook, source_map[hook_id]))
                else:
                    result.append(hook)
            else:
                result.append(hook)

        # Add any source hooks that weren't in target
        for hook_id, hook in source_map.items():
            if hook_id not in target_map:
                result.append(hook)

        return result

    @staticmethod
    def merge_hook_configs(target_hook: dict, source_hook: dict) -> dict:
        """Merge individual hook configurations, preserving custom exclude patterns"""
        result = target_hook.copy()

        for key, value in source_hook.items():
            if key == 'exclude':
                # Preserve custom exclude patterns - don't overwrite with template defaults
                if 'exclude' not in result or result['exclude'] == '':
                    result[key] = value
                # If target has custom exclude, keep it
            elif key in result and isinstance(result[key], list) and isinstance(value, list):
                # Merge arrays without duplicates
                merged_list = result[key].copy()
                for item in value:
                    if item not in merged_list:
                        merged_list.append(item)
                result[key] = merged_list
            else:
                result[key] = value

        return result

    @staticmethod
    def load_yaml_file(file_path) -> dict:
        """Load YAML file with error handling"""
        try:
            with open(file_path) as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    @staticmethod
    def save_yaml_file(file_path, data: dict):
        """Save YAML file with consistent formatting"""
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)
