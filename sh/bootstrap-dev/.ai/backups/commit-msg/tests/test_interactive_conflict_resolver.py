#!/usr/bin/env python3
"""
Unit Tests for Interactive Conflict Resolution System

Tests the InteractiveConflictResolver class and integration with 
PathMerger for Phase 3 Task 3.1: Interactive Conflict Resolution.
"""

import json
import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from src.packages.core.interactive_conflict_resolver import (
    InteractiveConflictResolver, 
    ConflictResolution
)
from src.packages.core.schema_composer import PluginConflict


class TestConflictResolution:
    """Test ConflictResolution dataclass."""
    
    def test_conflict_resolution_creation(self):
        """Test basic ConflictResolution creation."""
        resolution = ConflictResolution(
            strategy="union",
            resolved_value=["test1", "test2"]
        )
        
        assert resolution.strategy == "union"
        assert resolution.resolved_value == ["test1", "test2"]
        assert resolution.chosen_plugin is None
        assert resolution.custom_value is None
        assert resolution.apply_to_similar is False
        assert resolution.resolved_at != ""
    
    def test_conflict_resolution_with_custom_timestamp(self):
        """Test ConflictResolution with pre-set timestamp."""
        timestamp = "2025-01-06T15:30:00"
        resolution = ConflictResolution(
            strategy="override",
            chosen_plugin="test-plugin",
            resolved_at=timestamp
        )
        
        assert resolution.resolved_at == timestamp


