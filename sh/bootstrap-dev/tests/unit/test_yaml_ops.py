"""Unit tests for the yaml_ops adapter.

Tests YAML/JSON operations, template processing, and format validation.
"""

import pytest
import tempfile
import shutil
import json
import yaml
from pathlib import Path

from src.packages.adapters.yaml_ops import YamlOpsAdapter
from src.packages.domain.errors import TransactionError


class TestYamlOpsAdapter:
    """Test YAML operations adapter functionality."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def yaml_ops(self, temp_workspace):
        """Create YamlOpsAdapter for testing."""
        return YamlOpsAdapter(target_dir=temp_workspace)

    def test_yaml_merge_deep_strategy(self, yaml_ops):
        """Test deep merge strategy for YAML content."""
        base_content = """
config:
  database:
    host: localhost
    port: 5432
  features:
    - auth
    - logging
"""

        overlay_content = """
config:
  database:
    port: 3306
    ssl: true
  features:
    - monitoring
  new_section:
    enabled: true
"""

        result = yaml_ops.merge_yaml(base_content, overlay_content, "deep")
        merged_data = yaml.safe_load(result)

        # Check deep merge results
        assert merged_data['config']['database']['host'] == 'localhost'  # preserved
        assert merged_data['config']['database']['port'] == 3306  # overridden
        assert merged_data['config']['database']['ssl'] is True  # added
        assert 'auth' in merged_data['config']['features']  # preserved
        assert 'monitoring' in merged_data['config']['features']  # added
        assert merged_data['config']['new_section']['enabled'] is True  # added

    def test_yaml_merge_shallow_strategy(self, yaml_ops):
        """Test shallow merge strategy for YAML content."""
        base_content = """
section1:
  key1: value1
  key2: value2
section2:
  key3: value3
"""

        overlay_content = """
section1:
  key2: new_value2
section3:
  key4: value4
"""

        result = yaml_ops.merge_yaml(base_content, overlay_content, "shallow")
        merged_data = yaml.safe_load(result)

        # Check shallow merge results
        assert merged_data['section1']['key2'] == 'new_value2'  # overridden
        assert 'key1' not in merged_data['section1']  # lost in shallow merge
        assert merged_data['section2']['key3'] == 'value3'  # preserved
        assert merged_data['section3']['key4'] == 'value4'  # added

    def test_yaml_merge_replace_strategy(self, yaml_ops):
        """Test replace strategy for YAML content."""
        base_content = """
keep_this:
  data: should_be_lost
"""

        overlay_content = """
new_data:
  value: replaces_everything
"""

        result = yaml_ops.merge_yaml(base_content, overlay_content, "replace")
        merged_data = yaml.safe_load(result)

        # Check replace results
        assert 'keep_this' not in merged_data
        assert merged_data['new_data']['value'] == 'replaces_everything'

    def test_json_merge_operations(self, yaml_ops):
        """Test JSON merge operations."""
        base_content = '{"config": {"timeout": 30, "retries": 3}}'
        overlay_content = '{"config": {"timeout": 60}, "logging": {"level": "info"}}'

        result = yaml_ops.merge_json(base_content, overlay_content, "deep")
        merged_data = json.loads(result)

        # Check JSON merge results
        assert merged_data['config']['timeout'] == 60  # overridden
        assert merged_data['config']['retries'] == 3  # preserved
        assert merged_data['logging']['level'] == 'info'  # added

    def test_simple_template_processing(self, yaml_ops):
        """Test simple template variable substitution."""
        template_content = """
