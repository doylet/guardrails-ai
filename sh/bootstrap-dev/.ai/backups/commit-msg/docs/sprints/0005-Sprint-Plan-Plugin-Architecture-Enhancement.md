# 0005-Sprint-Plan-Plugin-Architecture-Enhancement

**Date:** 2025-01-06
**Status:** � IN-PROGRESS
**Priority:** High
**Related:** [plugin-architecture-best-practices.md], [ADR-004-src-engine-design.md], [0004-Sprint-Plan-Src-Engine-Architecture.md]
**Branch:** feature/plugin-architecture-enhancement

---

## Executive Summary

This sprint implements the plugin architecture enhancement strategy defined in the Plugin Architecture Best Practices document. The goal is to evolve the existing plugin system with enhanced validation, templating, lifecycle management, and configuration schema support while maintaining full backward compatibility with existing plugins.

**Current Status: 50% Complete** - Phase 1 & 2 Complete (Enhanced Domain Models, File Processing, Validation, Legacy Compatibility, Lifecycle Hooks, Template Engine)

## Sprint Goal

Transform the current plugin system into a robust, extensible architecture with enhanced file operations, lifecycle hooks, configuration validation, and template processing while preserving all existing plugin functionality.

**Duration:** 6 weeks (3 phases as defined in best practices document)

---

## Phase 1: Enhanced Manifest & File Operations (Weeks 1-2) ✅ COMPLETE

### Enhanced Plugin Domain Models

- [x] **`packages/domain/plugin_models.py`** - Enhanced plugin data structures:
  - [x] `PluginManifest` dataclass with enhanced metadata
  - [x] `PluginDependency` with version constraints and optional flags
  - [x] `ComponentDefinition` with priority and configuration schema
  - [x] `FileOperation` with action types and conditions
  - [x] `LifecycleHooks` for pre/post/validate hooks
  - [x] `PluginEnvironment` for platform and requirement detection

### Enhanced File Processing System

- [x] **`packages/adapters/plugin_processor.py`** - Enhanced file operation handling:
  - [x] `process_file_operation()` with action type routing
  - [x] `_process_copy()` for simple file copying with mode support
  - [x] `_process_template()` for Jinja2 template processing
  - [x] `_process_merge()` for YAML merging with strategies
  - [x] `_evaluate_condition()` for conditional file operations
  - [x] Template variable resolution from environment and config

### Enhanced Manifest Validation

- [x] **`packages/core/plugin_validator.py`** - Comprehensive plugin validation:
  - [x] Plugin manifest schema validation
  - [x] Dependency resolution and version constraint checking
  - [x] File pattern validation and conflict detection
  - [x] Component configuration schema validation
  - [x] Environment requirement validation
  - [x] Security validation for file operations

### Backward Compatibility Layer

- [x] **`packages/adapters/legacy_plugin_adapter.py`** - Legacy plugin support:
  - [x] Convert legacy `file_patterns` to enhanced `FileOperation` objects
  - [x] Map legacy component definitions to enhanced format
  - [x] Provide default values for new fields
  - [x] Warning system for deprecated features
  - [x] Migration assistance utilities

---

## Phase 2: Lifecycle Hooks & Template Engine (Weeks 3-4) - ✅ COMPLETED

**Status**: ✅ **COMPLETED** (100%)
**Progress**: All Phase 2 deliverables implemented and integrated

### Progress Tracking

#### Week 3: Lifecycle Hook System ✅
- [x] **Plugin Lifecycle Manager** (`src/packages/core/plugin_lifecycle.py`)
  - Secure hook execution with sandboxed environment
  - Resource monitoring and timeout protection
  - Pre/post install, validation, and cleanup hooks
  - Script execution with proper error handling

#### Week 4: Template Engine & Integration ✅
- [x] **Template Engine** (`src/packages/adapters/template_engine.py`)
  - Enhanced Jinja2 processing with security restrictions
  - Custom filters for Git operations and filesystem functions
  - Variable substitution with environment detection
  - Secure template sandbox environment

- [x] **Configuration Validator** (`src/packages/core/config_validator.py`)
  - JSON Schema validation for plugin configuration
  - Configuration inheritance and merging support
  - Schema composition for complex validation rules
  - Profile-based configuration management