class TestInteractiveConflictResolver:
    """Test InteractiveConflictResolver class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "plugin_config.yaml"
        
    def test_resolver_initialization(self):
        """Test resolver initialization."""
        resolver = InteractiveConflictResolver(
            config_path=self.config_path,
            interactive=False
        )
        
        assert resolver.config_path == self.config_path
        assert resolver.interactive is False
        assert isinstance(resolver.saved_resolutions, dict)
        assert isinstance(resolver.session_resolutions, dict)
        assert isinstance(resolver.global_preferences, dict)
    
    def test_resolver_non_interactive_mode(self):
        """Test resolver defaults to non-interactive mode without tty."""
        with patch('sys.stdin.isatty', return_value=False):
            resolver = InteractiveConflictResolver(interactive=True)
            assert resolver.interactive is False
    
    def test_conflict_key_generation(self):
        """Test deterministic conflict key generation."""
        resolver = InteractiveConflictResolver(interactive=False)
        
        conflict1 = PluginConflict(
            type='file_overlap',
            plugins=['plugin-a', 'plugin-b'],
            path='.ai/config.yaml',
            message="Test conflict",
            severity='warning'
        )
        
        conflict2 = PluginConflict(
            type='file_overlap',
            plugins=['plugin-b', 'plugin-a'],  # Different order
            path='.ai/config.yaml',
            message="Different message",  # Different message
            severity='error'  # Different severity
        )
        
        key1 = resolver._generate_conflict_key(conflict1)
        key2 = resolver._generate_conflict_key(conflict2)
        
        # Should generate same key (plugins are sorted)
        assert key1 == key2
        assert len(key1) == 16  # MD5 hash truncated to 16 chars
    
    def test_merge_values_union_lists(self):
        """Test union merge for list values."""
        resolver = InteractiveConflictResolver(interactive=False)
        
        result = resolver._merge_values_union(
            ['*.tmp', '*.log'],
            ['*.tmp', '*.cache']
        )
        
        assert result == ['*.tmp', '*.log', '*.cache']
    
    def test_merge_values_union_dicts(self):
        """Test union merge for dictionary values."""
        resolver = InteractiveConflictResolver(interactive=False)
        
        result = resolver._merge_values_union(
            {'exclude': ['*.tmp'], 'type': 'config'},
            {'exclude': ['*.log'], 'version': '1.0'}
        )
        
        expected = {
            'exclude': ['*.tmp', '*.log'],
            'type': 'config',
            'version': '1.0'
        }
        assert result == expected
    
    def test_merge_values_union_strings(self):
        """Test union merge for string values."""
        resolver = InteractiveConflictResolver(interactive=False)
        
        # Same strings
        result = resolver._merge_values_union("test", "test")
        assert result == "test"
        
        # Different strings
        result = resolver._merge_values_union("hello", "world")
        assert result == "hello,world"
    
    def test_merge_values_union_numbers(self):
        """Test union merge for numeric values."""
        resolver = InteractiveConflictResolver(interactive=False)
        
        assert resolver._merge_values_union(5, 10) == 10
        assert resolver._merge_values_union(3.14, 2.71) == 3.14
    
    def test_merge_values_union_booleans(self):
        """Test union merge for boolean values."""
        resolver = InteractiveConflictResolver(interactive=False)
        
        assert resolver._merge_values_union(True, False) is True
        assert resolver._merge_values_union(False, True) is True
        assert resolver._merge_values_union(False, False) is False
    
    def test_non_interactive_conflict_resolution(self):
        """Test conflict resolution in non-interactive mode."""
        resolver = InteractiveConflictResolver(interactive=False)
        
        conflict = PluginConflict(
            type='property_conflict',
            plugins=['plugin-a', 'plugin-b'],
            path='.ai/config.yaml',
            message="Property conflict",
            severity='warning'
        )
        
        current_value = ['*.tmp', '*.log']
        new_value = ['*.tmp', '*.cache']
        
        resolution = resolver.resolve_conflict(conflict, current_value, new_value)
        
        assert resolution.strategy == "union"
        assert resolution.resolved_value == ['*.tmp', '*.log', '*.cache']
    
    def test_format_value_display(self):
        """Test value formatting for CLI display."""
        resolver = InteractiveConflictResolver(interactive=False)
        
        # Simple values
        assert resolver._format_value("test") == "test"
        assert resolver._format_value(42) == "42"
        assert resolver._format_value(True) == "True"
        
        # Complex values
        list_val = ['item1', 'item2']
        formatted = resolver._format_value(list_val)
        assert 'item1' in formatted and 'item2' in formatted
        
        dict_val = {'key': 'value'}
        formatted = resolver._format_value(dict_val)
        assert 'key' in formatted and 'value' in formatted
        
        # Long string
        long_string = "a" * 150
        formatted = resolver._format_value(long_string)
        assert len(formatted) <= 103  # 100 chars + "..."
        assert formatted.endswith("...")
    
    def test_preference_strategy_application(self):
        """Test applying global preference strategies."""
        resolver = InteractiveConflictResolver(interactive=False)
        
        conflict = PluginConflict(
            type='property_conflict',
            plugins=['plugin-a', 'plugin-b'],
            path='.ai/config.yaml',
            message="Test conflict",
            severity='warning'
        )
        
        current_value = "value_a"
        new_value = "value_b"
        
        # Test union preference
        resolution = resolver._apply_preference_strategy(
            "union", conflict, current_value, new_value
        )
        assert resolution.strategy == "union"
        assert resolution.resolved_value == "value_a,value_b"
        
        # Test override_first preference
        resolution = resolver._apply_preference_strategy(
            "override_first", conflict, current_value, new_value
        )
        assert resolution.strategy == "override"
        assert resolution.chosen_plugin == "plugin-a"
        assert resolution.resolved_value == current_value
        
        # Test override_last preference
        resolution = resolver._apply_preference_strategy(
            "override_last", conflict, current_value, new_value
        )
        assert resolution.strategy == "override"
        assert resolution.chosen_plugin == "plugin-b"
        assert resolution.resolved_value == new_value
        
        # Test skip preference
        resolution = resolver._apply_preference_strategy(
            "skip", conflict, current_value, new_value
        )
        assert resolution.strategy == "skip"
    
    def test_saved_resolution_reuse(self):
        """Test reusing saved conflict resolutions."""
        resolver = InteractiveConflictResolver(
            config_path=self.config_path,
            interactive=False
        )
        
        conflict = PluginConflict(
            type='file_overlap',
            plugins=['plugin-a', 'plugin-b'],
            path='.ai/config.yaml',
            message="Test conflict",
            severity='warning'
        )
        
        # Create a saved resolution
        conflict_key = resolver._generate_conflict_key(conflict)
        saved_resolution = ConflictResolution(
            strategy="override",
            chosen_plugin="plugin-a",
            resolved_value="saved_value"
        )
        resolver.saved_resolutions[conflict_key] = saved_resolution
        
        # Resolve conflict - should use saved resolution
        resolution = resolver.resolve_conflict(conflict, "current", "new")
        
        assert resolution.strategy == "override"
        assert resolution.chosen_plugin == "plugin-a"
        assert resolution.resolved_value == "saved_value"
    
    def test_global_preference_application(self):
        """Test applying global preferences for conflict types."""
        resolver = InteractiveConflictResolver(interactive=False)
        resolver.global_preferences['file_overlap'] = 'override_last'
        
        conflict = PluginConflict(
            type='file_overlap',
            plugins=['plugin-a', 'plugin-b'],
            path='.ai/config.yaml',
            message="Test conflict",
            severity='warning'
        )
        
        resolution = resolver.resolve_conflict(conflict, "current", "new")
        
        assert resolution.strategy == "override"
        assert resolution.chosen_plugin == "plugin-b"
        assert resolution.resolved_value == "new"
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_load_saved_resolutions(self, mock_yaml_load, mock_file):
        """Test loading saved resolutions from file."""
        # Mock configuration data
        config_data = {
            'conflict_resolutions': {
                'abc123': {
                    'strategy': 'union',
                    'resolved_value': ['merged', 'values'],
                    'resolved_at': '2025-01-06T15:30:00'
                }
            },
            'global_resolution_preferences': {
                'file_overlap': 'union'
            }
        }
        mock_yaml_load.return_value = config_data
        
        # Create resolver with existing config file
        with patch.object(Path, 'exists', return_value=True):
            resolver = InteractiveConflictResolver(config_path=self.config_path)
        
        # Verify resolutions were loaded
        assert len(resolver.saved_resolutions) == 1
        assert 'abc123' in resolver.saved_resolutions
        
        loaded_resolution = resolver.saved_resolutions['abc123']
        assert loaded_resolution.strategy == 'union'
        assert loaded_resolution.resolved_value == ['merged', 'values']
        
        # Verify global preferences were loaded
        assert resolver.global_preferences['file_overlap'] == 'union'
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.dump')
    def test_save_resolutions(self, mock_yaml_dump, mock_file):
        """Test saving resolutions to file."""
        resolver = InteractiveConflictResolver(
            config_path=self.config_path,
            interactive=False
        )
        
        # Add a resolution to save
        resolution = ConflictResolution(
            strategy="override",
            chosen_plugin="test-plugin",
            resolved_value="test_value"
        )
        resolver.saved_resolutions['test_key'] = resolution
        resolver.global_preferences['test_type'] = 'union'
        
        # Mock existing config file
        with patch.object(Path, 'exists', return_value=False):
            resolver._save_resolutions()
        
        # Verify file operations
        mock_file.assert_called()
        mock_yaml_dump.assert_called_once()
        
        # Check the data that would be saved
        call_args = mock_yaml_dump.call_args[0]
        saved_data = call_args[0]
        
        assert 'conflict_resolutions' in saved_data
        assert 'global_resolution_preferences' in saved_data
        assert saved_data['global_resolution_preferences']['test_type'] == 'union'
    
    def test_get_resolution_summary(self):
        """Test getting resolution summary."""
        resolver = InteractiveConflictResolver(interactive=False)
        
        # Add some test data
        resolver.saved_resolutions['key1'] = ConflictResolution(strategy="union")
        resolver.session_resolutions['key2'] = ConflictResolution(strategy="override")
        resolver.global_preferences['file_overlap'] = 'union'
        
        summary = resolver.get_resolution_summary()
        
        assert summary['saved_resolutions'] == 1
        assert summary['session_resolutions'] == 1
        assert summary['global_preferences']['file_overlap'] == 'union'
        assert summary['interactive_mode'] is False


class TestInteractivePrompting:
    """Test interactive prompting functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "plugin_config.yaml"
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_prompt_user_resolution_override_first(self, mock_print, mock_input):
        """Test user selecting first plugin override."""
        mock_input.return_value = '1'
        
        resolver = InteractiveConflictResolver(
            config_path=self.config_path,
            interactive=True
        )
        resolver.interactive = True  # Force interactive mode
        
        conflict = PluginConflict(
            type='file_overlap',
            plugins=['plugin-a', 'plugin-b'],
            path='.ai/config.yaml',
            message="Test conflict",
            severity='warning'
        )
        
        resolution = resolver._prompt_user_resolution(
            conflict, "value_a", "value_b"
        )
        
        assert resolution.strategy == "override"
        assert resolution.chosen_plugin == "plugin-a"
        assert resolution.resolved_value == "value_a"
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_prompt_user_resolution_union(self, mock_print, mock_input):
        """Test user selecting union strategy."""
        mock_input.return_value = '3'
        
        resolver = InteractiveConflictResolver(
            config_path=self.config_path,
            interactive=True
        )
        resolver.interactive = True
        
        conflict = PluginConflict(
            type='property_conflict',
            plugins=['plugin-a', 'plugin-b'],
            path='.ai/config.yaml',
            message="Test conflict",
            severity='warning'
        )
        
        resolution = resolver._prompt_user_resolution(
            conflict, ['item1'], ['item2']
        )
        
        assert resolution.strategy == "union"
        assert resolution.resolved_value == ['item1', 'item2']
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_prompt_user_resolution_quit(self, mock_print, mock_input):
        """Test user quitting to non-interactive mode."""
        mock_input.return_value = 'q'
        
        resolver = InteractiveConflictResolver(
            config_path=self.config_path,
            interactive=True
        )
        resolver.interactive = True
        
        conflict = PluginConflict(
            type='file_overlap',
            plugins=['plugin-a', 'plugin-b'],
            path='.ai/config.yaml',
            message="Test conflict",
            severity='warning'
        )
        
        resolution = resolver._prompt_user_resolution(
            conflict, "value_a", "value_b"
        )
        
        assert resolution.strategy == "union"
        assert resolver.interactive is False  # Should switch to non-interactive
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_prompt_custom_value_string(self, mock_print, mock_input):
        """Test prompting for custom string value."""
        mock_input.return_value = 'custom_value'
        
        resolver = InteractiveConflictResolver(interactive=True)
        resolver.interactive = True
        
        result = resolver._prompt_custom_value("existing", "new")
        assert result == "custom_value"
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_prompt_custom_value_list(self, mock_print, mock_input):
        """Test prompting for custom list value."""
        mock_input.return_value = 'item1,item2,item3'
        
        resolver = InteractiveConflictResolver(interactive=True)
        resolver.interactive = True
        
        result = resolver._prompt_custom_value(['existing'], ['new'])
        assert result == ['item1', 'item2', 'item3']
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_prompt_custom_value_json_list(self, mock_print, mock_input):
        """Test prompting for custom JSON list value."""
        mock_input.return_value = '["item1", "item2"]'
        
        resolver = InteractiveConflictResolver(interactive=True)
        resolver.interactive = True
        
        result = resolver._prompt_custom_value(['existing'], ['new'])
        assert result == ['item1', 'item2']
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_prompt_custom_value_invalid_retry(self, mock_print, mock_input):
        """Test handling invalid custom value with retry."""
        # First input is invalid JSON, second is valid
        mock_input.side_effect = ['{"invalid": json}', '{"valid": "json"}']
        
        resolver = InteractiveConflictResolver(interactive=True)
        resolver.interactive = True
        
        result = resolver._prompt_custom_value({'existing': 'value'}, {'new': 'value'})
        assert result == {'valid': 'json'}
        
        # Verify error message was printed
        assert mock_print.call_count >= 2  # At least error + prompt messages


if __name__ == '__main__':
    pytest.main([__file__])
