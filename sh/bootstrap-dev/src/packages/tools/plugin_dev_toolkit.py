"""
Plugin Development Toolkit for AI Guardrails Bootstrap

This module provides comprehensive development tools for plugin creators,
including scaffolding, testing, packaging, and publishing utilities.

Features:
- Plugin project scaffolding with templates
- Manifest validation and linting
- Component testing framework
- Plugin packaging utilities
- Development server for testing
- Documentation generation
- Version management
- Publishing helpers
"""

import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import yaml
import logging
from datetime import datetime

from ..domain.plugin_models import PluginManifest, ComponentDefinition
from ..core.plugin_validator import PluginValidator
from ..adapters.enhanced_plugin_installer import (
    EnhancedPluginInstaller,
    PluginInstallationContext,
)
from ..core.config_validator import ConfigValidator


@dataclass
class PluginTemplate:
    """Plugin template definition."""

    name: str
    description: str
    files: Dict[str, str]  # filename -> content
    variables: Dict[str, str] = None  # template variables


@dataclass
class TestResult:
    """Plugin test result."""

    success: bool
    test_name: str
    message: str
    duration: float
    details: Dict[str, Any] = None


class PluginDevToolkit:
    """Development toolkit for plugin creators."""

    def __init__(self, workspace_dir: Path = None):
        self.workspace_dir = workspace_dir or Path.cwd()
        self.validator = PluginValidator()
        self.config_validator = ConfigValidator()
        self.logger = logging.getLogger(__name__)

        # Load templates
        self.templates = self._load_templates()

    def scaffold_plugin(
        self,
        plugin_name: str,
        template_name: str = "basic",
        author: str = None,
        description: str = None,
        license: str = "MIT",
    ) -> bool:
        """
        Create a new plugin from template.

        Args:
            plugin_name: Name of the plugin
            template_name: Template to use
            author: Plugin author
            description: Plugin description
            license: Plugin license

        Returns:
            True if scaffolding successful
        """
        try:
            if template_name not in self.templates:
                self.logger.error(f"Template not found: {template_name}")
                return False

            plugin_dir = self.workspace_dir / plugin_name

            if plugin_dir.exists():
                self.logger.error(f"Plugin directory already exists: {plugin_dir}")
                return False

            template = self.templates[template_name]

            # Create plugin directory
            plugin_dir.mkdir(parents=True)

            # Template variables
            variables = {
                "plugin_name": plugin_name,
                "author": author or os.getenv("USER", "Unknown"),
                "description": description or f"A plugin for {plugin_name}",
                "license": license,
                "year": datetime.now().year,
                "date": datetime.now().strftime("%Y-%m-%d"),
            }

            # Process template files
            for file_path, content_template in template.files.items():
                target_path = plugin_dir / file_path
                target_path.parent.mkdir(parents=True, exist_ok=True)

                # Apply template variables
                content = content_template
                for var, value in variables.items():
                    content = content.replace(f"{{{{ {var} }}}}", str(value))

                with open(target_path, "w") as f:
                    f.write(content)

            self.logger.info(f"Created plugin: {plugin_dir}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to scaffold plugin: {e}")
            return False

    def validate_plugin(self, plugin_dir: Path) -> List[str]:
        """
        Validate plugin structure and manifest.

        Args:
            plugin_dir: Plugin directory path

        Returns:
            List of validation errors
        """
        errors = []

        try:
            # Check basic structure
            manifest_path = plugin_dir / "plugin-manifest.yaml"
            if not manifest_path.exists():
                errors.append("Missing plugin-manifest.yaml")
                return errors

            # Load and validate manifest
            with open(manifest_path) as f:
                manifest_data = yaml.safe_load(f)

            manifest = PluginManifest.from_dict(manifest_data)
            manifest_errors = self.validator.validate_plugin_manifest(manifest)
            errors.extend(manifest_errors)

            # Check component files
            for component_name, component in manifest.components.items():
                component_errors = self._validate_component_files(plugin_dir, component)
                errors.extend(component_errors)

            # Check for required files
            required_files = ["README.md"]
            for required_file in required_files:
                if not (plugin_dir / required_file).exists():
                    errors.append(f"Missing required file: {required_file}")

            return errors

        except Exception as e:
            errors.append(f"Validation failed: {e}")
            return errors

    def test_plugin(
        self, plugin_dir: Path, target_dir: Path = None
    ) -> List[TestResult]:
        """
        Test plugin installation and functionality.

        Args:
            plugin_dir: Plugin directory path
            target_dir: Test target directory (temporary if None)

        Returns:
            List of test results
        """
        results = []

        try:
            # Use temporary directory if none provided
            if target_dir is None:
                temp_dir = Path(tempfile.mkdtemp())
                target_dir = temp_dir
                cleanup_temp = True
            else:
                cleanup_temp = False

            try:
                # Test 1: Manifest validation
                start_time = datetime.now()
                validation_errors = self.validate_plugin(plugin_dir)
                duration = (datetime.now() - start_time).total_seconds()

                results.append(
                    TestResult(
                        success=len(validation_errors) == 0,
                        test_name="manifest_validation",
                        message=f"Found {len(validation_errors)} validation errors"
                        if validation_errors
                        else "Manifest is valid",
                        duration=duration,
                        details={"errors": validation_errors},
                    )
                )

                # Test 2: Installation test
                if len(validation_errors) == 0:
                    start_time = datetime.now()
                    install_success = self._test_installation(plugin_dir, target_dir)
                    duration = (datetime.now() - start_time).total_seconds()

                    results.append(
                        TestResult(
                            success=install_success,
                            test_name="installation",
                            message="Installation successful"
                            if install_success
                            else "Installation failed",
                            duration=duration,
                        )
                    )

                # Test 3: Component validation
                start_time = datetime.now()
                component_success = self._test_components(plugin_dir)
                duration = (datetime.now() - start_time).total_seconds()

                results.append(
                    TestResult(
                        success=component_success,
                        test_name="component_validation",
                        message="Components valid"
                        if component_success
                        else "Component validation failed",
                        duration=duration,
                    )
                )

            finally:
                if cleanup_temp:
                    shutil.rmtree(temp_dir, ignore_errors=True)

            return results

        except Exception as e:
            results.append(
                TestResult(
                    success=False,
                    test_name="test_execution",
                    message=f"Test execution failed: {e}",
                    duration=0.0,
                )
            )
            return results

    def package_plugin(
        self, plugin_dir: Path, output_path: Path = None
    ) -> Optional[Path]:
        """
        Package plugin for distribution.

        Args:
            plugin_dir: Plugin directory path
            output_path: Output package path (auto-generated if None)

        Returns:
            Path to created package or None if failed
        """
        try:
            # Validate plugin first
            validation_errors = self.validate_plugin(plugin_dir)
            if validation_errors:
                self.logger.error(f"Cannot package invalid plugin: {validation_errors}")
                return None

            # Load manifest for version info
            manifest_path = plugin_dir / "plugin-manifest.yaml"
            with open(manifest_path) as f:
                manifest_data = yaml.safe_load(f)

            plugin_name = manifest_data.get("name", plugin_dir.name)
            plugin_version = manifest_data.get("version", "0.1.0")

            # Generate output path if not provided
            if output_path is None:
                output_path = self.workspace_dir / f"{plugin_name}-{plugin_version}.zip"

            # Create package
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in plugin_dir.rglob("*"):
                    if file_path.is_file():
                        # Skip hidden files and directories
                        if any(part.startswith(".") for part in file_path.parts):
                            continue

                        arcname = file_path.relative_to(plugin_dir)
                        zipf.write(file_path, arcname)

            self.logger.info(f"Packaged plugin: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"Failed to package plugin: {e}")
            return None

    def generate_docs(self, plugin_dir: Path) -> bool:
        """
        Generate documentation for plugin.

        Args:
            plugin_dir: Plugin directory path

        Returns:
            True if documentation generated successfully
        """
        try:
            # Load manifest
            manifest_path = plugin_dir / "plugin-manifest.yaml"
            with open(manifest_path) as f:
                manifest_data = yaml.safe_load(f)

            manifest = PluginManifest.from_dict(manifest_data)

            # Generate documentation
            docs_dir = plugin_dir / "docs"
            docs_dir.mkdir(exist_ok=True)

            # Generate API documentation
            api_doc = self._generate_api_docs(manifest)
            with open(docs_dir / "API.md", "w") as f:
                f.write(api_doc)

            # Generate component documentation
            components_doc = self._generate_components_docs(manifest)
            with open(docs_dir / "COMPONENTS.md", "w") as f:
                f.write(components_doc)

            # Generate configuration documentation
            config_doc = self._generate_config_docs(manifest)
            with open(docs_dir / "CONFIGURATION.md", "w") as f:
                f.write(config_doc)

            self.logger.info("Generated plugin documentation")
            return True

        except Exception as e:
            self.logger.error(f"Failed to generate documentation: {e}")
            return False

    def lint_plugin(self, plugin_dir: Path) -> List[str]:
        """
        Lint plugin for best practices and common issues.

        Args:
            plugin_dir: Plugin directory path

        Returns:
            List of lint warnings/errors
        """
        issues = []

        try:
            # Check basic validation first
            validation_errors = self.validate_plugin(plugin_dir)
            issues.extend(validation_errors)

            # Load manifest for additional checks
            manifest_path = plugin_dir / "plugin-manifest.yaml"
            if manifest_path.exists():
                with open(manifest_path) as f:
                    manifest_data = yaml.safe_load(f)

                # Check best practices
                issues.extend(self._check_best_practices(plugin_dir, manifest_data))

                # Check security issues
                issues.extend(self._check_security_issues(plugin_dir, manifest_data))

                # Check performance issues
                issues.extend(self._check_performance_issues(plugin_dir, manifest_data))

            return issues

        except Exception as e:
            issues.append(f"Linting failed: {e}")
            return issues

    def _load_templates(self) -> Dict[str, PluginTemplate]:
        """Load plugin templates."""
        return {
            "basic": PluginTemplate(
                name="basic",
                description="Basic plugin template",
                files={
                    "plugin-manifest.yaml": """name: {{ plugin_name }}
version: 0.1.0
description: {{ description }}
author: {{ author }}
license: {{ license }}
api_version: v1

components:
  {{ plugin_name }}-component:
    description: Main component for {{ plugin_name }}
    files: []

profiles:
  default:
    description: Default {{ plugin_name }} installation
    components:
      - {{ plugin_name }}-component

configuration:
  enabled: true
""",
                    "README.md": """# {{ plugin_name }} Plugin

{{ description }}

## Installation

```bash
ai-guardrails plugin install {{ plugin_name }}
```

## Usage

Describe how to use your plugin here.

## Configuration

Describe any configuration options here.

## Components

- `{{ plugin_name }}-component`: Main component for {{ plugin_name }}

## License

{{ license }}

## Author

{{ author }}
""",
                    "docs/DEVELOPMENT.md": """# Development Guide for {{ plugin_name }}

## Development Setup

1. Clone the plugin repository
2. Make your changes
3. Test the plugin: `ai-guardrails plugin test`
4. Validate: `ai-guardrails plugin validate plugin-manifest.yaml`

## Testing

Run tests with:
```bash
ai-guardrails plugin test {{ plugin_name }}
```

## Contributing

Describe contribution guidelines here.
""",
                    "components/{{ plugin_name }}-component/files/.gitkeep": "",
                },
            ),
            "advanced": PluginTemplate(
                name="advanced",
                description="Advanced plugin template with hooks and templates",
                files={
                    "plugin-manifest.yaml": """name: {{ plugin_name }}
version: 0.1.0
description: {{ description }}
author: {{ author }}
license: {{ license }}
api_version: v1

environment:
  detects: []
  requires: []
  platforms: ["linux", "macos", "windows"]

components:
  {{ plugin_name }}-core:
    description: Core component for {{ plugin_name }}
    files:
      - action: copy
        source: "components/{{ plugin_name }}-core/files/**"
        target: ".{{ plugin_name }}/"
    hooks:
      pre_install: "hooks/pre-install.sh"
      post_install: "hooks/post-install.sh"
      validate: "hooks/validate.sh"

  {{ plugin_name }}-config:
    description: Configuration component
    files:
      - action: template
        source: "templates/config.yaml.j2"
        target: ".{{ plugin_name }}/config.yaml"
    dependencies:
      - {{ plugin_name }}-core

profiles:
  minimal:
    description: Minimal {{ plugin_name }} installation
    components:
      - {{ plugin_name }}-core

  full:
    description: Full {{ plugin_name }} installation
    components:
      - {{ plugin_name }}-core
      - {{ plugin_name }}-config

configuration:
  enabled: true
  debug: false
""",
                    "README.md": """# {{ plugin_name }} Plugin

{{ description }}

## Installation

```bash
# Minimal installation
ai-guardrails plugin install {{ plugin_name }} --profile minimal

# Full installation
ai-guardrails plugin install {{ plugin_name }} --profile full
```

## Profiles

- `minimal`: Core functionality only
- `full`: Complete feature set with configuration

## Configuration

The plugin supports the following configuration options:

```yaml
{{ plugin_name }}:
  enabled: true
  debug: false
```

## Components

- `{{ plugin_name }}-core`: Core functionality
- `{{ plugin_name }}-config`: Configuration management

## License

{{ license }}
""",
                    "hooks/pre-install.sh": """#!/bin/bash
# Pre-installation hook for {{ plugin_name }}

echo "Preparing to install {{ plugin_name }}..."

# Add any pre-installation checks here
exit 0
""",
                    "hooks/post-install.sh": """#!/bin/bash
# Post-installation hook for {{ plugin_name }}

echo "{{ plugin_name }} installation completed!"

# Add any post-installation setup here
exit 0
""",
                    "hooks/validate.sh": """#!/bin/bash
# Validation hook for {{ plugin_name }}

echo "Validating {{ plugin_name }} installation..."

# Add validation checks here
exit 0
""",
                    "templates/config.yaml.j2": """# {{ plugin_name }} Configuration
# Generated on {{ date }}

{{ plugin_name }}:
  enabled: {{ enabled | default(true) }}
  debug: {{ debug | default(false) }}

  # Add your configuration options here
""",
                    "components/{{ plugin_name }}-core/files/.gitkeep": "",
                },
            ),
        }

    def _validate_component_files(
        self, plugin_dir: Path, component: ComponentDefinition
    ) -> List[str]:
        """Validate component file references."""
        errors = []

        for file_op in component.files:
            source_path = plugin_dir / file_op.source
            if not source_path.exists():
                errors.append(
                    f"Component {component.name}: source file not found: {file_op.source}"
                )

        return errors

    def _test_installation(self, plugin_dir: Path, target_dir: Path) -> bool:
        """Test plugin installation."""
        try:
            # Load manifest
            manifest_path = plugin_dir / "plugin-manifest.yaml"
            with open(manifest_path) as f:
                manifest_data = yaml.safe_load(f)

            manifest = PluginManifest.from_dict(manifest_data)

            # Create installer
            installer = EnhancedPluginInstaller(plugin_dir, target_dir)

            # Create installation context
            context = PluginInstallationContext(
                plugin_path=plugin_dir,
                target_path=target_dir,
                manifest=manifest,
                configuration={},
                dry_run=True,  # Dry run for testing
                force=False,
            )

            # Test installation
            result = installer.install_plugin(context)
            return result.success

        except Exception as e:
            self.logger.error(f"Installation test failed: {e}")
            return False

    def _test_components(self, plugin_dir: Path) -> bool:
        """Test component definitions."""
        try:
            # Load manifest
            manifest_path = plugin_dir / "plugin-manifest.yaml"
            with open(manifest_path) as f:
                manifest_data = yaml.safe_load(f)

            manifest = PluginManifest.from_dict(manifest_data)

            # Validate each component
            for component_name, component in manifest.components.items():
                # Check component files exist
                errors = self._validate_component_files(plugin_dir, component)
                if errors:
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Component test failed: {e}")
            return False

    def _generate_api_docs(self, manifest: PluginManifest) -> str:
        """Generate API documentation."""
        doc = f"# {manifest.name} API Documentation\n\n"
        doc += f"**Version:** {manifest.version}\n"
        doc += f"**Author:** {manifest.author}\n\n"
        doc += f"## Description\n\n{manifest.description}\n\n"

        if manifest.components:
            doc += "## Components\n\n"
            for name, component in manifest.components.items():
                doc += f"### {name}\n\n"
                doc += f"{component.description}\n\n"

                if component.dependencies:
                    doc += f"**Dependencies:** {', '.join(component.dependencies)}\n\n"

        return doc

    def _generate_components_docs(self, manifest: PluginManifest) -> str:
        """Generate component documentation."""
        doc = f"# {manifest.name} Components\n\n"

        for name, component in manifest.components.items():
            doc += f"## {name}\n\n"
            doc += f"{component.description}\n\n"

            if component.files:
                doc += "### Files\n\n"
                for file_op in component.files:
                    doc += f"- **{file_op.action}**: `{file_op.source}` → `{file_op.target}`\n"
                doc += "\n"

            if component.dependencies:
                doc += "### Dependencies\n\n"
                for dep in component.dependencies:
                    doc += f"- {dep}\n"
                doc += "\n"

        return doc

    def _generate_config_docs(self, manifest: PluginManifest) -> str:
        """Generate configuration documentation."""
        doc = f"# {manifest.name} Configuration\n\n"

        if manifest.configuration:
            doc += "## Plugin Configuration\n\n"
            doc += "```yaml\n"
            doc += yaml.dump(manifest.configuration, default_flow_style=False)
            doc += "```\n\n"

        return doc

    def _check_best_practices(self, plugin_dir: Path, manifest_data: Dict) -> List[str]:
        """Check for best practice violations."""
        issues = []

        # Check for version format
        version = manifest_data.get("version", "")
        if (
            not version
            or not version.replace(".", "")
            .replace("-", "")
            .replace("+", "")
            .replace("alpha", "")
            .replace("beta", "")
            .replace("rc", "")
            .isalnum()
        ):
            issues.append("Version should follow semantic versioning (e.g., 1.0.0)")

        # Check for description length
        description = manifest_data.get("description", "")
        if len(description) < 10:
            issues.append("Description should be at least 10 characters long")

        # Check for author
        if not manifest_data.get("author"):
            issues.append("Author field is recommended")

        # Check for license
        if not manifest_data.get("license"):
            issues.append("License field is recommended")

        return issues

    def _check_security_issues(
        self, plugin_dir: Path, manifest_data: Dict
    ) -> List[str]:
        """Check for security issues."""
        issues = []

        # Check for executable files
        for file_path in plugin_dir.rglob("*"):
            if file_path.is_file() and os.access(file_path, os.X_OK):
                if file_path.suffix not in [".sh", ".py"]:
                    issues.append(
                        f"Unexpected executable file: {file_path.relative_to(plugin_dir)}"
                    )

        return issues

    def _check_performance_issues(
        self, plugin_dir: Path, manifest_data: Dict
    ) -> List[str]:
        """Check for performance issues."""
        issues = []

        # Check for large files
        for file_path in plugin_dir.rglob("*"):
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                if size_mb > 10:  # 10MB threshold
                    issues.append(
                        f"Large file detected: {file_path.relative_to(plugin_dir)} ({size_mb:.1f}MB)"
                    )

        return issues


class PluginDevToolkitError(Exception):
    """Exception raised during plugin development operations."""

    pass