- [x] **Component Manager** (`src/packages/core/component_manager.py`)
  - Component dependency resolution with topological sorting
  - Installation ordering based on dependencies and priorities
  - Atomic installation with rollback support
  - Component health monitoring and status tracking

- [x] **Enhanced Plugin Installer** (`src/packages/adapters/enhanced_plugin_installer.py`)
  - Complete plugin installation workflow integration
  - Lifecycle hooks execution with security sandboxing
  - Template processing with variable substitution
  - Dry-run capability and progress reporting

- [x] **Integration with Existing System**
  - Updated component manager to support enhanced plugin installation
  - Backward compatibility maintained with legacy adapter
  - Extended domain constants with plugin-specific settings
  - Fixed import dependencies and compilation issues

### Phase 2 Achievements

#### Lifecycle Hook System
- **Secure Execution Environment**: Sandboxed script execution with resource limits
- **Comprehensive Hook Types**: Pre/post install, validation, cleanup, and component-specific hooks
- **Resource Monitoring**: Memory and execution time limits with automatic termination
- **Error Handling**: Detailed error reporting and graceful failure handling

#### Template Engine
- **Enhanced Jinja2**: Secure template processing with restricted environment
- **Custom Filters**: Git operations, filesystem functions, and utility filters
- **Variable Substitution**: Environment detection and configuration interpolation
- **Security Features**: Path traversal protection and function whitelisting

#### Component Management
- **Dependency Resolution**: Topological sorting for component installation order
- **Atomic Operations**: Installation with rollback support on failure
- **Status Tracking**: Real-time component status monitoring
- **Conflict Detection**: Pre-installation conflict detection and reporting

#### Enhanced Installation
- **Complete Workflow**: End-to-end plugin installation with all lifecycle phases
- **Dry Run Support**: Installation preview without making changes
- **Progress Reporting**: Detailed installation progress and status updates
- **Error Recovery**: Automatic rollback on installation failures

### Integration Points
- ✅ Component Manager enhanced with plugin support
- ✅ Template Engine integrated with file processor
- ✅ Lifecycle hooks integrated with installation workflow
- ✅ Configuration validator integrated with component validation
- ✅ Enhanced installer integrated with existing component system

### Security Implementation
- ✅ Sandboxed script execution environment
- ✅ Resource monitoring and limits
- ✅ Path traversal protection
- ✅ Function whitelisting for templates
- ✅ Configuration validation and sanitization

### Backward Compatibility
- ✅ Legacy plugin adapter maintains 100% compatibility
- ✅ Existing plugins continue to work without modification
- ✅ Gradual migration path for plugin enhancement
- ✅ Feature detection for plugin capabilities

---

## Phase 3: Advanced Features & Plugin Registry (Weeks 5-6) 🟡 PLANNED

### Plugin Registry System

- [ ] **`packages/core/plugin_registry.py`** - Plugin discovery and management:
  - [ ] Local plugin directory scanning
  - [ ] Remote plugin repository support
  - [ ] Plugin versioning and update checking
  - [ ] Plugin dependency resolution
  - [ ] Plugin installation and removal
  - [ ] Plugin validation and security scanning

### Enhanced CLI Commands

- [ ] **`packages/cli/plugin_commands.py`** - Plugin management CLI:
  - [ ] `ai-guardrails plugin list` - List available and installed plugins
  - [ ] `ai-guardrails plugin install <name>` - Install plugin with dependencies
  - [ ] `ai-guardrails plugin update <name>` - Update plugin to latest version
  - [ ] `ai-guardrails plugin validate <path>` - Validate plugin structure
  - [ ] `ai-guardrails plugin info <name>` - Show detailed plugin information
  - [ ] `ai-guardrails plugin remove <name>` - Remove plugin and cleanup

### Advanced File Operations

- [ ] **`packages/adapters/advanced_file_ops.py`** - Sophisticated file handling:
  - [ ] Multi-strategy YAML merging (deep, replace, append)
  - [ ] JSON file operations with schema validation
  - [ ] Binary file handling with checksums
  - [ ] File permission and ownership management
  - [ ] Symlink and directory structure creation
  - [ ] File backup and restoration

### Plugin Development Tools

