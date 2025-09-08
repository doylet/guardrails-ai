# How the AI Guardrails Bootstrap System Works
## Comprehensive System Operation Guide

**Version:** 2.0.0
**Date:** September 6, 2025
**Audience:** Developers, DevOps Engineers, System Architects

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Core Architecture](#2-core-architecture)
3. [Initialization and Bootstrap Process](#3-initialization-and-bootstrap-process)
4. [Plugin Discovery and Integration](#4-plugin-discovery-and-integration)
5. [Component Installation Flow](#5-component-installation-flow)
6. [File Discovery and Pattern Resolution](#6-file-discovery-and-pattern-resolution)
7. [Configuration Management](#7-configuration-management)
8. [State Management and Persistence](#8-state-management-and-persistence)
9. [Validation and Diagnostics](#9-validation-and-diagnostics)
10. [Complete Operation Walkthrough](#10-complete-operation-walkthrough)
11. [Data Flow Diagrams](#11-data-flow-diagrams)
12. [Error Handling and Recovery](#12-error-handling-and-recovery)
13. [How the system works](#13-The-Answer-Explicit-Target-Structure-Definition)

---

## 1. System Overview

The AI Guardrails Bootstrap System is a **modular, infrastructure-as-code platform** that automates the installation and configuration of AI development tools across software projects. It transforms a complex, manual setup process into a declarative, repeatable operation.

### 1.1 What It Does

The system installs and configures:
- **Language-specific linting and testing configurations**
- **AI-powered code review workflows**
- **Documentation templates and validation tools**
- **Pre-commit hooks and GitHub integrations**
- **Plugin-based extensibility for specialized tooling**

### 1.2 How It Works (High Level)

```
User Command → Bootstrap Orchestrator → Plugin Discovery → Manifest Merging →
Component Installation → File Operations → State Updates → Validation
```

### 1.3 Key Design Principles

1. **Declarative Configuration**: Everything defined in YAML manifests
2. **Dynamic Discovery**: No hardcoded file lists, everything discovered via patterns
3. **Plugin Architecture**: Extensible through independent plugins
4. **Idempotent Operations**: Safe to run multiple times
5. **Infrastructure-as-Code**: Version-controlled, reproducible configurations

---

## 2. Core Architecture

### 2.1 Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                         │
│  Command Line Interface + Interactive Selection                │
├─────────────────────────────────────────────────────────────────┤
│                     PRESENTATION LAYER                         │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ StatePresenter  │ │ComponentPresenter│ │ ProfilePresenter│   │
│  │ - State display │ │ - Component info │ │ - Profile info  │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                     APPLICATION LAYER                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           InfrastructureBootstrap                       │   │
│  │           - Main orchestrator                           │   │
│  │           - Composition root                            │   │
│  │           - Use case coordination                       │   │
│  └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                       DOMAIN LAYER                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────┐ │
│  │StateManager  │ │ComponentMgr  │ │PluginSystem  │ │ Doctor  │ │
│  │- State track │ │- File ops    │ │- Plugin disc │ │- Diagnostics│
│  └──────────────┘ └──────────────┘ └──────────────┘ └─────────┘ │
│  ┌──────────────┐ ┌──────────────┐                             │
│  │ConfigManager │ │YAMLOperations│                             │
│  │- Config merge│ │- YAML utils  │                             │
│  └──────────────┘ └──────────────┘                             │
├─────────────────────────────────────────────────────────────────┤
│                   INFRASTRUCTURE LAYER                         │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ File System     │ │ YAML Processing │ │ Git Integration │   │
│  │ - File I/O      │ │ - Parse/merge   │ │ - Repo status   │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

| Component | What It Does | Key Operations |
|-----------|--------------|----------------|
| **InfrastructureBootstrap** | Main orchestrator that coordinates all operations | `install_profile()`, `install_component()`, `list_components()` |
| **StateManager** | Tracks what's installed and when | `load_state()`, `update_state_for_profile()`, `is_component_installed()` |
| **ComponentManager** | Handles file discovery and installation | `discover_files()`, `install_component()`, `_install_single_file()` |
| **PluginSystem** | Discovers and integrates plugins | `discover_plugins()`, `get_merged_manifest()`, `is_plugin_component()` |
| **ConfigManager** | Customizes configuration files | `customize_precommit_config()`, `merge_yaml_file()` |
| **Doctor** | Validates system health | `run_diagnostics()`, `_check_target_structure()` |

---

## 3. Initialization and Bootstrap Process

### 3.1 System Startup Sequence

When you run the bootstrap system, here's what happens:

#### Step 1: Initialization
```python
# User runs: python3 infrastructure_bootstrap.py install standard
bootstrap = InfrastructureBootstrap('.')  # Target directory
```

#### Step 2: Component Creation and Dependency Injection
```python
def __init__(self, target_dir: str):
    self.target_dir = Path(target_dir)

    # 1. Set up paths
    self.template_repo = self._find_template_repo()

    # 2. Create core managers (dependency injection)
    self.state_manager = StateManager(self.target_dir)
    self.plugin_system = PluginSystem(self.target_dir)
    self.component_manager = ComponentManager(
        self.target_dir,
        self.template_repo,
        self.plugin_system
    )

    # 3. Load and merge manifests
    self.base_manifest = self._load_manifest()
    self.merged_manifest = self.plugin_system.get_merged_manifest(self.base_manifest)
```

#### Step 3: Manifest Loading and Validation
```python
def _load_manifest(self) -> Dict:
    """Load the base installation manifest"""
    manifest_path = self.template_repo.parent / "installation-manifest.yaml"
    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)

    # Validate manifest structure
    self._validate_manifest_structure(manifest)
    return manifest
```

### 3.2 Directory Structure Discovery

The system discovers its operational environment:

```python
def _find_template_repo(self) -> Path:
    """Locate the template repository"""
    # Look for src/ai-guardrails-templates relative to script
    script_dir = Path(__file__).parent
    template_repo = script_dir.parent / "src" / "ai-guardrails-templates"

    if not template_repo.exists():
        raise ValueError(f"Template repository not found: {template_repo}")

    return template_repo
```

**Directory Layout Understanding:**
```
bootstrap-dev/                    ← Root project directory
├── src/                         ← Source directory
│   ├── installation-manifest.yaml ← Main configuration
│   ├── ai-guardrails-templates/   ← Template files
│   │   ├── .ai/                  ← Core templates
│   │   ├── ai/                   ← Automation templates
│   │   └── docs/                 ← Documentation templates
│   └── plugins/                  ← Plugin directory
│       ├── commit-msg-kit/       ← Individual plugins
│       ├── demos-on-rails-kit/
│       └── doc-guardrails-kit/
└── target-project/               ← Where files get installed
    ├── .ai/                      ← Installed configuration
    ├── ai/                       ← Installed automation
    └── docs/                     ← Installed documentation
```

---

## 4. Plugin Discovery and Integration

### 4.1 Plugin Discovery Process

The plugin system automatically discovers available plugins:

#### Step 1: Scan Plugin Directory
```python
def discover_plugins(self) -> Dict:
    """Discover and load plugin manifests from tool installation"""
    plugins = {}

    # Look in src/plugins/ directory
    if self.plugins_dir.exists():
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir():
                manifest_file = plugin_dir / "plugin-manifest.yaml"
                if manifest_file.exists():
                    # Load and parse plugin manifest
                    with open(manifest_file) as f:
                        manifest = yaml.safe_load(f)
                        plugin_name = manifest.get('name', plugin_dir.name)
                        plugins[plugin_name] = {
                            'path': plugin_dir,
                            'manifest': manifest
                        }
    return plugins
```

#### Step 2: Plugin Manifest Structure
Each plugin defines its capabilities in `plugin-manifest.yaml`:

```yaml
# Example: plugins/demos-on-rails-kit/plugin-manifest.yaml
plugin:
  name: "demos-on-rails-kit"
  version: "1.0.0"
  description: "Demo harness ensuring production interface compliance"
  dependencies: ["core", "scripts"]  # What it needs
  environment:
    detects: ["python", "yaml"]      # What it can work with
    requires: ["python3"]            # What it must have

components:
  demo-harness:                      # New component definition
    description: "Demo execution and validation harness"
    file_patterns:
      - "ai/tools/**/*.py"           # Files to install
      - "ai/demo_scenarios/**/*.yaml"

profiles:
  demo-basic:                        # New profile definition
    description: "Basic demo harness"
    components: ["demo-harness", "core", "scripts"]
```

### 4.2 Manifest Merging Process

The system creates a unified view by merging base and plugin manifests:

#### Step 1: Base Manifest Loading
```python
# Load base installation-manifest.yaml
base_components = {
    "core": {"file_patterns": [".ai/*.yaml"]},
    "scripts": {"file_patterns": ["ai/scripts/**/*.py"]},
    # ... more base components
}
```

#### Step 2: Plugin Integration
```python
def get_merged_manifest(self, base_manifest: Dict) -> Dict:
    """Get manifest merged with plugin configurations"""
    merged = base_manifest.copy()

    for plugin_name, plugin_data in self.plugins.items():
        plugin_manifest = plugin_data['manifest']

        # Merge components (plugins can add new components)
        if 'components' in plugin_manifest:
            merged['components'].update(plugin_manifest['components'])

        # Merge profiles (plugins can add new profiles)
        if 'profiles' in plugin_manifest:
            merged['profiles'].update(plugin_manifest['profiles'])

    return merged
```

#### Step 3: Unified Component View
After merging, the system sees all components from base + plugins:

```python
# Merged result contains:
{
    "components": {
        # Base components
        "core": {"file_patterns": [".ai/*.yaml"]},
        "scripts": {"file_patterns": ["ai/scripts/**/*.py"]},

        # Plugin components
        "demo-harness": {"file_patterns": ["ai/tools/**/*.py"]},
        "doc-workflows": {"file_patterns": [".github/workflows/**/*.yaml"]},
    },
    "profiles": {
        # Base profiles
        "standard": {"components": ["core", "scripts", "docs"]},

        # Plugin profiles
        "demo-basic": {"components": ["demo-harness", "core"]},
        "doc-full": {"components": ["doc-workflows", "doc-templates"]},
    }
}
```

---

## 5. Component Installation Flow

### 5.1 Profile Installation Process

When a user runs `install standard`, here's the complete flow:

#### Step 1: Profile Resolution
```python
def install_profile(self, profile_name: str, force: bool = False) -> bool:
    """Install a complete profile (set of components)"""

    # 1. Validate profile exists
    if profile_name not in self.merged_manifest['profiles']:
        available = list(self.merged_manifest['profiles'].keys())
        raise ValueError(f"Unknown profile: {profile_name}. Available: {available}")

    # 2. Get component list for profile
    profile_config = self.merged_manifest['profiles'][profile_name]
    components = profile_config['components']

    print(f"Installing profile: {profile_name}")
    print(f"Components: {components}")
```

#### Step 2: Component Installation Loop
```python
    # 3. Install each component in the profile
    success = True
    installed_components = []

    for component in components:
        print(f"\n--- Installing component: {component} ---")

        if self.install_component(component, force):
            installed_components.append(component)
            # Update state after each successful component
            self.state_manager.update_state_for_component(component)
        else:
            print(f"Failed to install component: {component}")
            success = False
            # Continue with other components (partial installation)

    # 4. Update profile state if any components installed
    if installed_components:
        self.state_manager.update_state_for_profile(profile_name, installed_components)

    return success
```

### 5.2 Individual Component Installation

#### Step 1: Component Validation and Discovery
```python
def install_component(self, component: str, force: bool = False) -> bool:
    """Install a specific component"""

    # 1. Validate component exists in merged manifest
    if component not in self.merged_manifest['components']:
        available = list(self.merged_manifest['components'].keys())
        raise ValueError(f"Unknown component: {component}. Available: {available}")

    # 2. Discover files using dynamic patterns
    files = self.component_manager.discover_files(component, self.merged_manifest)
    if not files:
        print(f"No files found for component: {component}")
        return False

    print(f"Installing component: {component} ({len(files)} files)")
```

#### Step 2: File Installation Loop
```python
    # 3. Install each file
    success = True
    for rel_file in files:
        if not self.component_manager._install_single_file(
            component, rel_file, force, self.merged_manifest
        ):
            success = False
            # Continue with other files

    # 4. Post-installation customization
    if success:
        if component == 'precommit':
            # Special handling for pre-commit configuration
            self.component_manager.config_manager.customize_precommit_config()
            self.component_manager.config_manager.install_precommit_hooks()

    return success
```

---

## 6. File Discovery and Pattern Resolution

### 6.1 Dynamic File Discovery

The system uses **dynamic file discovery** instead of hardcoded file lists:

#### Step 1: Pattern-Based Discovery
```python
def discover_files(self, component: str, manifest: Dict) -> List[str]:
    """Dynamically discover files based on patterns - NO hardcoding!"""

    # 1. Get component configuration
    component_config = manifest['components'][component]
    patterns = component_config['file_patterns']

    # 2. Determine if this is a plugin component
    is_plugin_component = self.plugin_system.is_plugin_component(component)

    discovered = []
    for pattern in patterns:
        if is_plugin_component:
            # Search in plugin directory
            plugin_path = self.plugin_system.get_plugin_path_for_component(component)
            search_pattern = str(plugin_path / pattern)
        else:
            # Search in template repository
            search_pattern = str(self.template_repo / pattern)

        # Use glob for pattern matching
        discovered.extend(Path(f) for f in glob(search_pattern, recursive=True))

    # 3. Convert to relative paths
    relative_files = []
    base_path = plugin_path if is_plugin_component else self.template_repo
    relative_files = [str(f.relative_to(base_path)) for f in discovered if f.is_file()]

    return relative_files
```

#### Step 2: Pattern Examples and Resolution

**Base Component Pattern:**
```yaml
# installation-manifest.yaml
components:
  scripts:
    file_patterns:
      - "ai/scripts/**/*.py"    # Recursive: all .py files in subdirectories
      - "ai/scripts/**/*.sh"    # Recursive: all .sh files in subdirectories
```

**Resolves to:**
```
src/ai-guardrails-templates/ai/scripts/check_envelope.py
src/ai-guardrails-templates/ai/scripts/lang_lint.sh
src/ai-guardrails-templates/ai/scripts/policy/check_demo_on_rails.py
# ... more files discovered dynamically
```

**Plugin Component Pattern:**
```yaml
# plugins/demos-on-rails-kit/plugin-manifest.yaml
components:
  demo-harness:
    file_patterns:
      - "ai/tools/**/*.py"
      - "ai/demo_scenarios/**/*.yaml"
```

**Resolves to:**
```
src/plugins/demos-on-rails-kit/ai/tools/demo_runner.py
src/plugins/demos-on-rails-kit/ai/demo_scenarios/basic_demo.yaml
# ... more plugin files discovered dynamically
```

### 6.2 Target Path Resolution

#### Step 1: Target Path Calculation
```python
def _install_single_file(self, component: str, rel_file: str, force: bool, manifest: Dict) -> bool:
    """Install a single file from component to target"""

    # 1. Apply target prefix stripping if configured
    target_rel_file = self._apply_target_prefix_stripping(component, rel_file, manifest)

    # 2. Calculate source and target paths
    if self.plugin_system.is_plugin_component(component):
        plugin_path = self.plugin_system.get_plugin_path_for_component(component)
        src_path = plugin_path / rel_file
    else:
        src_path = self.template_repo / rel_file

    target_path = self.target_dir / target_rel_file
```

#### Step 2: Target Prefix Stripping
```python
def _apply_target_prefix_stripping(self, component: str, rel_file: str, manifest: Dict) -> str:
    """Apply target_prefix stripping if configured for component"""
    component_config = manifest['components'][component]
    target_prefix = component_config.get('target_prefix')

    if target_prefix is not None:
        # Remove the prefix from the file path
        if rel_file.startswith(target_prefix):
            return rel_file[len(target_prefix):]

    return rel_file
```

**Example of Prefix Stripping:**
```yaml
# Component configuration
github:
  file_patterns: ["templates/.github/**/*"]
  target_prefix: "templates/"  # Strip 'templates/' when installing
```

**Result:**
- Source: `templates/.github/workflows/ci.yaml`
- Target: `.github/workflows/ci.yaml` (prefix stripped)

---

## 7. Configuration Management

### 7.1 YAML File Merging

The system intelligently merges configuration files instead of overwriting:

#### Step 1: Merge Decision Logic
```python
def _should_merge_file(self, src_path: Path, target_path: Path) -> bool:
    """Determine if file should be merged vs copied"""

    # 1. Only merge YAML/JSON files
    if src_path.suffix not in ['.yaml', '.yml', '.json']:
        return False

    # 2. Only merge if target already exists
    if not target_path.exists():
        return False

    # 3. Check if it's a mergeable file type
    mergeable_files = [
        '.pre-commit-config.yaml',
        'guardrails.yaml',
        # ... other mergeable configurations
    ]

    return target_path.name in mergeable_files
```

#### Step 2: YAML Merging Process
```python
def merge_yaml_file(self, source_file: Path, target_file: Path):
    """Merge YAML files with intelligent conflict resolution"""

    # 1. Load both files
    with open(source_file) as f:
        source_data = yaml.safe_load(f)

    if target_file.exists():
        with open(target_file) as f:
            target_data = yaml.safe_load(f) or {}
    else:
        target_data = {}

    # 2. Perform deep merge
    if source_file.name == '.pre-commit-config.yaml':
        merged = self._merge_precommit_config(source_data, target_data)
    else:
        merged = YAMLOperations.deep_merge(target_data, source_data)

    # 3. Write merged result
    with open(target_file, 'w') as f:
        yaml.dump(merged, f, default_flow_style=False, sort_keys=False)
```

### 7.2 Pre-commit Configuration Customization

#### Step 1: Language Detection and Exclusion
```python
def customize_precommit_config(self):
    """Customize pre-commit config based on project languages"""

    # 1. Detect project languages
    languages = self._detect_project_languages()

    # 2. Load excluded languages from configuration
    excluded_languages = self._get_excluded_languages()

    # 3. Apply exclusions to pre-commit config
    self._apply_language_exclusions(languages, excluded_languages)

def _detect_project_languages(self) -> List[str]:
    """Auto-detect programming languages in project"""
    languages = []

    # Check for common language indicators
    if (self.target_dir / "package.json").exists():
        languages.append("javascript")
    if list(self.target_dir.glob("*.py")):
        languages.append("python")
    if (self.target_dir / "Cargo.toml").exists():
        languages.append("rust")
    # ... more language detection

    return languages
```

#### Step 2: Hook Customization
```python
def _apply_language_exclusions(self, detected: List[str], excluded: List[str]):
    """Remove hooks for excluded languages"""
    config_path = self.target_dir / ".pre-commit-config.yaml"

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Filter out repos/hooks for excluded languages
    filtered_repos = []
    for repo in config.get('repos', []):
        if not self._should_exclude_repo(repo, excluded):
            filtered_repos.append(repo)

    config['repos'] = filtered_repos

    # Write updated configuration
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
```

---

## 8. State Management and Persistence

### 8.1 State File Structure

The system maintains persistent state in `.ai-guardrails-state.yaml`:

```yaml
# Example state file content
version: '1.0.0'
installed_profile: 'standard'
installed_components:
  - 'core'
  - 'schemas'
  - 'scripts'
  - 'precommit'
  - 'docs'
installation_history:
  - timestamp: '2025-09-06T10:30:00'
    action: 'install_component'
    component: 'core'
  - timestamp: '2025-09-06T10:30:15'
    action: 'install_profile'
    profile: 'standard'
    components: ['core', 'schemas', 'scripts', 'precommit', 'docs']
```

### 8.2 State Operations

#### Step 1: State Loading with Error Recovery
```python
def load_state(self) -> Dict:
    """Load the installation state file"""
    if not self.state_path.exists():
        # Create default state for new installations
        return {
            'version': '1.0.0',
            'installed_profile': None,
            'installed_components': [],
            'installation_history': []
        }

    try:
        with open(self.state_path) as f:
            state = yaml.safe_load(f)
            return state or self._create_default_state()
    except Exception as e:
        print(f"Failed to load state file: {e}")
        # Return default state instead of failing
        return self._create_default_state()
```

#### Step 2: State Updates
```python
def update_state_for_component(self, component: str):
    """Update state file after component installation"""
    state = self.load_state()

    # Add component if not already present
    if component not in state.get('installed_components', []):
        state.setdefault('installed_components', []).append(component)

    # Add to installation history
    history_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'install_component',
        'component': component
    }
    state.setdefault('installation_history', []).append(history_entry)

    # Persist changes
    self.save_state(state)

def update_state_for_profile(self, profile: str, components: List[str]):
    """Update state file after profile installation"""
    state = self.load_state()

    # Update current profile
    state['installed_profile'] = profile

    # Merge component lists (union of existing + new)
    existing_components = set(state.get('installed_components', []))
    new_components = set(components)
    state['installed_components'] = list(existing_components.union(new_components))

    # Add to history
    history_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'install_profile',
        'profile': profile,
        'components': components
    }
    state.setdefault('installation_history', []).append(history_entry)

    self.save_state(state)
```

---

## 9. Validation and Diagnostics

### 9.1 Multi-Layer Validation System

The system performs validation at multiple stages:

#### Step 1: Pre-Installation Validation
```python
def install_profile(self, profile_name: str, force: bool = False) -> bool:
    # 1. Validate profile exists
    if profile_name not in self.merged_manifest['profiles']:
        raise ValueError(f"Unknown profile: {profile_name}")

    # 2. Validate all components in profile exist
    profile_config = self.merged_manifest['profiles'][profile_name]
    components = profile_config['components']

    for component in components:
        if component not in self.merged_manifest['components']:
            raise ValueError(f"Profile {profile_name} references unknown component: {component}")
```

#### Step 2: File Discovery Validation
```python
def discover_files(self, component: str, manifest: Dict) -> List[str]:
    # Validate component exists
    if component not in manifest['components']:
        raise ValueError(f"Unknown component: {component}")

    # Validate patterns resolve to actual files
    files = self._resolve_patterns(patterns)
    if not files:
        print(f"Warning: No files found for component {component}")

    return files
```

### 9.2 Diagnostic System

#### Step 1: Comprehensive Health Checks
```python
def run_diagnostics(self, manifest: Dict, focus: str = "all") -> bool:
    """Comprehensive system diagnostics"""
    total_issues = 0

    print("=== AI Guardrails Diagnostics ===")

    if focus in ["all", "yaml"]:
        print("\n--- YAML Structure Check ---")
        total_issues += self._check_yaml_structure()

    if focus in ["all", "files"]:
        print("\n--- File Integrity Check ---")
        total_issues += self._check_file_integrity(manifest)

    if focus in ["all", "components"]:
        print("\n--- Component Status Check ---")
        total_issues += self._check_component_status(manifest)

    if focus in ["all", "structure"]:
        print("\n--- Target Structure Check ---")
        total_issues += self._check_target_structure(manifest)

    if focus in ["all", "environment"]:
        print("\n--- Environment Check ---")
        total_issues += self._check_environment()

    print(f"\n=== Diagnostics Complete: {total_issues} issues found ===")
    return total_issues == 0
```

#### Step 2: Specific Diagnostic Checks
```python
def _check_component_status(self, manifest: Dict) -> int:
    """Check status of installed components"""
    issues = 0
    state = self.state_manager.load_state()
    installed_components = state.get('installed_components', [])

    print(f"Installed components: {len(installed_components)}")

    for component in installed_components:
        if component not in manifest['components']:
            print(f"  ❌ {component}: Component definition not found")
            issues += 1
        else:
            # Check if component files actually exist
            try:
                files = self.component_manager.discover_files(component, manifest)
                missing_files = []

                for rel_file in files:
                    target_path = self._get_target_path(component, rel_file, manifest)
                    if not target_path.exists():
                        missing_files.append(rel_file)

                if missing_files:
                    print(f"  ⚠️  {component}: {len(missing_files)} files missing")
                    issues += 1
                else:
                    print(f"  ✅ {component}: All files present")

            except Exception as e:
                print(f"  ❌ {component}: Error checking files - {e}")
                issues += 1

    return issues
```

---

## 10. Complete Operation Walkthrough

Let's trace through a complete operation: `python3 infrastructure_bootstrap.py install standard`

### 10.1 Initialization Phase (0-2 seconds)

```python
# 1. Bootstrap object creation
bootstrap = InfrastructureBootstrap('.')

# 2. Path resolution
# - Finds src/ai-guardrails-templates/
# - Finds src/plugins/
# - Sets target as current directory

# 3. Manager creation
# - StateManager created
# - PluginSystem created and discovers plugins
# - ComponentManager created with dependencies

# 4. Manifest loading and merging
# - Loads installation-manifest.yaml
# - Discovers 4 plugins: commit-msg-kit, demos-on-rails-kit, doc-guardrails-kit, root-hygiene-kit
# - Merges plugin components and profiles into unified manifest
```

### 10.2 Plugin Discovery Phase (2-3 seconds)

```python
# Plugin discovery finds:
plugins = {
    'commit-msg-kit': {
        'path': Path('src/plugins/commit-msg-kit'),
        'manifest': {
            'components': {'commit-msg-templates': {...}},
            'profiles': {'commit-msg-basic': {...}}
        }
    },
    'demos-on-rails-kit': {
        'path': Path('src/plugins/demos-on-rails-kit'),
        'manifest': {
            'components': {'demo-harness': {...}},
            'profiles': {'demo-basic': {...}}
        }
    },
    # ... more plugins
}

# Manifest merging creates unified view:
merged_manifest = {
    'components': {
        # Base components
        'core': {'file_patterns': ['.ai/*.yaml']},
        'scripts': {'file_patterns': ['ai/scripts/**/*.py']},

        # Plugin components
        'demo-harness': {'file_patterns': ['ai/tools/**/*.py']},
        'commit-msg-templates': {'file_patterns': ['templates/.github/**/*']},
        # ... all components from base + plugins
    },
    'profiles': {
        # Base profiles
        'standard': {'components': ['core', 'schemas', 'scripts', 'precommit', 'docs']},

        # Plugin profiles
        'demo-basic': {'components': ['demo-harness', 'core']},
        # ... all profiles from base + plugins
    }
}
```

### 10.3 Profile Installation Phase (3-10 seconds)

```python
# 1. Profile validation
profile_name = 'standard'
if 'standard' not in merged_manifest['profiles']:
    raise ValueError("Unknown profile")

# 2. Component list extraction
components = ['core', 'schemas', 'scripts', 'precommit', 'docs']

# 3. Component installation loop
for component in components:
    print(f"--- Installing component: {component} ---")

    # 3a. File discovery for component
    files = component_manager.discover_files(component, merged_manifest)
    # Example for 'core' component:
    # files = ['.ai/guardrails.yaml', '.ai/envelope.json.example']

    # 3b. File installation loop
    for rel_file in files:
        # Determine source and target paths
        src_path = template_repo / rel_file  # src/ai-guardrails-templates/.ai/guardrails.yaml
        target_path = target_dir / rel_file  # ./.ai/guardrails.yaml

        # Install the file
        if target_path.exists() and not force:
            print(f"  skipping: {rel_file} (already exists)")
        else:
            print(f"  copying: {rel_file}")
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, target_path)

    # 3c. Update state for installed component
    state_manager.update_state_for_component(component)
```

### 10.4 State Management Phase (10-11 seconds)

```python
# Update final state after profile installation
state_manager.update_state_for_profile('standard', installed_components)

# Final state file:
final_state = {
    'version': '1.0.0',
    'installed_profile': 'standard',
    'installed_components': ['core', 'schemas', 'scripts', 'precommit', 'docs'],
    'installation_history': [
        {'timestamp': '2025-09-06T10:30:00', 'action': 'install_component', 'component': 'core'},
        {'timestamp': '2025-09-06T10:30:05', 'action': 'install_component', 'component': 'schemas'},
        {'timestamp': '2025-09-06T10:30:10', 'action': 'install_component', 'component': 'scripts'},
        {'timestamp': '2025-09-06T10:30:15', 'action': 'install_component', 'component': 'precommit'},
        {'timestamp': '2025-09-06T10:30:20', 'action': 'install_component', 'component': 'docs'},
        {'timestamp': '2025-09-06T10:30:25', 'action': 'install_profile', 'profile': 'standard', 'components': [...]}
    ]
}
```

### 10.5 Final Result

```
target-project/
├── .ai/                              ← Installed from 'core' component
│   ├── guardrails.yaml              ← Language-specific configurations
│   └── envelope.json.example        ← Copilot envelope template
├── ai/                              ← Installed from 'schemas' and 'scripts' components
│   ├── schemas/
│   │   └── copilot_envelope.schema.json
│   └── scripts/
│       ├── check_envelope.py
│       ├── lang_lint.sh
│       └── policy/
│           └── check_demo_on_rails.py
├── docs/                            ← Installed from 'docs' component
│   ├── decisions/
│   ├── guides/
│   └── README.md
├── .pre-commit-config.yaml          ← Installed from 'precommit' component
└── .ai-guardrails-state.yaml        ← State tracking file
```

---

## 11. Data Flow Diagrams

### 11.1 High-Level Data Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │───▶│  Bootstrap      │───▶│  Plugin System  │
│ install std     │    │  Orchestrator   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   State File    │◀───│  State Manager  │    │ Manifest Merger │
│  .ai-state.yaml │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Target Files   │◀───│ Component Mgr   │◀───│ Merged Manifest │
│   .ai/, docs/   │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 11.2 File Discovery Flow

```
Component Request
       │
       ▼
┌─────────────────┐
│ Is Plugin       │     YES    ┌─────────────────┐
│ Component?      │───────────▶│ Plugin Path     │
└─────────────────┘            │ Resolution      │
       │ NO                    └─────────────────┘
       ▼                               │
┌─────────────────┐                   │
│ Template Repo   │                   │
│ Path            │                   │
└─────────────────┘                   │
       │                              │
       ▼                              ▼
┌─────────────────┐            ┌─────────────────┐
│ Glob Pattern    │◀───────────│ Glob Pattern    │
│ Matching        │            │ Matching        │
└─────────────────┘            └─────────────────┘
       │                              │
       ▼                              ▼
┌─────────────────┐            ┌─────────────────┐
│ Relative Path   │            │ Relative Path   │
│ Conversion      │            │ Conversion      │
└─────────────────┘            └─────────────────┘
       │                              │
       └──────────────┬───────────────┘
                      ▼
               ┌─────────────────┐
               │ File List       │
               │ Return          │
               └─────────────────┘
```

### 11.3 State Management Flow

```
Operation Start
       │
       ▼
┌─────────────────┐
│ Load Current    │
│ State           │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ Perform         │
│ Operation       │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ Update State    │
│ Data            │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ Add History     │
│ Entry           │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ Persist State   │
│ to YAML         │
└─────────────────┘
```

---

## 12. Error Handling and Recovery

### 12.1 Error Categories and Handling

#### Category 1: Validation Errors (Fail Fast)
```python
# These errors stop execution immediately
try:
    if profile_name not in self.merged_manifest['profiles']:
        raise ValueError(f"Unknown profile: {profile_name}")
except ValueError as e:
    print(f"Error: {e}")
    return False  # Exit cleanly
```

#### Category 2: File Operation Errors (Continue with Warning)
```python
# These errors are logged but don't stop the process
def _install_single_file(self, component: str, rel_file: str, force: bool, manifest: Dict) -> bool:
    try:
        # File installation logic
        shutil.copy2(src_path, target_path)
        return True
    except Exception as e:
        print(f"  ERROR: Failed to install {rel_file}: {e}")
        return False  # Continue with other files
```

#### Category 3: State Corruption (Graceful Degradation)
```python
def load_state(self) -> Dict:
    try:
        with open(self.state_path) as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: State file corrupted, using default state: {e}")
        return self._create_default_state()  # Graceful fallback
```

### 12.2 Recovery Mechanisms

#### Partial Installation Recovery
```python
# If some components fail, system tracks what succeeded
def install_profile(self, profile_name: str, force: bool = False) -> bool:
    success = True
    installed_components = []

    for component in components:
        if self.install_component(component, force):
            installed_components.append(component)
            # Save progress after each successful component
            self.state_manager.update_state_for_component(component)
        else:
            success = False
            # Continue with remaining components

    # Update state with what was successfully installed
    if installed_components:
        self.state_manager.update_state_for_profile(profile_name, installed_components)

    return success  # False if any component failed, but partial progress saved
```

#### State Recovery from Filesystem
```python
def recover_state_from_filesystem(self) -> Dict:
    """Attempt to recover state by analyzing installed files"""
    recovered_components = []

    # Check for component markers
    if (self.target_dir / ".ai" / "guardrails.yaml").exists():
        recovered_components.append("core")
    if (self.target_dir / "ai" / "schemas").exists():
        recovered_components.append("schemas")
    # ... more recovery logic

    return {
        'version': '1.0.0',
        'installed_components': recovered_components,
        'installation_history': [{'action': 'state_recovery', 'timestamp': datetime.now().isoformat()}]
    }
```

---

## 13. The Answer: Explicit Target Structure Definition

### 13.1 The Problem: Implicit Target Knowledge

Before the explicit target structure schema, the system suffered from **scattered implicit knowledge**:

```python
# Knowledge scattered across different files and functions
def install_component(self, component):
    # Hardcoded knowledge: "core component needs .ai/guardrails.yaml"
    if component == "core":
        create_file(".ai/guardrails.yaml")

    # Hardcoded knowledge: "schemas component needs ai/schemas/ directory"
    if component == "schemas":
        create_directory("ai/schemas/")
        create_file("ai/schemas/copilot_envelope.schema.json")
```

**Problems with this approach:**
- **Implicit contracts**: Installation logic knew what to create, but validation couldn't verify completeness
- **Scattered knowledge**: Target structure requirements spread across multiple components
- **No validation**: System couldn't verify if an installation was complete or corrupted
- **Inconsistent expectations**: Different components might have conflicting assumptions

### 13.2 The Solution: Centralized Schema Definition

Now the guardrails system **explicitly knows** what the target structure should be through:

#### 13.2.1 Declarative Target Structure Schema

The system defines the expected structure in `target-structure.schema.yaml`:

```yaml
# target-structure.schema.yaml - Single Source of Truth
expected_structure:
  # Core AI configuration directory
  ".ai/":
    required: true
    description: "Core AI guardrails configuration directory"
    files:
      "guardrails.yaml":
        required: true
        description: "Language-specific lint/test commands"
        schema_ref: "guardrails.schema.yaml"
      "envelope.json":
        required: false
        description: "Copilot planning envelope (auto-generated)"
        schema_ref: "ai/schemas/copilot_envelope.schema.json"

  # AI automation directory
  "ai/":
    required: true
    description: "AI automation scripts and schemas"
    subdirs:
      "schemas/":
        required: true
        description: "JSON schemas for validation"
        files:
          "copilot_envelope.schema.json":
            required: true
            description: "Copilot envelope JSON schema"
```

#### 13.2.2 Validation Rules as Code

The schema includes explicit validation rules:

```yaml
validation:
  # Core requirements that must be satisfied
  core_requirements:
    - "Must have .ai/ directory with guardrails.yaml"
    - "Must have ai/schemas/ directory with copilot_envelope.schema.json"
    - "No files allowed in repository root unless in root-allowlist.txt"

  # Structure constraints
  constraints:
    - name: "ai_directory_structure"
      description: "AI directories must follow standard layout"
      rule: ".ai/ for config, ai/ for automation"

    - name: "schema_validation"
      description: "All JSON files must validate against their schemas"
      rule: "Files with .json extension must pass schema validation"
```

#### 13.2.3 Conflict Resolution Rules

The schema defines how to handle conflicts:

```yaml
conflicts:
  - pattern: ".ai/guardrails.yaml vs .ai/guardrails/"
    resolution: "Both can coexist - file for simple config, directory for complex"

  - pattern: "docs/ vs .github/ documentation"
    resolution: "docs/ for project docs, .github/ for GitHub-specific automation"
```

### 13.3 How the System Uses This Knowledge

#### 13.3.1 Installation Validation

The installation manifest references the schema:

```yaml
# installation-manifest.yaml
settings:
  target_structure_schema: "target-structure.schema.yaml"  # Reference to schema
  validate_target_structure: true  # Enable validation
```

#### 13.3.2 Doctor Diagnostic System

The Doctor component can now validate against the explicit schema:

```python
def _check_target_structure(self, manifest: Dict) -> int:
    """Validate target directory structure against schema"""

    # Load the explicit target structure schema
    schema_file = self.target_dir.parent / "src" / "target-structure.schema.yaml"
    with open(schema_file) as f:
        target_schema = yaml.safe_load(f)

    # Check required directories exist
    expected_structure = target_schema.get('expected_structure', {})
    for path, config in expected_structure.items():
        if config.get('required', False):
            target_path = self.target_dir / path.strip('/"')
            if not target_path.exists():
                print(f"  ERROR: Required structure missing: {path}")
                issues += 1

    # Check core requirements
    core_requirements = target_schema.get('validation', {}).get('core_requirements', [])
    for requirement in core_requirements:
        if "Must have .ai/ directory with guardrails.yaml" in requirement:
            if not (self.target_dir / ".ai" / "guardrails.yaml").exists():
                print(f"  ERROR: Missing core requirement: .ai/guardrails.yaml")
                issues += 1
```

#### 13.3.3 Profile-Specific Validation

Different profiles have different requirements:

```yaml
profiles:
  minimal:
    required_structure:
      - ".ai/guardrails.yaml"
      - "ai/schemas/copilot_envelope.schema.json"

  standard:
    required_structure:
      - ".ai/guardrails.yaml"
      - "ai/schemas/copilot_envelope.schema.json"
      - "ai/scripts/"
      - "docs/"
      - ".pre-commit-config.yaml"

  full:
    required_structure:
      - ".ai/guardrails.yaml"
      - "ai/schemas/copilot_envelope.schema.json"
      - "ai/scripts/"
      - ".github/workflows/"
      - "docs/"
      - ".pre-commit-config.yaml"
```

### 13.4 Benefits of Explicit Target Structure

#### 13.4.1 Complete Installation Verification

```python
# Before: Could only check if component was "installed" in state
if self.state_manager.is_component_installed("core"):
    print("Core component installed")  # But are the files actually there?

# After: Can verify actual structure against schema
if self.doctor.validate_target_structure():
    print("Installation verified complete and valid")
```

#### 13.4.2 Corruption Detection

```python
# System can detect when files go missing or get corrupted
def check_installation_integrity(self):
    schema_issues = self.doctor._check_target_structure(self.manifest)
    if schema_issues > 0:
        print(f"Installation corrupted: {schema_issues} structure violations")
        return False
    return True
```

#### 13.4.3 Clear Contracts for Plugins

Plugins know exactly what structure they should create:

```yaml
# Plugin can reference the target structure schema
components:
  demo-harness:
    description: "Demo execution framework"
    file_patterns: ["ai/tools/**/*.py"]
    validates_against: "target-structure.schema.yaml"
    creates_structure:
      - "ai/tools/"
      - "ai/demo_scenarios/"
```

#### 13.4.4 Migration and Upgrade Support

```python
def migrate_to_new_structure(self):
    """Migrate existing installation to new target structure"""
    current_structure = self._analyze_current_structure()
    target_schema = self._load_target_schema()

    # Compare current vs expected and create migration plan
    migration_plan = self._create_migration_plan(current_structure, target_schema)

    # Execute migration with validation
    return self._execute_migration(migration_plan)
```

### 13.5 Schema Evolution and Versioning

The schema supports evolution:

```yaml
# Version tracking for schema changes
version_history:
  "1.0.0":
    changes:
      - "Initial target structure schema definition"
      - "Separated .ai/ (config) from ai/ (automation)"
      - "Defined core vs optional components"

  "1.1.0":  # Future version
    changes:
      - "Added support for language-specific subdirectories"
      - "Enhanced conflict resolution rules"
```

### 13.6 Implementation Status

**✅ Currently Implemented:**
- Target structure schema definition (`target-structure.schema.yaml`)
- Basic schema loading in Doctor component
- Core requirements validation
- Required directory structure checking

**🚧 Partially Implemented:**
- Schema enforcement during installation (basic validation only)
- Profile-specific structure validation (schema exists, enforcement incomplete)

**❌ Not Yet Implemented:**
- Advanced conflict resolution based on schema rules
- Automatic structure migration between schema versions
- Plugin validation against target structure requirements
- Complete integration with installation flow

### 13.7 The Architectural Breakthrough

This explicit target structure definition represents a **fundamental architectural improvement**:

**Before:** Scattered implicit knowledge → Unreliable installations → Hard to debug issues

**After:** Centralized explicit schema → Verifiable installations → Clear error diagnosis

The system now has a **single source of truth** for what constitutes a valid installation, enabling:
- **Reliable validation** against known good structure
- **Clear error messages** when installations are incomplete
- **Automated repair** of corrupted installations (future capability)
- **Consistent behavior** across all components and plugins

This transforms the system from "hoping installations work" to "knowing installations are correct" - a critical difference for production reliability.

---

## Summary

The AI Guardrails Bootstrap System is a sophisticated, modular platform that transforms complex manual setup processes into declarative, repeatable operations. Its key strengths include:

### **Core Capabilities**
- **Dynamic Discovery**: No hardcoded file lists, everything discovered via patterns
- **Plugin Architecture**: Extensible through independent plugin development
- **Intelligent Merging**: Smart configuration file merging instead of overwriting
- **State Persistence**: Comprehensive tracking of installations and history
- **Multi-layer Validation**: Validation at manifest, component, and file levels

### **Operational Flow**
1. **Initialization**: Set up managers and discover operational environment
2. **Plugin Discovery**: Automatically find and load plugin manifests
3. **Manifest Merging**: Create unified view of base + plugin components
4. **Component Installation**: Install files using dynamic pattern discovery
5. **State Management**: Track installation progress and history
6. **Validation**: Verify system health and consistency

### **Architecture Benefits**
- **Maintainable**: Clear separation of concerns across layers
- **Extensible**: Plugin system enables independent innovation
- **Reliable**: Comprehensive error handling and recovery mechanisms
- **Traceable**: Full audit trail of installation operations

The system successfully balances **flexibility** (plugin architecture) with **reliability** (validation and state management), making it suitable for both development experimentation and production deployment of AI development tooling.

---

**Document Control**
- **Author**: AI Guardrails Technical Team
- **Technical Review**: Architecture Review Board
- **Next Update**: As system evolves
- **Related Documents**:
  - [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md)
  - [PLUGIN_ARCHITECTURE_ANALYSIS.md](./PLUGIN_ARCHITECTURE_ANALYSIS.md)
