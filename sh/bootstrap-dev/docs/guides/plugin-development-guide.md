# Plugin Development Guide: AI Guardrails Bootstrap System

## Overview

This guide provides comprehensive instructions for developing custom plugins for the AI Guardrails Bootstrap System. Plugins extend the system's functionality by adding new components, templates, and installation behaviors while integrating seamlessly with the core architecture.

## Plugin Architecture

### Plugin Structure

Each plugin follows a standardized directory structure:

```
plugins/my-plugin/
├── plugin-manifest.yaml          # Plugin metadata and configuration
├── components/                   # Component definitions
│   ├── component-1/
│   │   ├── files/               # Source files to install
│   │   └── manifest.yaml        # Component-specific configuration
│   └── component-2/
│       ├── files/
│       └── manifest.yaml
├── templates/                    # Template files for processing
│   ├── config.template.yml
│   └── workflow.template.yml
├── hooks/                       # Lifecycle hooks (optional)
│   ├── pre-install.sh
│   ├── post-install.sh
│   └── validate.sh
└── docs/                        # Plugin documentation
    ├── README.md
    └── examples/
```

### Core Components

#### 1. Plugin Manifest (`plugin-manifest.yaml`)

The plugin manifest defines metadata, dependencies, and components:

```yaml
# plugin-manifest.yaml
version: "1.0"
name: "my-custom-plugin"
description: "Custom plugin for specialized workflows"
author: "Your Organization"
license: "MIT"
homepage: "https://github.com/yourorg/my-custom-plugin"

# Plugin metadata
metadata:
  version: "1.2.0"
  compatibility: ">=1.0.0"
  tags: ["workflow", "automation", "custom"]

# Dependencies on other plugins
dependencies:
  - plugin: "core-files"
    version: ">=1.0.0"
    required: true
  - plugin: "git-hooks"
    version: ">=0.5.0"
    required: false

# Components provided by this plugin
components:
  custom-workflow:
    description: "Custom workflow configuration"
    priority: 100
    dependencies: ["core-files"]

  advanced-templates:
    description: "Advanced template configurations"
    priority: 200
    dependencies: ["custom-workflow"]

# Plugin-level configuration
configuration:
  default_branch: "main"
  enable_validation: true
  template_engine: "jinja2"
```

#### 2. Component Manifests (`components/*/manifest.yaml`)

Each component has its own manifest defining installation behavior:

```yaml
# components/custom-workflow/manifest.yaml
version: "1.0"
name: "custom-workflow"
description: "Custom workflow configuration files"

# File operations for this component
files:
  # Direct file copy
  - source: "workflow.yml"
    target: ".github/workflows/custom.yml"
    action: "copy"
    mode: 0644

  # Template processing with variables
  - source: "config.template.yml"
    target: ".ai/custom-config.yml"
    action: "template"
    mode: 0600
    variables:
      project_name: "{{ env.PROJECT_NAME | default('my-project') }}"
      debug_mode: "{{ config.debug | default(false) }}"

  # YAML merge operation
  - source: "merge-config.yml"
    target: ".ai/config.yml"
    action: "merge"
    merge_strategy: "deep"

  # Conditional file based on environment
  - source: "prod-settings.yml"
    target: ".ai/prod-config.yml"
    action: "copy"
    condition: "{{ env.ENVIRONMENT == 'production' }}"

# Component-specific hooks
hooks:
  pre_install: "hooks/pre-install.sh"
  post_install: "hooks/post-install.sh"
  validate: "hooks/validate.sh"

# Component configuration schema
configuration_schema:
  type: "object"
  properties:
    enable_notifications:
      type: "boolean"
      default: true
    notification_channels:
      type: "array"
      items:
        type: "string"
```

## Development Workflow

### 1. Setup Development Environment

```bash
# Create plugin directory structure
mkdir -p plugins/my-plugin/{components,templates,hooks,docs}
cd plugins/my-plugin

# Initialize plugin manifest
cat > plugin-manifest.yaml << EOF
version: "1.0"
name: "my-plugin"
description: "My custom plugin"
author: "$(git config user.name)"
metadata:
  version: "0.1.0"
components: {}
EOF
```

### 2. Create Your First Component

```bash
# Create component directory
mkdir -p components/my-component/files

# Create component manifest
cat > components/my-component/manifest.yaml << EOF
version: "1.0"
name: "my-component"
description: "My first component"
files:
  - source: "example.yml"
    target: ".ai/example.yml"
    action: "copy"
    mode: 0644
EOF

# Create source file
cat > components/my-component/files/example.yml << EOF
# Example configuration file
config:
  name: "my-component"
  version: "1.0"
  enabled: true
EOF
```