Hello {{ name }}!
Your environment is {{ environment }}.
Debug mode: {{ debug }}
"""

        variables = {
            'name': 'World',
            'environment': 'production',
            'debug': False
        }

        result = yaml_ops.process_template(template_content, variables)

        assert 'Hello World!' in result
        assert 'Your environment is production.' in result
        assert 'Debug mode: False' in result

    def test_template_with_missing_variables(self, yaml_ops):
        """Test template processing with missing variables."""
        template_content = "Hello {{ name }}! Missing: {{ missing_var }}"
        variables = {'name': 'World'}

        # Should not raise error, just leave unreplaced variables
        result = yaml_ops.process_template(template_content, variables)

        assert 'Hello World!' in result
        assert '{{ missing_var }}' in result  # Should remain unreplaced

    def test_content_transformation_copy(self, yaml_ops, temp_workspace):
        """Test content transformation with COPY action."""
        # Create source file
        source_file = temp_workspace / "source.txt"
        source_file.write_text("Original content")

        target_file = temp_workspace / "target.txt"

        result = yaml_ops.transform_content(
            source_file, target_file, "COPY"
        )

        assert result == "Original content"

    def test_content_transformation_template(self, yaml_ops, temp_workspace):
        """Test content transformation with TEMPLATE action."""
        # Create template source file
        source_file = temp_workspace / "template.txt"
        source_file.write_text("Hello {{ name }}, welcome to {{ app }}!")

        target_file = temp_workspace / "output.txt"

        variables = {'name': 'Alice', 'app': 'MyApp'}

        result = yaml_ops.transform_content(
            source_file, target_file, "TEMPLATE", variables
        )

        assert result == "Hello Alice, welcome to MyApp!"

    def test_content_transformation_yaml_merge(self, yaml_ops, temp_workspace):
        """Test content transformation with YAML MERGE action."""
        # Create source YAML file
        source_file = temp_workspace / "overlay.yaml"
        source_file.write_text("config:\n  debug: true\n  new_key: value")

        # Create target YAML file
        target_file = temp_workspace / "base.yaml"
        target_file.write_text("config:\n  debug: false\n  existing: data")

        result = yaml_ops.transform_content(
            source_file, target_file, "MERGE"
        )

        merged_data = yaml.safe_load(result)
        assert merged_data['config']['debug'] is True  # overridden
        assert merged_data['config']['existing'] == 'data'  # preserved
        assert merged_data['config']['new_key'] == 'value'  # added

    def test_yaml_validation(self, yaml_ops):
        """Test YAML content validation."""
        # Valid YAML
        valid_yaml = "key: value\nlist:\n  - item1\n  - item2"
        errors = yaml_ops.validate_yaml(valid_yaml)
        assert len(errors) == 0

        # Invalid YAML
        invalid_yaml = "key: value\n  invalid: indentation\nno colon here"
        errors = yaml_ops.validate_yaml(invalid_yaml)
        assert len(errors) > 0
        assert "Invalid YAML" in errors[0]

    def test_json_validation(self, yaml_ops):
        """Test JSON content validation."""
        # Valid JSON
        valid_json = '{"key": "value", "array": [1, 2, 3]}'
        errors = yaml_ops.validate_json(valid_json)
        assert len(errors) == 0

        # Invalid JSON
        invalid_json = '{"key": "value", "missing": quote}'
        errors = yaml_ops.validate_json(invalid_json)
        assert len(errors) > 0
        assert "Invalid JSON" in errors[0]

    def test_variable_extraction_yaml(self, yaml_ops):
        """Test variable extraction from YAML content."""
        yaml_content = """
name: TestApp
version: 1.0.0
config:
  debug: true
  database:
    host: localhost
"""

        variables = yaml_ops.extract_variables(yaml_content, "yaml")

        assert variables['name'] == 'TestApp'
        assert variables['version'] == '1.0.0'
        assert variables['config']['debug'] is True
        assert variables['config']['database']['host'] == 'localhost'

    def test_variable_extraction_json(self, yaml_ops):
        """Test variable extraction from JSON content."""
        json_content = '{"app": "MyApp", "settings": {"theme": "dark"}}'

        variables = yaml_ops.extract_variables(json_content, "json")

        assert variables['app'] == 'MyApp'
        assert variables['settings']['theme'] == 'dark'

    def test_variable_extraction_env_format(self, yaml_ops):
        """Test variable extraction from environment format."""
        env_content = """