- [ ] **`packages/tools/plugin_scaffold.py`** - Plugin development assistance:
  - [ ] Plugin project scaffolding
  - [ ] Manifest template generation
  - [ ] Component structure creation
  - [ ] Validation rule generation
  - [ ] Documentation template creation
  - [ ] Testing framework integration

### Performance Optimization

- [ ] **Enhanced Performance Features**:
  - [ ] Plugin manifest caching with invalidation
  - [ ] Lazy loading of plugin components
  - [ ] Parallel plugin processing where safe
  - [ ] Template compilation caching
  - [ ] File operation batching and optimization
  - [ ] Memory usage optimization for large manifests

---

## Enhanced Plugin Manifest Format

### Backward Compatible Extension

```yaml
# Enhanced manifest format (fully backward compatible)
plugin:
  name: "enhanced-plugin"
  version: "2.0.0"
  description: "Example of enhanced plugin format"
  author: "Plugin Developer"
  license: "MIT"
  homepage: "https://github.com/dev/enhanced-plugin"

  # New enhanced fields
  api_version: "v2"
  min_bootstrap_version: ">=2.1.0"

  # Enhanced dependency management
  dependencies:
    - plugin: "core"
      version: ">=1.0.0"
      optional: false
      reason: "Required for base functionality"
    - plugin: "git-hooks"
      version: ">=0.5.0"
      optional: true
      reason: "Optional Git integration"

  # Environment requirements
  environment:
    requires: ["git", "python3"]
    detects: ["python", "yaml", "json"]
    platforms: ["linux", "macos", "windows"]
    min_versions:
      python3: "3.8"
      git: "2.20"

# Enhanced component definitions
components:
  core-component:
    description: "Core functionality with enhanced features"
    priority: 100

    # Enhanced file operations
    files:
      # Simple file copy with enhanced options
      - pattern: "config/**/*.yml"
        action: "copy"
        target: ".ai/"
        mode: 0644
        owner: "user"
        backup: true

      # Template processing with variables
      - pattern: "templates/**/*.template.yml"
        action: "template"
        target: ".ai/"
        mode: 0600
        variables:
          project_name: "{{ env.PROJECT_NAME | default(plugin.name) }}"
          debug_mode: "{{ config.debug | default(false) }}"
          version: "{{ plugin.version }}"

      # YAML merging with strategy
      - pattern: "merge-configs/**/*.yml"
        action: "merge"
        target: ".ai/config.yml"
        strategy: "deep"
        backup: true

      # Conditional files
      - pattern: "prod/**/*"
        action: "copy"
        target: ".github/"
        condition: "{{ env.ENVIRONMENT == 'production' }}"

      # JSON operations
      - pattern: "schemas/**/*.json"
        action: "merge"
        target: ".ai/schemas/"
        strategy: "replace"

    # Lifecycle hooks
    hooks:
      pre_install: "scripts/pre-install.sh"
      post_install: "scripts/post-install.sh"
      validate: "scripts/validate.sh"
      cleanup: "scripts/cleanup.sh"

    # Component configuration schema
    config_schema:
      type: "object"
      properties:
        enable_feature:
          type: "boolean"
          default: true
          description: "Enable the main feature"
        notification_channels:
          type: "array"
          items:
            type: "string"
            pattern: "^(email|slack|teams)$"
          default: ["email"]
          description: "Notification channels to use"
        advanced_settings:
          type: "object"
          properties:
            timeout:
              type: "integer"
              minimum: 1
              maximum: 300
              default: 30
            retry_count:
              type: "integer"
              minimum: 0
              maximum: 5
              default: 3
      required: ["enable_feature"]

# Plugin-level configuration
configuration:
  template_engine: "jinja2"
  enable_validation: true
  cache_templates: true
  backup_files: true

# Profile definitions
profiles:
  minimal:
    description: "Minimal installation"
    components: ["core-component"]
  standard:
    description: "Standard installation with common features"
    components: ["core-component", "optional-features"]
  full:
    description: "Full installation with all features"
    components: ["core-component", "optional-features", "advanced-features"]
```

### Legacy Format Support

```yaml
# Legacy format (continues to work)
plugin:
  name: "legacy-plugin"
  version: "1.0.0"
  description: "Legacy plugin format"
  dependencies: ["core"]

components:
  legacy-component:
    description: "Legacy component"
    file_patterns:
      - ".github/**/*"
      - ".ai/**/*"
```