### 3. Test Your Plugin

```bash
# Test plugin validation
ai-guardrails doctor --plugin my-plugin

# Preview installation plan
ai-guardrails plan --plugin my-plugin --component my-component

# Dry run installation
ai-guardrails install --plugin my-plugin --component my-component --dry-run

# Install for testing
ai-guardrails install --plugin my-plugin --component my-component --verbose
```

## Advanced Features

### Template Processing

Plugins support advanced template processing with Jinja2:

```yaml
# components/advanced-templates/files/config.template.yml
project:
  name: "{{ project.name | default('unnamed-project') }}"
  version: "{{ project.version | default('1.0.0') }}"

environment:
  {% if env.ENVIRONMENT == 'production' %}
  debug: false
  log_level: "INFO"
  {% else %}
  debug: true
  log_level: "DEBUG"
  {% endif %}

features:
  {% for feature in features | default([]) %}
  - name: "{{ feature.name }}"
    enabled: {{ feature.enabled | default(true) | lower }}
  {% endfor %}

# Conditional sections
{% if enable_database %}
database:
  host: "{{ database.host | default('localhost') }}"
  port: {{ database.port | default(5432) }}
  name: "{{ database.name | default('app_db') }}"
{% endif %}
```

### YAML Merging Strategies

Support for sophisticated YAML merging:

```yaml
# components/config-merger/manifest.yaml
files:
  - source: "base-config.yml"
    target: ".ai/config.yml"
    action: "merge"
    merge_strategy: "deep"        # Deep merge objects and arrays

  - source: "overrides.yml"
    target: ".ai/config.yml"
    action: "merge"
    merge_strategy: "replace"     # Replace entire sections

  - source: "additions.yml"
    target: ".ai/config.yml"
    action: "merge"
    merge_strategy: "append"      # Append to arrays, merge objects
```

### Lifecycle Hooks

Implement custom behavior with lifecycle hooks:

```bash
# hooks/pre-install.sh
#!/bin/bash
set -euo pipefail

echo "🔧 Pre-install hook: Validating environment..."

# Check required environment variables
if [[ -z "${PROJECT_NAME:-}" ]]; then
    echo "❌ ERROR: PROJECT_NAME environment variable is required"
    exit 1
fi

# Validate dependencies
if ! command -v docker &> /dev/null; then
    echo "⚠️  WARNING: Docker not found, some features may not work"
fi

echo "✅ Pre-install validation complete"
```

```bash
# hooks/post-install.sh
#!/bin/bash
set -euo pipefail

echo "🎯 Post-install hook: Setting up custom workflow..."

# Create required directories
mkdir -p .ai/workflows/custom

# Set appropriate permissions
chmod 755 .ai/workflows/custom

# Initialize configuration if it doesn't exist
if [[ ! -f .ai/workflows/custom/config.yml ]]; then
    cp components/custom-workflow/files/default-config.yml .ai/workflows/custom/config.yml
fi

echo "✅ Post-install setup complete"
```

```bash
# hooks/validate.sh
#!/bin/bash
set -euo pipefail

echo "🔍 Validation hook: Checking installation..."

errors=0

# Check required files exist
required_files=(
    ".ai/custom-config.yml"
    ".github/workflows/custom.yml"
)

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ ERROR: Required file missing: $file"
        ((errors++))
    else
        echo "✅ Found: $file"
    fi
done

# Validate configuration syntax
if [[ -f ".ai/custom-config.yml" ]]; then
    if ! python -c "import yaml; yaml.safe_load(open('.ai/custom-config.yml'))" 2>/dev/null; then
        echo "❌ ERROR: Invalid YAML syntax in .ai/custom-config.yml"
        ((errors++))
    else
        echo "✅ Configuration syntax valid"
    fi
fi

if [[ $errors -eq 0 ]]; then
    echo "✅ Validation passed"
    exit 0
else
    echo "❌ Validation failed with $errors errors"
    exit 1
fi
```

## Configuration and Variables

### Environment Variables

Plugins can access environment variables in templates:

```yaml
# Template usage
database_url: "{{ env.DATABASE_URL | default('sqlite:///app.db') }}"
debug_mode: "{{ env.DEBUG | default('false') | bool }}"
port: {{ env.PORT | default(8000) | int }}
```

### Configuration Files

Access project configuration in templates:

```yaml
# Access from .ai/config.yml
project_name: "{{ config.project.name | default('unnamed') }}"
features: {{ config.features | default([]) | tojson }}
```

### Plugin Configuration

Define plugin-specific configuration:

```yaml
# plugin-manifest.yaml
configuration:
  default_theme: "dark"
  enable_analytics: false
  supported_languages: ["python", "javascript", "go"]

# Access in templates
theme: "{{ plugin.config.default_theme }}"
analytics: {{ plugin.config.enable_analytics | lower }}
```

## Testing Your Plugin

### Unit Testing

Create tests for your plugin components:

```python
# tests/test_my_plugin.py
import pytest
import yaml
from pathlib import Path
from packages.core.planner import Planner
from packages.adapters.yaml_ops import YAMLOperations

class TestMyPlugin:

    def setup_method(self):
        self.plugin_dir = Path("plugins/my-plugin")
        self.yaml_ops = YAMLOperations()

    def test_plugin_manifest_valid(self):
        """Test that plugin manifest is valid YAML."""
        manifest_path = self.plugin_dir / "plugin-manifest.yaml"
        assert manifest_path.exists()

        with open(manifest_path) as f:
            manifest = yaml.safe_load(f)

        assert "name" in manifest
        assert "version" in manifest
        assert "components" in manifest

    def test_component_manifest_valid(self):
        """Test that component manifests are valid."""
        components_dir = self.plugin_dir / "components"

        for component_dir in components_dir.iterdir():
            if component_dir.is_dir():
                manifest_path = component_dir / "manifest.yaml"
                assert manifest_path.exists()

                with open(manifest_path) as f:
                    manifest = yaml.safe_load(f)

                assert "name" in manifest
                assert "files" in manifest

    def test_template_processing(self):
        """Test template processing with variables."""
        template_content = """
        name: "{{ project.name }}"
        debug: {{ debug | default(false) | lower }}
        """

        variables = {
            "project": {"name": "test-project"},
            "debug": True
        }

        result = self.yaml_ops.render_template(template_content, variables)

        assert "test-project" in result
        assert "debug: true" in result
```

### Integration Testing

Test plugin installation end-to-end:

```python
# tests/test_plugin_integration.py
import tempfile
import subprocess
from pathlib import Path

class TestPluginIntegration:

    def test_plugin_installation(self):
        """Test complete plugin installation workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=test_dir, check=True)

            # Copy plugin to test directory
            plugin_source = Path("plugins/my-plugin")
            plugin_dest = test_dir / "plugins" / "my-plugin"
            shutil.copytree(plugin_source, plugin_dest)

            # Test installation
            result = subprocess.run([
                "ai-guardrails", "install",
                "--plugin", "my-plugin",
                "--component", "my-component",
                "--dry-run"
            ], cwd=test_dir, capture_output=True, text=True)

            assert result.returncode == 0
            assert "my-component" in result.stdout
```

## Best Practices

### 1. Plugin Design

- **Single Responsibility**: Each plugin should have a clear, focused purpose
- **Modular Components**: Break functionality into discrete, reusable components
- **Clear Dependencies**: Explicitly declare all plugin and component dependencies
- **Semantic Versioning**: Use semantic versioning for your plugin releases

### 2. File Organization

- **Logical Grouping**: Group related files in component subdirectories
- **Clear Naming**: Use descriptive names for files and components
- **Documentation**: Include README files and examples
- **Template Separation**: Keep templates in dedicated directories

### 3. Configuration Management

- **Schema Validation**: Define clear schemas for configuration
- **Sensible Defaults**: Provide reasonable default values
- **Environment Flexibility**: Support different environments (dev, staging, prod)
- **Variable Validation**: Validate required variables in templates

### 4. Error Handling

- **Descriptive Errors**: Provide clear, actionable error messages
- **Graceful Degradation**: Handle missing dependencies gracefully
- **Validation Hooks**: Use validation hooks to catch errors early
- **Rollback Support**: Ensure clean rollback on installation failures

### 5. Testing Strategy

- **Unit Tests**: Test individual components and templates
- **Integration Tests**: Test complete installation workflows
- **Validation Tests**: Test configuration schema validation
- **Cross-Platform**: Test on different operating systems

## Publishing Your Plugin

### 1. Documentation

Create comprehensive documentation:

```markdown
# My Plugin

Brief description of what your plugin does.

## Installation

```bash
ai-guardrails install --plugin my-plugin
```

## Components

### my-component

Description of what this component provides.

**Files Created:**
- `.ai/example.yml` - Example configuration
- `.github/workflows/custom.yml` - Custom workflow

**Configuration:**
```yaml
my_plugin:
  enable_feature: true
  custom_setting: "value"
```

## Examples

### Basic Usage

```bash
ai-guardrails install --plugin my-plugin --component my-component
```

### Advanced Configuration

```yaml
# .ai/config.yml
my_plugin:
  advanced_mode: true
  features:
    - name: "feature1"
      enabled: true