# Configuration
APP_NAME=TestApp
DEBUG=true
DATABASE_URL=postgresql://localhost:5432/test
EMPTY_VAR=

# Comment line
QUOTED_VALUE="with spaces"
"""

        variables = yaml_ops.extract_variables(env_content, "env")

        assert variables['APP_NAME'] == 'TestApp'
        assert variables['DEBUG'] == 'true'
        assert variables['DATABASE_URL'] == 'postgresql://localhost:5432/test'
        assert variables['EMPTY_VAR'] == ''
        assert variables['QUOTED_VALUE'] == 'with spaces'

    def test_content_type_detection(self, yaml_ops, temp_workspace):
        """Test content type detection from file extensions."""
        # Test YAML files
        yaml_file = temp_workspace / "test.yaml"
        assert yaml_ops.get_content_type(yaml_file) == "yaml"

        yml_file = temp_workspace / "test.yml"
        assert yaml_ops.get_content_type(yml_file) == "yaml"

        # Test JSON files
        json_file = temp_workspace / "test.json"
        assert yaml_ops.get_content_type(json_file) == "json"

        # Test template files
        template_file = temp_workspace / "test.j2"
        assert yaml_ops.get_content_type(template_file) == "template"

        jinja_file = temp_workspace / "test.jinja"
        assert yaml_ops.get_content_type(jinja_file) == "template"

        # Test other files
        text_file = temp_workspace / "test.txt"
        assert yaml_ops.get_content_type(text_file) == "text"

    def test_mergeable_file_detection(self, yaml_ops, temp_workspace):
        """Test detection of mergeable file types."""
        yaml1 = temp_workspace / "file1.yaml"
        yaml2 = temp_workspace / "file2.yml"
        json1 = temp_workspace / "file1.json"
        json2 = temp_workspace / "file2.json"
        text1 = temp_workspace / "file1.txt"
        text2 = temp_workspace / "file2.txt"

        # YAML files should be mergeable with each other
        assert yaml_ops.is_mergeable(yaml1, yaml2)

        # JSON files should be mergeable with each other
        assert yaml_ops.is_mergeable(json1, json2)

        # Different types should not be mergeable
        assert not yaml_ops.is_mergeable(yaml1, json1)
        assert not yaml_ops.is_mergeable(yaml1, text1)
        assert not yaml_ops.is_mergeable(text1, text2)

    def test_receipt_format_validation(self, yaml_ops):
        """Test validation of receipt format."""
        # Valid receipt
        valid_receipt = {
            'component_id': 'test-component',
            'installed_at': '2024-01-01T12:00:00Z',
            'manifest_hash': 'a' * 64,
            'files': [
                {
                    'target_path': 'test.txt',
                    'action_type': 'copy',
                    'content_hash': 'b' * 64
                }
            ],
            'metadata': {'version': '1.0'}
        }

        errors = yaml_ops.validate_receipt_format(valid_receipt)
        assert len(errors) == 0

        # Invalid receipt - missing required field
        invalid_receipt = {
            'component_id': 'test-component',
            # missing installed_at
            'manifest_hash': 'a' * 64,
            'files': []
        }

        errors = yaml_ops.validate_receipt_format(invalid_receipt)
        assert len(errors) > 0
        assert any('Missing required field: installed_at' in error for error in errors)

        # Invalid manifest hash
        invalid_hash_receipt = {
            'component_id': 'test-component',
            'installed_at': '2024-01-01T12:00:00Z',
            'manifest_hash': 'invalid_hash',  # Too short
            'files': []
        }

        errors = yaml_ops.validate_receipt_format(invalid_hash_receipt)
        assert len(errors) > 0
        assert any('64-character SHA256' in error for error in errors)

    def test_envelope_format_validation(self, yaml_ops):
        """Test validation of Copilot envelope format."""
        # Valid envelope
        valid_envelope = {
            'discovery': [
                {
                    'path': 'src/test.py',
                    'evidence': 'function test()',
                    'why': 'test function'
                }
            ],
            'plan': ['Step 1', 'Step 2'],
            'changes': [
                {
                    'path': 'src/test.py',
                    'patch': 'diff content'
                }
            ],
            'validation': {
                'commands': ['pytest'],
                'results': ['all green']
            }
        }

        errors = yaml_ops.validate_envelope_format(valid_envelope)
        assert len(errors) == 0

        # Invalid envelope - missing required field
        invalid_envelope = {
            'discovery': [],
            'plan': [],
            # missing changes and validation
        }

        errors = yaml_ops.validate_envelope_format(invalid_envelope)
        assert len(errors) >= 2  # missing changes and validation
        assert any('Missing required envelope field: changes' in error for error in errors)
        assert any('Missing required envelope field: validation' in error for error in errors)

    def test_configuration_merge_multiple_files(self, yaml_ops, temp_workspace):
        """Test merging multiple configuration files."""
        # Create base config
        base_config = temp_workspace / "base.yaml"
        base_config.write_text("""