---

## Implementation Strategy

### Phase 1: Foundation Enhancement

#### Enhanced Domain Models
```python
# packages/domain/plugin_models.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal, Union
from pathlib import Path

@dataclass
class PluginEnvironment:
    requires: List[str] = field(default_factory=list)
    detects: List[str] = field(default_factory=list)
    platforms: List[str] = field(default_factory=list)
    min_versions: Dict[str, str] = field(default_factory=dict)

@dataclass
class PluginDependency:
    plugin: str
    version: str = ">=0.0.0"
    optional: bool = False
    reason: Optional[str] = None

@dataclass
class FileOperation:
    pattern: str
    action: Literal["copy", "template", "merge"]
    target: str
    mode: Optional[int] = None
    owner: Optional[str] = None
    backup: bool = False
    variables: Dict[str, str] = field(default_factory=dict)
    condition: Optional[str] = None
    strategy: Optional[str] = None

@dataclass
class LifecycleHooks:
    pre_install: Optional[str] = None
    post_install: Optional[str] = None
    validate: Optional[str] = None
    cleanup: Optional[str] = None

@dataclass
class ComponentDefinition:
    name: str
    description: str
    priority: int = 100
    files: List[FileOperation] = field(default_factory=list)
    hooks: Optional[LifecycleHooks] = None
    config_schema: Optional[Dict] = None
    dependencies: List[str] = field(default_factory=list)

@dataclass
class PluginManifest:
    name: str
    version: str
    description: str
    author: Optional[str] = None
    license: Optional[str] = None
    homepage: Optional[str] = None
    api_version: str = "v1"
    min_bootstrap_version: str = ">=1.0.0"
    dependencies: List[PluginDependency] = field(default_factory=list)
    environment: Optional[PluginEnvironment] = None
    components: Dict[str, ComponentDefinition] = field(default_factory=dict)
    configuration: Dict[str, Union[str, bool, int]] = field(default_factory=dict)
    profiles: Dict[str, Dict] = field(default_factory=dict)
```

#### Enhanced File Processor
```python
# packages/adapters/plugin_processor.py
import jinja2
from pathlib import Path
from typing import Dict, Any
from ..domain.plugin_models import FileOperation

class PluginProcessor:
    def __init__(self):
        self.template_env = self._setup_template_environment()

    def _setup_template_environment(self) -> jinja2.Environment:
        """Setup secure Jinja2 environment."""
        return jinja2.Environment(
            loader=jinja2.BaseLoader(),
            undefined=jinja2.StrictUndefined,
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )

    def process_file_operation(self, operation: FileOperation, context: Dict[str, Any]) -> None:
        """Process a file operation based on its action type."""
        if not self._evaluate_condition(operation.condition, context):
            return

        if operation.action == "copy":
            self._process_copy(operation, context)
        elif operation.action == "template":
            self._process_template(operation, context)
        elif operation.action == "merge":
            self._process_merge(operation, context)
        else:
            raise ValueError(f"Unknown action type: {operation.action}")

    def _evaluate_condition(self, condition: Optional[str], context: Dict[str, Any]) -> bool:
        """Evaluate conditional expression."""
        if not condition:
            return True

        template = self.template_env.from_string(f"{{% if {condition} %}}true{{% endif %}}")
        result = template.render(**context)
        return result.strip() == "true"

    def _process_copy(self, operation: FileOperation, context: Dict[str, Any]) -> None:
        """Process file copy operation."""
        # Implementation for file copying with mode, owner, backup
        pass

    def _process_template(self, operation: FileOperation, context: Dict[str, Any]) -> None:
        """Process template operation with variable substitution."""
        # Implementation for template processing
        pass

    def _process_merge(self, operation: FileOperation, context: Dict[str, Any]) -> None:
        """Process YAML/JSON merge operation."""
        # Implementation for file merging with strategies
        pass
```

### Phase 2: Lifecycle and Templating

