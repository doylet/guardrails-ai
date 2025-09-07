# Canonical Plugin Development Guide: AI Guardrails Bootstrap System

**Version:** 2.0.0  
**Date:** 2025-01-07  
**Scope:** Complete plugin development lifecycle following `.ai/` path consolidation

---

## Executive Summary

This guide provides the definitive approach to creating plugins for the AI Guardrails Bootstrap System. Following the recent path consolidation to `.ai/` directories, all plugins must adhere to the updated conventions and structure outlined below.

---

## Table of Contents

1. [Plugin Architecture Principles](#plugin-architecture-principles)
2. [Directory Structure Standards](#directory-structure-standards)
3. [Naming Conventions](#naming-conventions)
4. [Plugin Manifest Specification](#plugin-manifest-specification)
5. [Component Development](#component-development)
6. [Installation Integration](#installation-integration)
7. [Testing & Validation](#testing--validation)
8. [Best Practices & Patterns](#best-practices--patterns)
9. [Complete Example](#complete-example)

---

## Plugin Architecture Principles

### Core Design Philosophy

The AI Guardrails plugin system follows these foundational principles:

1. **Convention Over Configuration** - Standardized file locations and naming reduce cognitive overhead
2. **Declarative Over Imperative** - Manifests describe "what" not "how"
3. **Composable Components** - Small, focused components that work together
4. **Path Consistency** - All AI-related files consolidated under `.ai/` directory
5. **Backwards Compatibility** - Plugins work across system versions

### Architectural Patterns

```yaml
# Pattern: Component-Based Architecture
plugin:
  name: "plugin-name"
  components:
    component-name:
      description: "Single responsibility component"
      file_patterns: ["specific file patterns"]
```

```yaml
# Pattern: Environment Detection
plugin:
  environment:
    detects: ["python", "node", "rust"]  # What this plugin can detect
    requires: ["git", "pre-commit"]      # What this plugin needs
```

```yaml
# Pattern: Profile-Based Installation
profiles:
  minimal: ["core-component"]
  standard: ["core-component", "enhanced-component"]
  full: ["core-component", "enhanced-component", "advanced-component"]
```

---

## Directory Structure Standards

### Plugin Repository Structure

```
src/plugins/your-plugin-name/           # Plugin root directory
├── plugin-manifest.yaml               # Required: Plugin definition
├── README.md                          # Required: Plugin documentation
├── CHANGELOG.md                       # Recommended: Version history
├── .ai/                               # AI-related files for installation
│   ├── scripts/                       # Automation scripts
│   │   ├── your-script.py            # Python scripts
│   │   ├── your-script.sh            # Shell scripts
│   │   └── your-script.js            # Node.js scripts
│   ├── schemas/                       # JSON schemas
│   │   ├── your-config.schema.json   # Configuration validation
│   │   └── your-data.schema.json     # Data validation
│   ├── guardrails/                    # Configuration files
│   │   ├── your-config.yaml          # Plugin-specific config
│   │   └── rules/                    # Rule definitions
│   └── workflows/                     # AI workflow definitions
├── .github/                           # GitHub-specific files
│   ├── workflows/                     # CI/CD workflows
│   │   └── your-plugin-ci.yaml       # Plugin testing workflow
│   ├── instructions/                  # AI instructions
│   └── chatmodes/                    # Copilot chat modes
├── docs/                              # Plugin documentation
│   ├── installation.md               # Installation guide
│   ├── usage.md                      # Usage examples
│   └── api.md                        # API documentation
├── tests/                             # Plugin tests
│   ├── test_your_plugin.py          # Unit tests
│   └── integration/                  # Integration tests
└── examples/                          # Usage examples
    └── basic-usage/                  # Example configurations
```

### Target Installation Structure

After installation, your plugin files will be placed in the target project:

```
target-project/
├── .ai/                               # Consolidated AI directory
│   ├── scripts/                       # All automation scripts
│   │   ├── check_envelope.py         # Core scripts
│   │   └── your-script.py            # Your plugin scripts
│   ├── schemas/                       # All JSON schemas
│   │   ├── copilot_envelope.schema.json  # Core schemas
│   │   └── your-config.schema.json   # Your plugin schemas
│   ├── guardrails/                    # Configuration files
│   │   ├── root-allowlist.txt        # Core config
│   │   └── your-config.yaml          # Your plugin config
│   └── workflows/                     # AI workflows
├── .github/                           # GitHub integration
└── docs/                              # Documentation
```

---

## Naming Conventions

### Plugin Names

**Format:** `<category>-<purpose>-kit`

**Categories:**
- `commit-msg-kit` - Git commit message handling
- `demos-on-rails-kit` - Demo validation and testing
- `root-hygiene-kit` - Repository cleanliness
- `doc-guardrails-kit` - Documentation standards
- `security-scan-kit` - Security scanning
- `performance-monitor-kit` - Performance monitoring

**Rules:**
- Use lowercase with hyphens
- End with `-kit` suffix
- Be descriptive but concise
- Avoid vendor-specific names

### Component Names

**Format:** `<functionality>-<type>`

**Examples:**
- `commit-msg` - Core commit message functionality
- `vscode-commit` - VS Code integration
- `demo-harness` - Demo execution framework
- `validation-scripts` - Validation automation
- `github-workflows` - GitHub Actions

### File Names

**Scripts:**
- Python: `snake_case.py` (e.g., `check_envelope.py`)
- Shell: `kebab-case.sh` (e.g., `lang-lint.sh`)
- Node.js: `kebab-case.js` (e.g., `package-audit.js`)

**Configuration:**
- YAML: `kebab-case.yaml` (e.g., `plugin-config.yaml`)
- JSON: `kebab-case.json` (e.g., `schema-config.json`)

**Documentation:**
- Markdown: `UPPERCASE.md` for main docs, `lowercase.md` for specific guides
- Examples: `README.md`, `CHANGELOG.md`, `installation.md`

---

## Plugin Manifest Specification

### Complete Manifest Template

```yaml
# plugin-manifest.yaml
---
# Plugin identification
plugin:
  name: "your-plugin-kit"
  version: "1.0.0"
  description: "Brief description of plugin purpose"
  author: "Your Name or Organization"
  license: "MIT"
  homepage: "https://github.com/your-org/your-plugin"
  repository: "https://github.com/your-org/your-plugin.git"
  
  # Plugin dependencies
  dependencies:
    - "core"                           # Core AI Guardrails
    - "other-plugin-kit"              # Other plugins if needed
  
  # Environment requirements
  environment:
    detects: ["python", "git"]        # What this plugin can detect
    requires: ["python3", "git"]      # Required tools
    platforms: ["linux", "macos", "windows"]  # Supported platforms
    min_version: "1.0.0"              # Minimum AI Guardrails version

# Component definitions
components:
  # Primary component
  core-functionality:
    description: "Core plugin functionality"
    file_patterns:
      - ".ai/scripts/your-main-script.py"
      - ".ai/guardrails/your-config.yaml"
    post_install:
      - "chmod +x .ai/scripts/your-main-script.py"
    
  # Enhanced component
  advanced-features:
    description: "Advanced plugin features"
    file_patterns:
      - ".ai/scripts/advanced-script.py"
      - ".ai/schemas/advanced-config.schema.json"
    dependencies: ["core-functionality"]
    
  # Integration component
  github-integration:
    description: "GitHub-specific integration"
    file_patterns:
      - ".github/workflows/your-plugin-ci.yaml"
      - ".github/instructions/your-plugin.md"
    optional: true

# Installation profiles
profiles:
  minimal:
    description: "Basic plugin functionality"
    components: ["core-functionality"]
    
  standard:
    description: "Recommended plugin setup"
    components: ["core-functionality", "advanced-features"]
    
  full:
    description: "Complete plugin with all features"
    components: ["core-functionality", "advanced-features", "github-integration"]

# Plugin configuration schema
config:
  schema_file: ".ai/schemas/your-plugin-config.schema.json"
  default_values:
    enabled: true
    check_level: "standard"
    exclude_patterns: []

# Lifecycle hooks
hooks:
  pre_install:
    - "echo 'Installing your-plugin-kit...'"
  post_install:
    - ".ai/scripts/your-setup-script.py"
  pre_uninstall:
    - ".ai/scripts/your-cleanup-script.py"
  validate:
    - ".ai/scripts/your-validation-script.py"

# Plugin metadata
metadata:
  tags: ["automation", "validation", "ci-cd"]
  category: "development-tools"
  maturity: "stable"  # alpha, beta, stable, deprecated
  support_level: "community"  # core, supported, community
```

### Required Fields

**Minimum viable manifest:**

```yaml
plugin:
  name: "your-plugin-kit"
  version: "1.0.0"
  description: "Plugin description"
  author: "Your Name"

components:
  main:
    description: "Main component"
    file_patterns:
      - ".ai/scripts/your-script.py"

profiles:
  minimal:
    components: ["main"]
```

---

## Component Development

### Script Development

**Python Scripts** (`.ai/scripts/your_script.py`):

```python
#!/usr/bin/env python3
"""
Your Plugin Script
Part of the AI Guardrails Bootstrap System
"""

import sys
import json
import os
from pathlib import Path

# Standard imports for AI Guardrails compatibility
try:
    import jsonschema
    import yaml
except ImportError:
    print("Error: Required dependencies not found", file=sys.stderr)
    sys.exit(1)

def load_config():
    """Load plugin configuration from .ai/guardrails/"""
    config_path = Path(".ai/guardrails/your-config.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}

def validate_with_schema(data, schema_name):
    """Validate data against schema in .ai/schemas/"""
    schema_path = Path(f".ai/schemas/{schema_name}")
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    jsonschema.validate(data, schema)

def main():
    """Main plugin logic"""
    config = load_config()
    
    # Your plugin logic here
    print("Your plugin is running...")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

**Shell Scripts** (`.ai/scripts/your-script.sh`):

```bash
#!/bin/bash
# Your Plugin Script
# Part of the AI Guardrails Bootstrap System

set -euo pipefail

# Constants
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly AI_DIR="$(dirname "$SCRIPT_DIR")"
readonly CONFIG_FILE="$AI_DIR/guardrails/your-config.yaml"

# Utility functions
log_info() {
    echo "ℹ️  $*" >&2
}

log_error() {
    echo "❌ $*" >&2
}

log_success() {
    echo "✅ $*" >&2
}

# Load configuration
load_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        # Parse YAML config (requires yq or python)
        python3 -c "import yaml; import sys; print(yaml.safe_load(open('$CONFIG_FILE')))"
    else
        echo "{}"
    fi
}

# Main function
main() {
    log_info "Starting your-plugin..."
    
    # Your plugin logic here
    
    log_success "Your plugin completed successfully"
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### Configuration Schema

**Schema Definition** (`.ai/schemas/your-config.schema.json`):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ai-guardrails.dev/schemas/your-plugin-config.schema.json",
  "title": "Your Plugin Configuration",
  "description": "Configuration schema for your-plugin-kit",
  "type": "object",
  "properties": {
    "enabled": {
      "type": "boolean",
      "default": true,
      "description": "Enable or disable the plugin"
    },
    "check_level": {
      "type": "string",
      "enum": ["minimal", "standard", "strict"],
      "default": "standard",
      "description": "Validation strictness level"
    },
    "exclude_patterns": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "default": [],
      "description": "File patterns to exclude from processing"
    },
    "custom_rules": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "enabled": {"type": "boolean"},
          "severity": {"type": "string", "enum": ["error", "warning", "info"]}
        }
      }
    }
  },
  "required": ["enabled"],
  "additionalProperties": false
}
```

### Configuration File

**Default Configuration** (`.ai/guardrails/your-config.yaml`):

```yaml
# Your Plugin Configuration
# Generated by AI Guardrails Bootstrap System

enabled: true
check_level: "standard"
exclude_patterns:
  - "vendor/**"
  - "node_modules/**"
  - ".git/**"

custom_rules:
  rule_001:
    enabled: true
    severity: "error"
    description: "Custom validation rule"
  
  rule_002:
    enabled: false
    severity: "warning"
    description: "Optional validation rule"

# Plugin-specific settings
settings:
  timeout: 30
  max_file_size: "10MB"
  parallel_processing: true
```

---

## Installation Integration

### Bootstrap Integration

Your plugin integrates with the bootstrap system through the installation manifest:

```yaml
# The bootstrap system automatically processes your plugin-manifest.yaml
# No additional integration code needed

# Your files are installed according to file_patterns:
components:
  your-component:
    file_patterns:
      - ".ai/scripts/your-script.py"    # -> target/.ai/scripts/your-script.py
      - ".ai/schemas/your-schema.json"  # -> target/.ai/schemas/your-schema.json
```

### Pre-commit Integration

**Hook Configuration** (`.pre-commit-config.yaml`):

```yaml
repos:
  - repo: local
    hooks:
      - id: your-plugin-check
        name: Your Plugin Validation
        entry: python .ai/scripts/your-script.py
        language: system
        pass_filenames: false
        stages: [pre-commit]
        
      - id: your-plugin-lint
        name: Your Plugin Linting
        entry: .ai/scripts/your-lint.sh
        language: system
        files: \\.py$
        stages: [pre-commit]
```

### GitHub Actions Integration

**Workflow Template** (`.github/workflows/your-plugin.yaml`):

```yaml
name: Your Plugin CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  your-plugin-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install jsonschema pyyaml
          
      - name: Run Your Plugin
        run: python .ai/scripts/your-script.py
        
      - name: Validate Configuration
        run: |
          python -c "
          import json, jsonschema, yaml
          with open('.ai/schemas/your-config.schema.json') as f:
              schema = json.load(f)
          with open('.ai/guardrails/your-config.yaml') as f:
              config = yaml.safe_load(f)
          jsonschema.validate(config, schema)
          print('✅ Configuration validation passed')
          "
```

---

## Testing & Validation

### Unit Testing

**Test Structure** (`tests/test_your_plugin.py`):

```python
#!/usr/bin/env python3
"""
Unit tests for your-plugin-kit
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add the plugin scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / ".ai" / "scripts"))

try:
    import your_script
except ImportError:
    # Handle case where plugin isn't installed
    your_script = None

class TestYourPlugin(unittest.TestCase):
    """Test cases for your plugin"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create minimal .ai structure
        os.makedirs(".ai/guardrails", exist_ok=True)
        os.makedirs(".ai/schemas", exist_ok=True)
        
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    @unittest.skipIf(your_script is None, "Plugin not installed")
    def test_load_config(self):
        """Test configuration loading"""
        # Create test config
        config_content = """
enabled: true
check_level: "standard"
"""
        with open(".ai/guardrails/your-config.yaml", "w") as f:
            f.write(config_content)
        
        config = your_script.load_config()
        self.assertTrue(config["enabled"])
        self.assertEqual(config["check_level"], "standard")
    
    def test_plugin_structure(self):
        """Test plugin directory structure"""
        plugin_dir = Path(__file__).parent.parent
        
        # Check required files
        self.assertTrue((plugin_dir / "plugin-manifest.yaml").exists())
        self.assertTrue((plugin_dir / "README.md").exists())
        
        # Check .ai structure
        ai_dir = plugin_dir / ".ai"
        self.assertTrue(ai_dir.exists())
        self.assertTrue((ai_dir / "scripts").exists())

if __name__ == "__main__":
    unittest.main()
```

### Integration Testing

**Integration Test** (`tests/integration/test_installation.py`):

```python
#!/usr/bin/env python3
"""
Integration tests for plugin installation
"""

import unittest
import tempfile
import subprocess
import shutil
from pathlib import Path

class TestPluginInstallation(unittest.TestCase):
    """Test plugin installation process"""
    
    def setUp(self):
        """Set up test project"""
        self.test_dir = tempfile.mkdtemp()
        self.plugin_dir = Path(__file__).parent.parent.parent
        
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
    
    def test_bootstrap_installation(self):
        """Test plugin installation via bootstrap"""
        # Initialize test project
        subprocess.run(["git", "init"], cwd=self.test_dir, check=True)
        
        # Run bootstrap with plugin
        bootstrap_script = self.plugin_dir.parent.parent / "src" / "ai_guardrails_bootstrap_modular.sh"
        result = subprocess.run([
            "bash", str(bootstrap_script),
            "--apply",
            f"--plugin={self.plugin_dir}",
            "--template-repo=file://" + str(self.plugin_dir.parent.parent / "src" / "ai-guardrails-templates")
        ], cwd=self.test_dir, capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0, f"Bootstrap failed: {result.stderr}")
        
        # Verify files were installed
        target_files = [
            ".ai/scripts/your-script.py",
            ".ai/guardrails/your-config.yaml",
            ".ai/schemas/your-config.schema.json"
        ]
        
        for file_path in target_files:
            full_path = Path(self.test_dir) / file_path
            self.assertTrue(full_path.exists(), f"Missing file: {file_path}")

if __name__ == "__main__":
    unittest.main()
```

---

## Best Practices & Patterns

### Code Quality Standards

1. **Error Handling**
   ```python
   try:
       result = risky_operation()
   except SpecificException as e:
       log_error(f"Operation failed: {e}")
       return 1
   ```

2. **Configuration Validation**
   ```python
   def validate_config(config):
       """Validate configuration against schema"""
       schema_path = Path(".ai/schemas/your-config.schema.json")
       with open(schema_path) as f:
           schema = json.load(f)
       jsonschema.validate(config, schema)
   ```

3. **Path Handling**
   ```python
   # Always use Path objects for file operations
   ai_dir = Path(".ai")
   config_file = ai_dir / "guardrails" / "your-config.yaml"
   ```

### Performance Considerations

1. **Lazy Loading**: Load heavy dependencies only when needed
2. **Caching**: Cache expensive operations in `/tmp` or user cache directories
3. **Parallel Processing**: Use threading/multiprocessing for I/O bound operations
4. **Resource Limits**: Respect system resources (memory, CPU, disk)

### Security Guidelines

1. **Input Validation**: Validate all external inputs
2. **Path Traversal**: Prevent directory traversal attacks
3. **Command Injection**: Sanitize shell command arguments
4. **Dependency Management**: Pin dependency versions

### Documentation Standards

1. **README.md**: Clear installation and usage instructions
2. **Inline Comments**: Explain complex logic
3. **Type Hints**: Use type annotations in Python
4. **API Documentation**: Document public functions/classes

---

## Complete Example

Here's a complete example plugin that follows all conventions:

### Plugin Structure

```
src/plugins/quality-check-kit/
├── plugin-manifest.yaml
├── README.md
├── CHANGELOG.md
├── .ai/
│   ├── scripts/
│   │   ├── quality_check.py
│   │   └── fix_quality_issues.sh
│   ├── schemas/
│   │   └── quality-config.schema.json
│   └── guardrails/
│       └── quality-config.yaml
├── .github/
│   └── workflows/
│       └── quality-check.yaml
├── tests/
│   ├── test_quality_check.py
│   └── integration/
│       └── test_installation.py
└── docs/
    ├── installation.md
    └── usage.md
```

### Plugin Manifest

```yaml
# plugin-manifest.yaml
plugin:
  name: "quality-check-kit"
  version: "1.0.0"
  description: "Code quality checking and automatic fixing"
  author: "AI Guardrails Team"
  license: "MIT"
  
  dependencies:
    - "core"
  
  environment:
    detects: ["python", "javascript", "typescript"]
    requires: ["git"]
    platforms: ["linux", "macos", "windows"]

components:
  quality-scripts:
    description: "Quality checking scripts"
    file_patterns:
      - ".ai/scripts/quality_check.py"
      - ".ai/scripts/fix_quality_issues.sh"
    post_install:
      - "chmod +x .ai/scripts/quality_check.py"
      - "chmod +x .ai/scripts/fix_quality_issues.sh"
  
  quality-config:
    description: "Quality configuration and schemas"
    file_patterns:
      - ".ai/guardrails/quality-config.yaml"
      - ".ai/schemas/quality-config.schema.json"
  
  github-integration:
    description: "GitHub Actions workflow"
    file_patterns:
      - ".github/workflows/quality-check.yaml"
    optional: true

profiles:
  minimal:
    components: ["quality-scripts", "quality-config"]
  
  full:
    components: ["quality-scripts", "quality-config", "github-integration"]

config:
  schema_file: ".ai/schemas/quality-config.schema.json"
  default_values:
    enabled: true
    auto_fix: false
    check_types: ["syntax", "style", "security"]

hooks:
  post_install:
    - "echo 'Quality Check Kit installed successfully'"
  validate:
    - "python .ai/scripts/quality_check.py --validate-config"
```

### Main Script

```python
#!/usr/bin/env python3
"""
Quality Check Script
Part of the AI Guardrails Bootstrap System - Quality Check Kit
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import argparse

try:
    import yaml
    import jsonschema
except ImportError:
    print("Error: Required dependencies not found. Install with: pip install pyyaml jsonschema", file=sys.stderr)
    sys.exit(1)

class QualityChecker:
    """Main quality checking class"""
    
    def __init__(self):
        self.ai_dir = Path(".ai")
        self.config_file = self.ai_dir / "guardrails" / "quality-config.yaml"
        self.schema_file = self.ai_dir / "schemas" / "quality-config.schema.json"
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load and validate configuration"""
        if not self.config_file.exists():
            return {"enabled": True, "auto_fix": False, "check_types": ["syntax"]}
        
        with open(self.config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate against schema
        if self.schema_file.exists():
            self.validate_config(config)
        
        return config
    
    def validate_config(self, config: Dict) -> None:
        """Validate configuration against schema"""
        with open(self.schema_file, 'r') as f:
            schema = json.load(f)
        
        try:
            jsonschema.validate(config, schema)
        except jsonschema.ValidationError as e:
            print(f"Configuration validation error: {e.message}", file=sys.stderr)
            sys.exit(1)
    
    def check_syntax(self, files: List[Path]) -> List[str]:
        """Check syntax of files"""
        issues = []
        for file_path in files:
            if file_path.suffix == '.py':
                result = subprocess.run(['python', '-m', 'py_compile', str(file_path)], 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    issues.append(f"Syntax error in {file_path}: {result.stderr.strip()}")
        return issues
    
    def run_checks(self) -> int:
        """Run all quality checks"""
        if not self.config.get("enabled", True):
            print("Quality checks are disabled in configuration")
            return 0
        
        print("🔍 Running quality checks...")
        
        # Find files to check
        python_files = list(Path(".").rglob("*.py"))
        
        all_issues = []
        
        # Run enabled checks
        check_types = self.config.get("check_types", ["syntax"])
        
        if "syntax" in check_types:
            print("  Checking syntax...")
            syntax_issues = self.check_syntax(python_files)
            all_issues.extend(syntax_issues)
        
        # Report results
        if all_issues:
            print(f"❌ Found {len(all_issues)} quality issues:")
            for issue in all_issues:
                print(f"  - {issue}")
            return 1
        else:
            print("✅ All quality checks passed!")
            return 0

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="AI Guardrails Quality Checker")
    parser.add_argument("--validate-config", action="store_true", 
                       help="Validate configuration file")
    
    args = parser.parse_args()
    
    checker = QualityChecker()
    
    if args.validate_config:
        print("✅ Configuration is valid")
        return 0
    
    return checker.run_checks()

if __name__ == "__main__":
    sys.exit(main())
```

This example demonstrates:
- ✅ Correct `.ai/` path usage
- ✅ Proper configuration handling
- ✅ Schema validation
- ✅ Error handling
- ✅ Command-line interface
- ✅ Modular design
- ✅ Documentation standards

---

## Migration from Legacy Plugins

If you have existing plugins using the old `ai/` structure, migrate them:

```bash
# 1. Update manifest file_patterns
sed -i 's|ai/scripts|.ai/scripts|g' plugin-manifest.yaml
sed -i 's|ai/schemas|.ai/schemas|g' plugin-manifest.yaml

# 2. Move files to new structure
mkdir -p .ai/scripts .ai/schemas .ai/guardrails
mv ai/scripts/* .ai/scripts/
mv ai/schemas/* .ai/schemas/
rmdir ai/scripts ai/schemas ai

# 3. Update script references
find .ai/scripts -type f -exec sed -i 's|ai/schemas|.ai/schemas|g' {} \;
find .ai/scripts -type f -exec sed -i 's|ai/guardrails|.ai/guardrails|g' {} \;
```

---

## Conclusion

This canonical guide provides everything needed to create high-quality plugins that integrate seamlessly with the AI Guardrails Bootstrap System. Following these conventions ensures consistency, maintainability, and a great developer experience.

For questions or contributions to this guide, please refer to the project documentation or submit issues through the standard channels.