app:
  name: MyApp
  version: 1.0.0
database:
  host: localhost
  port: 5432
""")

        # Create overlay configs
        env_config = temp_workspace / "env.yaml"
        env_config.write_text("""
app:
  environment: production
database:
  ssl: true
logging:
  level: info
""")

        feature_config = temp_workspace / "features.yaml"
        feature_config.write_text("""
app:
  features:
    - auth
    - monitoring
cache:
  enabled: true
""")

        # Merge configurations
        result = yaml_ops.merge_configuration(
            base_config,
            [env_config, feature_config],
            output_format="yaml"
        )

        merged_data = yaml.safe_load(result)

        # Verify merge results
        assert merged_data['app']['name'] == 'MyApp'  # from base
        assert merged_data['app']['version'] == '1.0.0'  # from base
        assert merged_data['app']['environment'] == 'production'  # from env
        assert 'auth' in merged_data['app']['features']  # from features
        assert merged_data['database']['host'] == 'localhost'  # from base
        assert merged_data['database']['ssl'] is True  # from env
        assert merged_data['logging']['level'] == 'info'  # from env
        assert merged_data['cache']['enabled'] is True  # from features

    def test_render_template_adapter_interface(self, yaml_ops, temp_workspace):
        """Test the render_template adapter interface for backwards compatibility."""
        # Create template file
        template_file = temp_workspace / "template.txt"
        template_file.write_text("Hello {{ name }}, version {{ version }}")

        variables = {'name': 'World', 'version': '2.0'}

        result = yaml_ops.render_template(str(template_file), variables)

        assert result == "Hello World, version 2.0"

    def test_error_handling(self, yaml_ops, temp_workspace):
        """Test error handling in various operations."""
        # Test invalid YAML merge
        with pytest.raises(TransactionError, match="YAML merge failed"):
            yaml_ops.merge_yaml("valid: yaml", "invalid: yaml: content:", "deep")

        # Test invalid JSON merge
        with pytest.raises(TransactionError, match="JSON merge failed"):
            yaml_ops.merge_json('{"valid": "json"}', '{"invalid": json}', "deep")

        # Test missing source file transformation
        nonexistent_file = temp_workspace / "nonexistent.txt"
        target_file = temp_workspace / "target.txt"

        with pytest.raises(TransactionError, match="Content transformation failed"):
            yaml_ops.transform_content(nonexistent_file, target_file, "COPY")

        # Test invalid template variables
        with pytest.raises(TransactionError, match="Variable extraction failed"):
            yaml_ops.extract_variables("invalid: yaml: content:", "yaml")