#### Lifecycle Hook System
```python
# packages/core/plugin_lifecycle.py
import subprocess
import os
from pathlib import Path
from typing import Dict, Any, Optional
from ..domain.plugin_models import LifecycleHooks

class PluginLifecycle:
    def __init__(self, plugin_path: Path):
        self.plugin_path = plugin_path

    def execute_hooks(self, hooks: LifecycleHooks, hook_type: str, context: Dict[str, Any]) -> bool:
        """Execute lifecycle hook with security boundaries."""
        script_path = getattr(hooks, hook_type, None)
        if not script_path:
            return True

        return self._execute_script(script_path, context)

    def _execute_script(self, script_path: str, context: Dict[str, Any]) -> bool:
        """Execute script with security restrictions."""
        full_path = self.plugin_path / script_path

        # Security validation
        if not self._validate_script_path(full_path):
            raise SecurityError(f"Script path outside plugin directory: {script_path}")

        # Execute with timeout and resource limits
        env = os.environ.copy()
        env.update({f"PLUGIN_{k.upper()}": str(v) for k, v in context.items()})

        try:
            result = subprocess.run(
                [str(full_path)],
                cwd=self.plugin_path,
                env=env,
                timeout=300,  # 5 minute timeout
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            raise PluginError(f"Hook script timeout: {script_path}")

    def _validate_script_path(self, script_path: Path) -> bool:
        """Validate script is within plugin directory."""
        try:
            script_path.resolve().relative_to(self.plugin_path.resolve())
            return True
        except ValueError:
            return False
```

### Phase 3: Advanced Features

#### Plugin Registry System
```python
# packages/core/plugin_registry.py
from pathlib import Path
from typing import List, Dict, Optional
from ..domain.plugin_models import PluginManifest

class PluginRegistry:
    def __init__(self, plugin_directories: List[Path]):
        self.plugin_directories = plugin_directories
        self._cache = {}

    def discover_plugins(self) -> Dict[str, PluginManifest]:
        """Discover all available plugins."""
        plugins = {}

        for directory in self.plugin_directories:
            if directory.exists():
                for plugin_dir in directory.iterdir():
                    if plugin_dir.is_dir():
                        manifest = self._load_plugin_manifest(plugin_dir)
                        if manifest:
                            plugins[manifest.name] = manifest

        return plugins

    def install_plugin(self, plugin_name: str, version: Optional[str] = None) -> bool:
        """Install plugin with dependency resolution."""
        # Implementation for plugin installation
        pass

    def validate_plugin(self, plugin_path: Path) -> List[str]:
        """Validate plugin structure and manifest."""
        # Implementation for comprehensive plugin validation
        pass
```

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/test_plugin_models.py
import pytest
from packages.domain.plugin_models import PluginManifest, FileOperation

class TestPluginModels:
    def test_plugin_manifest_creation(self):
        """Test plugin manifest creation and validation."""
        manifest = PluginManifest(
            name="test-plugin",
            version="1.0.0",
            description="Test plugin"
        )
        assert manifest.name == "test-plugin"
        assert manifest.api_version == "v1"  # Default value

    def test_file_operation_validation(self):
        """Test file operation validation."""
        operation = FileOperation(
            pattern="*.yml",
            action="copy",
            target=".ai/"
        )
        assert operation.action in ["copy", "template", "merge"]

# tests/unit/test_plugin_processor.py
class TestPluginProcessor:
    def test_template_processing(self):
        """Test template processing with variables."""
        processor = PluginProcessor()
        operation = FileOperation(
            pattern="config.template.yml",
            action="template",
            target=".ai/config.yml",
            variables={"project": "test"}
        )
        # Test template processing
        pass
```

### Integration Tests

```python
# tests/integration/test_plugin_lifecycle.py
import tempfile
from pathlib import Path
from packages.core.plugin_lifecycle import PluginLifecycle