```
```

### 2. Version Management

Follow semantic versioning:

```yaml
# plugin-manifest.yaml
metadata:
  version: "1.2.3"  # MAJOR.MINOR.PATCH

# Document changes
changelog:
  "1.2.3":
    - "Fixed template processing bug"
    - "Added new configuration options"
  "1.2.0":
    - "Added advanced-templates component"
    - "Breaking: Renamed configuration keys"
```

### 3. Distribution

Consider these distribution methods:

- **Git Repository**: Host plugin in a dedicated Git repository
- **Plugin Registry**: Submit to official plugin registry (if available)
- **Organization Fork**: Fork the main template repository and add your plugin
- **Package Manager**: Distribute via package managers (npm, pip, etc.)

## Plugin Registry Integration

When the plugin registry becomes available, you can register your plugin:

```bash
# Register plugin with official registry
ai-guardrails plugin register \
  --name my-plugin \
  --version 1.0.0 \
  --repository https://github.com/myorg/my-plugin \
  --description "Custom workflow automation plugin"

# Install from registry
ai-guardrails plugin install my-plugin

# Update plugin
ai-guardrails plugin update my-plugin --version 1.1.0
```

## Troubleshooting

### Common Issues

#### 1. Template Processing Errors

**Problem**: Variables not rendering correctly
**Solution**: Check variable names and default values

```yaml
# Instead of
name: "{{ project_name }}"

# Use with defaults
name: "{{ project.name | default('unnamed') }}"
```

#### 2. File Permission Issues

**Problem**: Files created with wrong permissions
**Solution**: Specify explicit file modes

```yaml
files:
  - source: "script.sh"
    target: "bin/custom-script.sh"
    action: "copy"
    mode: 0755  # Explicitly set executable
```

#### 3. Dependency Resolution Failures

**Problem**: Plugin dependencies not found
**Solution**: Check dependency names and versions

```yaml
dependencies:
  - plugin: "core-files"  # Exact plugin name
    version: ">=1.0.0"    # Valid version constraint
    required: true
```

#### 4. YAML Merge Conflicts

**Problem**: YAML merging produces unexpected results
**Solution**: Choose appropriate merge strategy

```yaml
# For replacing entire sections
merge_strategy: "replace"

# For deep merging objects
merge_strategy: "deep"

# For appending to arrays
merge_strategy: "append"
```

### Debugging Tips

1. **Use Verbose Mode**: `ai-guardrails install --verbose`
2. **Dry Run First**: `ai-guardrails install --dry-run`
3. **Check Logs**: Review `.ai/guardrails/logs/`
4. **Validate Syntax**: Use `ai-guardrails doctor`
5. **Test Incrementally**: Install components one at a time

## Advanced Topics

### Custom Action Types

Extend the system with custom action types:

```python
# plugins/my-plugin/actions/custom_action.py
from packages.domain.models import FileAction
from packages.adapters.file_ops import FileOperations

class CustomAction:
    """Custom action implementation."""

    def __init__(self, file_ops: FileOperations):
        self.file_ops = file_ops

    def execute(self, action: FileAction, context: dict) -> None:
        """Execute custom action logic."""
        # Implement your custom behavior
        pass
```

### Plugin Hooks Integration

Integrate with the core system's hook points:

```python
# plugins/my-plugin/hooks.py
from packages.core.orchestrator import Orchestrator

class MyPluginHooks:
    """Plugin hooks for system integration."""

    @staticmethod
    def pre_plan(context: dict) -> None:
        """Called before planning phase."""
        pass

    @staticmethod
    def post_install(context: dict) -> None:
        """Called after installation phase."""
        pass
```

### Dynamic Configuration

Support dynamic configuration generation:

```python
# plugins/my-plugin/config_generator.py
import yaml
from typing import Dict, Any

class ConfigGenerator:
    """Generate dynamic configuration based on environment."""

    def generate_config(self, environment: str) -> Dict[str, Any]:
        """Generate configuration for specific environment."""
        base_config = {
            "plugin": "my-plugin",
            "version": "1.0.0"
        }

        if environment == "production":
            base_config.update({
                "debug": False,
                "log_level": "INFO"
            })
        else:
            base_config.update({
                "debug": True,
                "log_level": "DEBUG"
            })

        return base_config
```

This comprehensive guide provides everything needed to develop robust, maintainable plugins for the AI Guardrails Bootstrap System. Follow these patterns and best practices to create plugins that integrate seamlessly with the core architecture while providing valuable functionality to users.
