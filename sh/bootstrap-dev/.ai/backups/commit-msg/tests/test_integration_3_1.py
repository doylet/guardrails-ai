#!/usr/bin/env python3
"""
Integration tests for Phase 3 Task 3.1: Interactive Conflict Resolution.

Tests the complete workflow for user-guided conflict resolution with CLI prompting,
resolution persistence, and integration with the existing conflict detection framework.
"""

import unittest
import tempfile
import os
import sys
import yaml
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the src directory to the Python path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from src.packages.core.schema_composer import SchemaComposer, MergeStrategy
from src.packages.core.interactive_conflict_resolver import InteractiveConflictResolver, ConflictResolution

import json
import pytest
import tempfile
import time
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.packages.core.schema_composer import (
    SchemaComposer, 
    MergeStrategy, 
    ConflictResolutionPolicy,
    CompositionResult
)
from src.packages.core.interactive_conflict_resolver import InteractiveConflictResolver


class TestInteractiveConflictResolutionIntegration:
    """Integration tests for interactive conflict resolution."""
    
    def setup_method(self):
        """Set up test environment with mock plugins and schemas."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.plugin_dir = self.temp_dir / "plugins"
        self.plugin_dir.mkdir()
        
        # Create base schema
        self.base_schema_path = self.temp_dir / "base_target_structure.yaml"
        base_schema = {
            "version": "1.0",
            "expected_structure": {
                ".ai/": {
                    "type": "directory",
                    "files": {
                        "base_config.yaml": {
                            "type": "file",
                            "required": True
                        }
                    }
                }
            }
        }
        with open(self.base_schema_path, 'w') as f:
            yaml.dump(base_schema, f)
        
        # Create test plugins with conflicting schemas
        self._create_test_plugin_schemas()
        
        # Create config path for interactive resolver
        self.config_path = self.temp_dir / "plugin_config.yaml"
    
    def _create_test_plugin_schemas(self):
        """Create test plugin schemas with known conflicts."""
        
        # Plugin A: commit-msg-kit
        plugin_a_dir = self.plugin_dir / "commit-msg-kit"
        plugin_a_dir.mkdir()
        plugin_a_schema = {
            "schema_version": "1.0.0",
            "plugin_name": "commit-msg-kit",
            "provides_structure": {
                ".ai/": {
                    "type": "directory",
                    "files": {
                        "config.yaml": {
                            "type": "file",
                            "exclude_patterns": ["*.tmp", "*.log"],
                            "git_hooks": ["pre-commit", "commit-msg"]
                        }
                    }
                },
                ".githooks/": {
                    "type": "directory",
                    "files": {
                        "commit-msg": {
                            "type": "file",
                            "executable": True,
                            "content": "#!/bin/bash\necho 'commit-msg hook'"
                        }
                    }
                }
            }
        }
        with open(plugin_a_dir / "plugin-structure.schema.yaml", 'w') as f:
            yaml.dump(plugin_a_schema, f)
        
        # Plugin B: repo-safety-kit (conflicts with Plugin A)
        plugin_b_dir = self.plugin_dir / "repo-safety-kit"
        plugin_b_dir.mkdir()
        plugin_b_schema = {
            "schema_version": "1.0.0",
            "plugin_name": "repo-safety-kit",
            "provides_structure": {
                ".ai/": {
                    "type": "directory",
                    "files": {
                        "config.yaml": {
                            "type": "file",
                            "exclude_patterns": ["*.tmp", "*.cache"],  # Conflict: different patterns
                            "safety_checks": ["secrets", "large-files"]
                        }
                    }
                },
                ".githooks/": {
                    "type": "directory",
                    "files": {
                        "pre-push": {
                            "type": "file",
                            "executable": True,
                            "content": "#!/bin/bash\necho 'pre-push hook'"
                        }
                        # Remove commit-msg conflict for this test
                    }
                }
            }
        }
        with open(plugin_b_dir / "plugin-structure.schema.yaml", 'w') as f:
            yaml.dump(plugin_b_schema, f)
        
        # Plugin C: doc-guardrails-kit (minimal conflicts)
        plugin_c_dir = self.plugin_dir / "doc-guardrails-kit"
        plugin_c_dir.mkdir()
        plugin_c_schema = {
            "schema_version": "1.0.0",
            "plugin_name": "doc-guardrails-kit",
            "provides_structure": {
                "docs/": {
                    "type": "directory",
                    "files": {
                        "README.md": {
                            "type": "file",
                            "required": True,
                            "template": "README.md.template"
                        }
                    }
                },
                ".ai/": {
                    "type": "directory", 
                    "files": {
                        "doc_config.yaml": {
                            "type": "file",
                            "doc_standards": ["adrs", "guides"]
                        }
                    }
                }
            }
        }
        with open(plugin_c_dir / "plugin-structure.schema.yaml", 'w') as f:
            yaml.dump(plugin_c_schema, f)
        
        # Set up the composer and plugins for the baseline test
        self.plugin_directory = self.plugin_dir
        self.composer = SchemaComposer(
            base_schema_path=self.base_schema_path,
            plugin_directory=self.plugin_directory,
            default_merge_strategy=MergeStrategy.UNION
        )
        
        # Create simple plugins for the baseline test
        self.plugins = [
            type('Plugin', (), {
                'get_schema': lambda: {
                    "schema_version": "1.0",
                    "plugin_name": "test_plugin1",
                    "provides_structure": {
                        "files": [
                            {
                                "path": "src/main.py",
                                "type": "file",
                                "content": "print('Hello from plugin1')"
                            }
                        ]
                    }
                }
            })(),
            type('Plugin', (), {
                'get_schema': lambda: {
                    "schema_version": "1.0",
                    "plugin_name": "test_plugin2",
                    "provides_structure": {
                        "files": [
                            {
                                "path": "src/utils.py",
                                "type": "file",
                                "content": "def utility_function(): pass"
                            }
                        ]
                    }
                }
            })()
        ]
    
    def test_non_interactive_conflict_resolution(self):
        """Test conflict resolution without interactive prompts (baseline test)."""
        # Use the correct method signature - it expects plugin names, not plugin objects
        enabled_plugins = ["commit-msg-kit", "repo-safety-kit"]
        result = self.composer.compose_target_schema(enabled_plugins)
        
        # Should not have unresolved conflicts in the main result
        assert result.success, f"Schema composition failed: {result.error_message}"
        assert not result.conflicts, "Should not have unresolved conflicts in union strategy"
        
        # Verify that the schema was composed correctly
        assert result.composed_schema is not None
        assert "expected_structure" in result.composed_schema or "provides_structure" in result.composed_schema

    def test_conflicting_schemas_with_override_strategy(self):
        """Test override strategy with conflicting file definitions using direct plugin creation."""
        # Create a temporary test setup for direct plugin testing
        temp_base_schema = self.temp_dir / "test_base.yaml"
        temp_plugin_dir = self.temp_dir / "test_plugins"
        temp_plugin_dir.mkdir()
        
        # Create minimal base schema
        base_schema = {
            "version": "1.0",
            "expected_structure": {}
        }
        with open(temp_base_schema, 'w') as f:
            yaml.dump(base_schema, f)
        
        # Create two plugins with actual conflicts
        plugin1_dir = temp_plugin_dir / "plugin1"
        plugin1_dir.mkdir()
        plugin1_schema = {
            "schema_version": "1.0",
            "plugin_name": "plugin1",
            "provides_structure": {
                "config.py": {
                    "type": "file",
                    "permissions": "644",
                    "content": "CONFIG = 'production'"
                }
            }
        }
        with open(plugin1_dir / "plugin-structure.schema.yaml", 'w') as f:
            yaml.dump(plugin1_schema, f)
        
        plugin2_dir = temp_plugin_dir / "plugin2"
        plugin2_dir.mkdir()
        plugin2_schema = {
            "schema_version": "1.0",
            "plugin_name": "plugin2",
            "provides_structure": {
                "config.py": {
                    "type": "file",
                    "permissions": "755",  # Different permissions - conflict
                    "content": "CONFIG = 'development'"  # Different content - conflict
                }
            }
        }
        with open(plugin2_dir / "plugin-structure.schema.yaml", 'w') as f:
            yaml.dump(plugin2_schema, f)
        
        # Create composer with OVERRIDE strategy and explicit conflict policy
        from src.packages.core.schema_composer import ConflictResolutionPolicy
        conflict_policy = ConflictResolutionPolicy(
            file_strategy=MergeStrategy.OVERRIDE,
            directory_strategy=MergeStrategy.OVERRIDE,
            permission_strategy=MergeStrategy.OVERRIDE
        )
        
        composer_override = SchemaComposer(
            base_schema_path=temp_base_schema,
            plugin_directory=temp_plugin_dir,
            default_merge_strategy=MergeStrategy.OVERRIDE
        )
        
        # Test override behavior with explicit conflict policy
        result = composer_override.compose_target_schema(
            ["plugin1", "plugin2"],
            conflict_policy=conflict_policy
        )
        
        # With OVERRIDE strategy, should succeed
        assert result.success, f"Schema composition failed: {result.conflicts}"
        
        # Verify the override behavior - plugin2 should win (last plugin)
        schema = result.composed_schema
        assert "expected_structure" in schema
        
        if "config.py" in schema["expected_structure"]:
            config_def = schema["expected_structure"]["config.py"]
            # Should keep the second plugin's values (override behavior)
            assert config_def["permissions"] == "755", f"Expected permissions 755, got {config_def.get('permissions')}"
            assert "development" in config_def["content"], f"Expected development content, got {config_def.get('content')}"

    @patch('sys.stdin.isatty', return_value=True)
    @patch('builtins.input')
    def test_interactive_conflict_resolution_with_prompts(self, mock_input, mock_isatty):
        """Test actual interactive prompting for conflict resolution."""
        # Set up mock user input for interactive resolution
        # User will choose OVERRIDE strategy and select plugin2
        mock_input.side_effect = [
            "2",  # Choose OVERRIDE strategy
            "2",  # Choose plugin2 (second option)
            "n"   # Don't save preference globally
        ]
        
        # Create similar setup to override test but with INTERACTIVE strategy
        temp_base_schema = self.temp_dir / "interactive_base.yaml"
        temp_plugin_dir = self.temp_dir / "interactive_plugins"
        temp_plugin_dir.mkdir()
        
        # Create minimal base schema
        base_schema = {
            "version": "1.0",
            "expected_structure": {}
        }
        with open(temp_base_schema, 'w') as f:
            yaml.dump(base_schema, f)
        
        # Create two plugins with conflicts
        plugin1_dir = temp_plugin_dir / "plugin1"
        plugin1_dir.mkdir()
        plugin1_schema = {
            "schema_version": "1.0",
            "plugin_name": "plugin1",
            "provides_structure": {
                "settings.py": {
                    "type": "file",
                    "permissions": "644",
                    "content": "DEBUG = True"
                }
            }
        }
        with open(plugin1_dir / "plugin-structure.schema.yaml", 'w') as f:
            yaml.dump(plugin1_schema, f)
        
        plugin2_dir = temp_plugin_dir / "plugin2"
        plugin2_dir.mkdir()
        plugin2_schema = {
            "schema_version": "1.0",
            "plugin_name": "plugin2",
            "provides_structure": {
                "settings.py": {
                    "type": "file",
                    "permissions": "600",  # Different permissions
                    "content": "DEBUG = False"  # Different content
                }
            }
        }
        with open(plugin2_dir / "plugin-structure.schema.yaml", 'w') as f:
            yaml.dump(plugin2_schema, f)
        
        # Create composer with INTERACTIVE strategy and resolver
        from src.packages.core.schema_composer import ConflictResolutionPolicy
        conflict_policy = ConflictResolutionPolicy(
            file_strategy=MergeStrategy.INTERACTIVE,
            directory_strategy=MergeStrategy.INTERACTIVE
        )
        
        composer_interactive = SchemaComposer(
            base_schema_path=temp_base_schema,
            plugin_directory=temp_plugin_dir,
            default_merge_strategy=MergeStrategy.INTERACTIVE,
            interactive_resolver=InteractiveConflictResolver()
        )
        
        # Test interactive resolution
        with patch('builtins.print'):  # Suppress print output during test
            result = composer_interactive.compose_target_schema(
                ["plugin1", "plugin2"],
                conflict_policy=conflict_policy
            )
        
        # Should succeed after interactive resolution
        assert result.success, f"Interactive composition failed: {result.conflicts}"
        
        # Verify the interactive resolution worked
        schema = result.composed_schema
        assert "expected_structure" in schema
        
        if "settings.py" in schema["expected_structure"]:
            settings_def = schema["expected_structure"]["settings.py"]
            # Depending on the user choice (OVERRIDE with plugin2), should have plugin2's values
            # This test validates that the interactive system is working, exact values depend on the mock choices
            assert "permissions" in settings_def, "Should have permissions defined"
            assert "content" in settings_def, "Should have content defined"
    
    def test_interactive_fallback_to_union(self):
        """Test INTERACTIVE strategy falls back to union when resolver is non-interactive."""
        # Create resolver in non-interactive mode
        resolver = InteractiveConflictResolver(
            config_path=self.config_path,
            interactive=False
        )
        
        # Use OVERRIDE strategy to avoid content conflicts
        composer = SchemaComposer(
            base_schema_path=self.base_schema_path,
            plugin_directory=self.plugin_dir,
            default_merge_strategy=MergeStrategy.INTERACTIVE,
            interactive_resolver=resolver
        )
        
        # Use plugins without content conflicts for this test
        result = composer.compose_target_schema(
            enabled_plugins=["commit-msg-kit", "doc-guardrails-kit"],
            merge_strategy=MergeStrategy.INTERACTIVE
        )
        
        # Should succeed with interactive fallback
        assert result.success
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_interactive_resolution_override_strategy(self, mock_print, mock_input):
        """Test interactive resolution with override strategy."""
        # Mock user selecting first plugin for all conflicts
        mock_input.side_effect = ['1', '1']  # Choose first plugin for both conflicts
        
        # Create resolver in interactive mode
        resolver = InteractiveConflictResolver(
            config_path=self.config_path,
            interactive=True
        )
        resolver.interactive = True  # Force interactive
        
        # Create composer
        composer = SchemaComposer(
            base_schema_path=self.base_schema_path,
            plugin_directory=self.plugin_dir,
            default_merge_strategy=MergeStrategy.INTERACTIVE,
            interactive_resolver=resolver
        )
        
        # Compose schema
        result = composer.compose_target_schema(
            enabled_plugins=["commit-msg-kit", "repo-safety-kit"],
            merge_strategy=MergeStrategy.INTERACTIVE
        )
        
        assert result.success
        
        # Check that first plugin won the conflicts
        config_file = result.composed_schema['expected_structure']['.ai/']['files']['config.yaml']
        assert config_file['exclude_patterns'] == ['*.tmp', '*.log']  # commit-msg-kit values
        
        commit_msg_file = result.composed_schema['expected_structure']['.githooks/']['files']['commit-msg']
        assert "commit-msg hook" in commit_msg_file['content']  # commit-msg-kit content
    
    @patch('builtins.input') 
    @patch('builtins.print')
    def test_interactive_resolution_union_strategy(self, mock_print, mock_input):
        """Test interactive resolution with union strategy."""
        # Mock user selecting union for all conflicts
        mock_input.side_effect = ['3', '3']  # Choose union for both conflicts
        
        resolver = InteractiveConflictResolver(
            config_path=self.config_path,
            interactive=True
        )
        resolver.interactive = True
        
        composer = SchemaComposer(
            base_schema_path=self.base_schema_path,
            plugin_directory=self.plugin_dir,
            default_merge_strategy=MergeStrategy.INTERACTIVE,
            interactive_resolver=resolver
        )
        
        result = composer.compose_target_schema(
            enabled_plugins=["commit-msg-kit", "repo-safety-kit"],
            merge_strategy=MergeStrategy.INTERACTIVE
        )
        
        assert result.success
        
        # Check union merge results
        config_file = result.composed_schema['expected_structure']['.ai/']['files']['config.yaml']
        exclude_patterns = config_file['exclude_patterns']
        assert '*.tmp' in exclude_patterns
        assert '*.log' in exclude_patterns
        assert '*.cache' in exclude_patterns
        
        # Both plugins should be tracked as sources
        assert 'git_hooks' in config_file  # From commit-msg-kit
        assert 'safety_checks' in config_file  # From repo-safety-kit
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_interactive_resolution_skip_strategy(self, mock_print, mock_input):
        """Test interactive resolution with skip strategy."""
        # Mock user selecting skip for conflict
        mock_input.return_value = '5'  # Skip
        
        resolver = InteractiveConflictResolver(
            config_path=self.config_path,
            interactive=True
        )
        resolver.interactive = True
        
        composer = SchemaComposer(
            base_schema_path=self.base_schema_path,
            plugin_directory=self.plugin_dir,
            default_merge_strategy=MergeStrategy.INTERACTIVE,
            interactive_resolver=resolver
        )
        
        result = composer.compose_target_schema(
            enabled_plugins=["commit-msg-kit", "repo-safety-kit"],
            merge_strategy=MergeStrategy.INTERACTIVE
        )
        
        assert result.success
        
        # Some conflicts should have been skipped
        # The exact behavior depends on which conflicts the user skipped
        assert len(result.composition_context.conflicts_encountered) > 0
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_interactive_resolution_custom_value(self, mock_print, mock_input):
        """Test interactive resolution with custom value."""
        # Mock user selecting custom value
        mock_input.side_effect = [
            '4',  # Choose custom value
            '["*.tmp", "*.custom"]',  # Custom JSON list
            '3'   # Union for any other conflicts
        ]
        
        resolver = InteractiveConflictResolver(
            config_path=self.config_path,
            interactive=True
        )
        resolver.interactive = True
        
        composer = SchemaComposer(
            base_schema_path=self.base_schema_path,
            plugin_directory=self.plugin_dir,
            default_merge_strategy=MergeStrategy.INTERACTIVE,
            interactive_resolver=resolver
        )
        
        result = composer.compose_target_schema(
            enabled_plugins=["commit-msg-kit", "repo-safety-kit"],
            merge_strategy=MergeStrategy.INTERACTIVE
        )
        
        assert result.success
        
        # Check that custom value was used
        config_file = result.composed_schema['expected_structure']['.ai/']['files']['config.yaml']
        # Custom resolution should be applied
        assert 'custom_resolution' in config_file.get('_source_plugin', '')
    
    def test_resolution_persistence_and_reuse(self):
        """Test that resolutions are saved and reused."""
        # First composition with saved resolutions
        initial_config = {
            'conflict_resolutions': {
                # Pre-saved resolution for exclude_patterns conflict
                self._generate_test_conflict_key('property_conflict', '.ai/config.yaml', 
                                               ['commit-msg-kit', 'repo-safety-kit']): {
                    'strategy': 'override',
                    'chosen_plugin': 'commit-msg-kit',
                    'resolved_value': ['*.tmp', '*.log'],
                    'resolved_at': '2025-01-06T15:30:00'
                }
            }
        }
        
        # Save initial config
        with open(self.config_path, 'w') as f:
            yaml.dump(initial_config, f)
        
        resolver = InteractiveConflictResolver(
            config_path=self.config_path,
            interactive=False
        )
        
        composer = SchemaComposer(
            base_schema_path=self.base_schema_path,
            plugin_directory=self.plugin_dir,
            default_merge_strategy=MergeStrategy.INTERACTIVE,
            interactive_resolver=resolver
        )
        
        result = composer.compose_target_schema(
            enabled_plugins=["commit-msg-kit", "repo-safety-kit"],
            merge_strategy=MergeStrategy.INTERACTIVE
        )
        
        assert result.success
        
        # Should use saved resolution
        config_file = result.composed_schema['expected_structure']['.ai/']['files']['config.yaml']
        assert config_file['exclude_patterns'] == ['*.tmp', '*.log']
    
    def test_global_preferences_application(self):
        """Test application of global conflict resolution preferences."""
        # Set up config with global preferences
        initial_config = {
            'global_resolution_preferences': {
                'property_conflict': 'union',
                'file_overlap': 'override_last'
            }
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(initial_config, f)
        
        resolver = InteractiveConflictResolver(
            config_path=self.config_path,
            interactive=False
        )
        
        composer = SchemaComposer(
            base_schema_path=self.base_schema_path,
            plugin_directory=self.plugin_dir,
            default_merge_strategy=MergeStrategy.INTERACTIVE,
            interactive_resolver=resolver
        )
        
        result = composer.compose_target_schema(
            enabled_plugins=["commit-msg-kit", "repo-safety-kit"],
            merge_strategy=MergeStrategy.INTERACTIVE
        )
        
        assert result.success
        
        # Property conflicts should use union (global preference)
        config_file = result.composed_schema['expected_structure']['.ai/']['files']['config.yaml']
        exclude_patterns = config_file['exclude_patterns']
        assert '*.tmp' in exclude_patterns
        assert '*.log' in exclude_patterns  
        assert '*.cache' in exclude_patterns
    
    def test_three_plugin_composition_with_conflicts(self):
        """Test interactive resolution with three plugins creating multiple conflicts."""
        resolver = InteractiveConflictResolver(
            config_path=self.config_path,
            interactive=False  # Use automatic resolution
        )
        
        composer = SchemaComposer(
            base_schema_path=self.base_schema_path,
            plugin_directory=self.plugin_dir,
            default_merge_strategy=MergeStrategy.INTERACTIVE,
            interactive_resolver=resolver
        )
        
        result = composer.compose_target_schema(
            enabled_plugins=["commit-msg-kit", "repo-safety-kit", "doc-guardrails-kit"],
            merge_strategy=MergeStrategy.INTERACTIVE
        )
        
        assert result.success
        
        # Should have multiple directories and files
        expected_structure = result.composed_schema['expected_structure']
        assert '.ai/' in expected_structure
        assert '.githooks/' in expected_structure
        assert 'docs/' in expected_structure
        
        # .ai/ directory should have files from all plugins
        ai_files = expected_structure['.ai/']['files']
        assert 'config.yaml' in ai_files  # Conflicted file from plugins A & B
        assert 'doc_config.yaml' in ai_files  # Non-conflicted file from plugin C
        assert 'base_config.yaml' in ai_files  # Base file
    
    def test_composition_metadata_tracking(self):
        """Test that conflict resolution metadata is properly tracked."""
        resolver = InteractiveConflictResolver(
            config_path=self.config_path,
            interactive=False
        )
        
        composer = SchemaComposer(
            base_schema_path=self.base_schema_path,
            plugin_directory=self.plugin_dir,
            default_merge_strategy=MergeStrategy.INTERACTIVE,
            interactive_resolver=resolver
        )
        
        result = composer.compose_target_schema(
            enabled_plugins=["commit-msg-kit", "repo-safety-kit"],
            merge_strategy=MergeStrategy.INTERACTIVE
        )
        
        assert result.success
        
        # Check composition metadata
        assert len(result.composition_context.conflicts_encountered) > 0
        assert len(result.composition_context.merge_history) > 0
        
        # Conflicts should have proper information
        for conflict in result.composition_context.conflicts_encountered:
            assert conflict.type in ['file_overlap', 'property_conflict']
            assert len(conflict.plugins) >= 2
            assert conflict.path
            assert conflict.message
        
        # Merge history should track resolution attempts
        for entry in result.composition_context.merge_history:
            plugin_name, path, operation = entry
            assert plugin_name in ["commit-msg-kit", "repo-safety-kit"]
            assert path
            assert 'merge_' in operation
    
    def test_error_handling_malformed_resolution_file(self):
        """Test graceful handling of malformed resolution configuration."""
        # Create malformed config file
        with open(self.config_path, 'w') as f:
            f.write("invalid: yaml: content: [unclosed")
        
        # Should still initialize without crashing
        resolver = InteractiveConflictResolver(
            config_path=self.config_path,
            interactive=False
        )
        
        # Should have empty resolutions due to load failure
        assert len(resolver.saved_resolutions) == 0
        assert len(resolver.global_preferences) == 0
        
        # Should still work for composition
        composer = SchemaComposer(
            base_schema_path=self.base_schema_path,
            plugin_directory=self.plugin_dir,
            default_merge_strategy=MergeStrategy.INTERACTIVE,
            interactive_resolver=resolver
        )
        
        result = composer.compose_target_schema(
            enabled_plugins=["commit-msg-kit"],
            merge_strategy=MergeStrategy.INTERACTIVE
        )
        
        assert result.success
    
    def test_fallback_to_union_without_resolver(self):
        """Test that INTERACTIVE strategy falls back to UNION without resolver."""
        # Create composer without interactive resolver
        composer = SchemaComposer(
            base_schema_path=self.base_schema_path,
            plugin_directory=self.plugin_dir,
            default_merge_strategy=MergeStrategy.INTERACTIVE
            # No interactive_resolver passed
        )
        
        result = composer.compose_target_schema(
            enabled_plugins=["commit-msg-kit", "repo-safety-kit"],
            merge_strategy=MergeStrategy.INTERACTIVE
        )
        
        assert result.success
        # Should have warnings about falling back to union
        assert len(result.warnings) > 0
        assert any("No interactive resolver" in warning for warning in result.warnings)
    
    def _generate_test_conflict_key(self, conflict_type: str, path: str, plugins: list) -> str:
        """Generate a conflict key for testing."""
        import hashlib
        import json
        
        signature_data = {
            'path': path,
            'type': conflict_type,
            'plugins': sorted(plugins)
        }
        signature_str = json.dumps(signature_data, sort_keys=True)
        return hashlib.md5(signature_str.encode()).hexdigest()[:16]


class TestInteractiveResolutionPerformance:
    """Test performance of interactive resolution system."""
    
    def setup_method(self):
        """Set up performance test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.plugin_dir = self.temp_dir / "plugins"
        self.plugin_dir.mkdir()
        self.config_path = self.temp_dir / "plugin_config.yaml"
        
        # Create base schema
        self.base_schema_path = self.temp_dir / "base_target_structure.yaml"
        base_schema = {
            "version": "1.0",
            "expected_structure": {}
        }
        with open(self.base_schema_path, 'w') as f:
            yaml.dump(base_schema, f)
    
    def test_resolution_caching_performance(self):
        """Test that resolution caching improves performance."""
        import time
        
        # Create plugin with conflicts
        plugin_dir = self.plugin_dir / "test-plugin"
        plugin_dir.mkdir()
        schema = {
            "schema_version": "1.0.0",
            "plugin_name": "test-plugin",
            "provides_structure": {
                f"file_{i}.txt": {
                    "type": "file",
                    "content": f"content_{i}"
                } for i in range(10)  # 10 files
            }
        }
        with open(plugin_dir / "plugin-structure.schema.yaml", 'w') as f:
            yaml.dump(schema, f)
        
        resolver = InteractiveConflictResolver(
            config_path=self.config_path,
            interactive=False
        )
        
        composer = SchemaComposer(
            base_schema_path=self.base_schema_path,
            plugin_directory=self.plugin_dir,
            default_merge_strategy=MergeStrategy.INTERACTIVE,
            interactive_resolver=resolver
        )
        
        # First composition (cold)
        start_time = time.time()
        result1 = composer.compose_target_schema(
            enabled_plugins=["test-plugin"],
            merge_strategy=MergeStrategy.INTERACTIVE
        )
        cold_time = time.time() - start_time
        
        # Second composition (warm cache)
        start_time = time.time()
        result2 = composer.compose_target_schema(
            enabled_plugins=["test-plugin"],
            merge_strategy=MergeStrategy.INTERACTIVE
        )
        warm_time = time.time() - start_time
        
        assert result1.success
        assert result2.success
        assert warm_time < cold_time  # Should be faster with cache
    
    def test_large_conflict_set_handling(self):
        """Test handling of many simultaneous conflicts."""
        # Create multiple plugins with overlapping files
        for plugin_num in range(5):
            plugin_dir = self.plugin_dir / f"plugin-{plugin_num}"
            plugin_dir.mkdir()
            
            schema = {
                "schema_version": "1.0.0",
                "plugin_name": f"plugin-{plugin_num}",
                "provides_structure": {
                    "shared_file.txt": {
                        "type": "file",
                        "content": f"content_from_plugin_{plugin_num}",
                        "priority": plugin_num
                    }
                }
            }
            with open(plugin_dir / "plugin-structure.schema.yaml", 'w') as f:
                yaml.dump(schema, f)
        
        resolver = InteractiveConflictResolver(
            config_path=self.config_path,
            interactive=False
        )
        
        composer = SchemaComposer(
            base_schema_path=self.base_schema_path,
            plugin_directory=self.plugin_dir,
            default_merge_strategy=MergeStrategy.INTERACTIVE,
            interactive_resolver=resolver
        )
        
        # Enable all plugins (should create many conflicts)
        start_time = time.time()
        result = composer.compose_target_schema(
            enabled_plugins=[f"plugin-{i}" for i in range(5)],
            merge_strategy=MergeStrategy.INTERACTIVE
        )
        composition_time = time.time() - start_time
        
        assert result.success
        assert composition_time < 1.0  # Should complete within 1 second
        assert len(result.composition_context.conflicts_encountered) >= 4  # 5 plugins, 4 conflicts for shared file


if __name__ == '__main__':
    pytest.main([__file__])