class TestPluginLifecycle:
    def test_hook_execution(self):
        """Test lifecycle hook execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_path = Path(temp_dir)

            # Create test hook script
            hook_script = plugin_path / "scripts" / "test-hook.sh"
            hook_script.parent.mkdir(parents=True)
            hook_script.write_text("#!/bin/bash\necho 'Hook executed'\nexit 0\n")
            hook_script.chmod(0o755)

            # Test hook execution
            lifecycle = PluginLifecycle(plugin_path)
            result = lifecycle._execute_script("scripts/test-hook.sh", {})
            assert result is True
```

### End-to-End Tests

```python
# tests/e2e/test_enhanced_plugin_system.py
class TestEnhancedPluginSystem:
    def test_complete_plugin_workflow(self):
        """Test complete plugin installation workflow."""
        # Test plugin discovery, validation, installation
        pass

    def test_backward_compatibility(self):
        """Test that legacy plugins continue to work."""
        # Test legacy plugin installation
        pass
```

---

## Migration Strategy

### For Existing Plugins

#### Automatic Migration
- **Phase 1**: All existing plugins work without changes
- **Phase 2**: Automatic conversion of legacy `file_patterns` to `FileOperation`
- **Phase 3**: Migration assistance tools for enhanced features

#### Migration Tools
```python
# packages/tools/plugin_migrator.py
class PluginMigrator:
    def migrate_legacy_manifest(self, legacy_manifest: Dict) -> Dict:
        """Convert legacy manifest to enhanced format."""
        pass

    def suggest_improvements(self, plugin_path: Path) -> List[str]:
        """Suggest improvements for existing plugins."""
        pass
```

### Documentation Updates

- [ ] Update plugin development guide with enhanced format
- [ ] Create migration guide for existing plugin developers
- [ ] Add examples for all new features
- [ ] Update CLI reference documentation

---

## Success Metrics

### Technical Metrics
- **100% backward compatibility** with existing plugins
- **Enhanced validation** catches 90% of common plugin errors
- **Template processing** supports complex configuration scenarios
- **Lifecycle hooks** enable advanced plugin behaviors
- **Performance** maintains <2 second plugin processing time

### Developer Experience Metrics
- **Plugin creation time** reduced by 50% with scaffolding tools
- **Configuration errors** reduced by 75% with schema validation
- **Plugin debugging** improved with enhanced error messages
- **Documentation completeness** for all new features

### Ecosystem Metrics
- **Plugin registry** supports community contributions
- **Plugin validation** ensures quality and security
- **Plugin dependencies** enable composable functionality

---

## Dependencies

### Upstream
- **Sprint 004**: Src Engine Architecture - Provides foundation packages
- **Current Plugin System**: 5 existing plugins continue to work
- **Python Dependencies**: Jinja2, jsonschema, PyYAML

### Downstream
- **Future Sprint**: Plugin Marketplace and Community Features
- **Documentation**: Enhanced plugin development guides
- **Tooling**: IDE integration and development tools

---

## Risks & Mitigation

### 🚨 Backward Compatibility Risk
**Risk**: Changes break existing plugins
**Mitigation**:
- Comprehensive testing with all existing plugins
- Legacy adapter layer for smooth transition
- Feature flags for gradual rollout

### 🚨 Complexity Risk
**Risk**: Enhanced features make system too complex
**Mitigation**:
- Maintain simple defaults for common use cases
- Progressive disclosure of advanced features
- Clear documentation and examples

### 🚨 Security Risk
**Risk**: Lifecycle hooks introduce security vulnerabilities
**Mitigation**:
- Sandboxed script execution
- Path validation and restrictions
- Resource limits and timeouts

### 🚨 Performance Risk
**Risk**: Enhanced features slow down plugin processing
**Mitigation**:
- Template caching and optimization
- Lazy loading of plugin components
- Performance benchmarks and monitoring

---

## Definition of Done

### Phase 1 Complete
- [x] Enhanced plugin domain models implemented
- [x] File operation processing with action types
- [x] Backward compatibility with all existing plugins
- [x] Comprehensive validation system

### Phase 2 Complete
- [x] Lifecycle hook system with security boundaries
- [x] Template engine with Jinja2 integration
- [x] Configuration schema validation
- [x] Component dependency management

### Phase 3 Complete
- [ ] Plugin registry and management system
- [ ] Enhanced CLI commands for plugin management
- [ ] Plugin development tools and scaffolding
- [ ] Performance optimization and caching

### Overall Sprint Complete
- [ ] All 5 existing plugins work without modification
- [ ] Enhanced plugin format fully supported
- [ ] Comprehensive testing suite (>90% coverage)
- [ ] Documentation updated and migration guides available
- [ ] Performance meets requirements (<2s processing time)

---

**Status:** 🟡 Ready for Implementation
**Next Review:** Post-Phase 1 completion (Week 2)
**Owner:** Plugin System Team
**Epic:** Plugin Architecture Modernization
